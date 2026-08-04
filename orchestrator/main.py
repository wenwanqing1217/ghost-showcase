"""
AgentOrchestrator — 双编程工具协同调度中枢

架构：
  Gateway (:18080) → Orchestrator (:19090)
    → ToolA (生成器, :8081)
    → ToolB (校验优化, :8082)
    → Alpha-ID MemoryStore (:8000)
    → Obsidian

工作模式：
  - 串联: 需求 → AI起草 → ToolA生成 → ToolB优化 → 归档
  - 并行: 同一需求同时发ToolA+ToolB → 对比 → 归档

安全/质量改进：
  - 有界线程池 (ThreadPoolExecutor) 替代无界 thread creation
  - 任务状态转换原子化 (under lock)
  - 输入校验 (limit 有上限)
  - 任务 TTL 自动清理
  - 可选 API Key 认证
  - 异步 HTTP 客户端复用
"""

import os
import json
import time
import uuid
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field, asdict

import uvicorn
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("orchestrator")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GATEWAY = os.getenv("GATEWAY_URL", "http://localhost:18080")
TOOL_A = os.getenv("TOOL_A_URL", "http://localhost:8081")
TOOL_B = os.getenv("TOOL_B_URL", "http://localhost:8082")
TOOL_A_TIMEOUT = float(os.getenv("TOOL_A_TIMEOUT", "30"))
TOOL_B_TIMEOUT = float(os.getenv("TOOL_B_TIMEOUT", "30"))
TOOL_MAX_RETRIES = int(os.getenv("TOOL_MAX_RETRIES", "2"))
PORT = int(os.getenv("ORCHESTRATOR_PORT", "19090"))
API_KEY = os.getenv("ORCHESTRATOR_API_KEY", "")  # 空字符串表示不校验
MAX_WORKERS = int(os.getenv("ORCHESTRATOR_MAX_WORKERS", "4"))
MAX_LIMIT = 100  # list_tasks 最大返回条数
TASK_TTL_SECONDS = int(os.getenv("ORCHESTRATOR_TASK_TTL", "3600"))  # 1 小时

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class Task:
    id: str = ""
    status: str = "pending"  # pending/running/completed/failed
    requirement: str = ""
    mode: str = "serial"  # serial/parallel
    created_at: float = 0.0
    completed_at: Optional[float] = None
    tool_a_result: Optional[dict] = None
    tool_b_result: Optional[dict] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Task manager (encapsulates state + lock)
# ---------------------------------------------------------------------------


class TaskManager:
    """Thread-safe task store with atomic transitions and TTL eviction."""

    def __init__(self, ttl: int = TASK_TTL_SECONDS):
        self._tasks: Dict[str, Task] = {}
        self._lock = threading.Lock()
        self._ttl = ttl

    def create(self, task: Task) -> None:
        with self._lock:
            self._maybe_evict()
            self._tasks[task.id] = task

    def get(self, task_id: str) -> Optional[Task]:
        with self._lock:
            return self._tasks.get(task_id)

    def transition(self, task_id: str, from_status: str, to_status: str) -> bool:
        """
        Atomically transition a task's status.
        Returns False if task not found or not in from_status.
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task or task.status != from_status:
                return False
            task.status = to_status
            return True

    def update(self, task_id: str, **kwargs) -> None:
        """Update task fields under lock."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                for k, v in kwargs.items():
                    if hasattr(task, k):
                        setattr(task, k, v)

    def list_latest(self, limit: int) -> List[Task]:
        """Return up to `limit` most-recent tasks."""
        with self._lock:
            return sorted(
                self._tasks.values(), key=lambda t: t.created_at, reverse=True
            )[:limit]

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._tasks)

    def _maybe_evict(self) -> None:
        """Remove expired tasks (must be called under lock)."""
        if self._ttl <= 0:
            return
        now = time.time()
        expired = [
            tid for tid, t in self._tasks.items()
            if t.created_at < now - self._ttl and t.status in ("completed", "failed")
        ]
        for tid in expired:
            del self._tasks[tid]
        if expired:
            logger.info("Evicted %d expired tasks", len(expired))


# ---------------------------------------------------------------------------
# Application state
# ---------------------------------------------------------------------------

app = FastAPI(title="AgentOrchestrator", version="1.1.0")
task_manager = TaskManager()
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix="task")
_http_client: Optional[httpx.AsyncClient] = None


async def get_http_client() -> httpx.AsyncClient:
    """Shared async HTTP client (avoids per-request client creation)."""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=10.0)
    return _http_client


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


async def require_api_key(request: Request) -> None:
    """FastAPI dependency: enforce API key if configured."""
    if not API_KEY:
        return  # auth disabled
    key = request.headers.get("Authorization", "")
    if key.startswith("Bearer "):
        key = key[7:]
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


# ---------------------------------------------------------------------------
# Gateway sync
# ---------------------------------------------------------------------------


async def sync_to_gateway(content: str, category: str = "orchestrator") -> None:
    """Send a memory entry to the gateway asynchronously."""
    client = await get_http_client()
    try:
        await client.post(
            f"{GATEWAY}/v1/memory/store",
            json={
                "alpha_id": "Alpha-001",
                "content": content,
                "category": category,
                "sensitivity": 30,
                "source": "orchestrator",
                "tags": ["orchestrator", "task"],
            },
        )
    except Exception as e:
        logger.warning("sync error: %s", e)


# ---------------------------------------------------------------------------
# Task execution logic
# ---------------------------------------------------------------------------


def _call_tool_with_retry(
    client: httpx.Client,
    url: str,
    payload: dict,
    timeout: float,
    max_retries: int,
    tool_name: str,
) -> dict:
    """Call a tool endpoint with exponential backoff retry.

    Returns a dict with either the JSON response under "data"
    or an error description under "error".
    """
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = client.post(url, json=payload, timeout=timeout)
            if resp.status_code == 200:
                return {"data": resp.json(), "attempt": attempt}
            # 5xx → retry, 4xx → no point retrying
            if resp.status_code >= 500:
                last_err = f"{tool_name} returned {resp.status_code} (attempt {attempt})"
                logger.warning(last_err)
                continue
            return {
                "error": f"{tool_name} returned {resp.status_code}",
                "status_code": resp.status_code,
                "body": resp.text[:500],
                "attempt": attempt,
            }
        except httpx.TimeoutException:
            last_err = f"{tool_name} timeout after {timeout}s (attempt {attempt})"
            logger.warning(last_err)
        except httpx.ConnectError:
            last_err = f"{tool_name} unreachable (attempt {attempt})"
            logger.warning(last_err)
        except Exception as exc:
            last_err = f"{tool_name} error: {exc} (attempt {attempt})"
            logger.warning(last_err)

    return {"error": last_err, "attempts": max_retries}


def _execute_task(task: Task) -> None:
    """Run in thread pool. Calls ToolA + ToolB via HTTP with retry."""
    try:
        logger.info("Executing task %s (%s mode)", task.id, task.mode)

        tool_a_result = None
        tool_b_result = None

        with httpx.Client(timeout=max(TOOL_A_TIMEOUT, TOOL_B_TIMEOUT) + 5) as client:
            # ── ToolA: 生成器（serial + parallel 模式均调用） ──
            if TOOL_A:
                tool_a_result = _call_tool_with_retry(
                    client=client,
                    url=f"{TOOL_A}/v1/generate",
                    payload={"requirement": task.requirement, "task_id": task.id},
                    timeout=TOOL_A_TIMEOUT,
                    max_retries=TOOL_MAX_RETRIES,
                    tool_name="ToolA",
                )
            else:
                tool_a_result = {"status": "not_configured", "message": "ToolA URL not configured"}

            # ── ToolB: 校验优化（parallel 模式调用；serial 模式跳过） ──
            if task.mode == "parallel" and TOOL_B:
                tool_b_result = _call_tool_with_retry(
                    client=client,
                    url=f"{TOOL_B}/v1/optimize",
                    payload={
                        "requirement": task.requirement,
                        "task_id": task.id,
                        "tool_a_result": tool_a_result.get("data") or tool_a_result,
                    },
                    timeout=TOOL_B_TIMEOUT,
                    max_retries=TOOL_MAX_RETRIES,
                    tool_name="ToolB",
                )
            else:
                reason = "serial mode" if task.mode != "parallel" else "ToolB URL not configured"
                tool_b_result = {"status": "skipped", "message": reason}

        task_manager.update(
            task.id,
            tool_a_result=tool_a_result,
            tool_b_result=tool_b_result,
            status="completed",
            completed_at=time.time(),
        )
        logger.info("Task %s completed (a_err=%s, b_err=%s)", task.id,
                    "data" in tool_a_result, "data" in (tool_b_result or {}))
    except Exception as exc:
        task_manager.update(task.id, status="failed", error=str(exc))
        logger.error("Task %s failed: %s", task.id, exc)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.post("/v1/task/submit")
async def submit_task(req: Request, _=Depends(require_api_key)):
    body = await req.json()
    requirement = body.get("requirement", "")
    mode = body.get("mode", "serial")
    if not requirement:
        return JSONResponse({"error": "requirement required"}, 400)
    if mode not in ("serial", "parallel"):
        return JSONResponse({"error": "mode must be serial or parallel"}, 400)

    task = Task(
        id=uuid.uuid4().hex[:12],
        requirement=requirement,
        mode=mode,
        created_at=time.time(),
    )
    task_manager.create(task)

    logger.info("Task %s submitted (mode=%s): %s...", task.id, mode, requirement[:80])
    await sync_to_gateway(
        f"[Orchestrator] 新任务 {task.id}: {requirement[:100]}", "task_submitted"
    )

    return {"success": True, "task_id": task.id, "status": task.status}


@app.get("/v1/task/{task_id}")
async def get_task(task_id: str, _=Depends(require_api_key)):
    task = task_manager.get(task_id)
    if not task:
        return JSONResponse({"error": "task not found"}, 404)
    return {"success": True, "task": asdict(task)}


@app.get("/v1/tasks")
async def list_tasks(limit: int = 20, _=Depends(require_api_key)):
    # Clamp limit to prevent abuse
    if limit < 1:
        limit = 1
    elif limit > MAX_LIMIT:
        limit = MAX_LIMIT
    items = task_manager.list_latest(limit)
    return {
        "success": True,
        "tasks": [asdict(t) for t in items],
        "total": task_manager.count,
    }


@app.post("/v1/task/{task_id}/execute")
async def execute_task(task_id: str, _=Depends(require_api_key)):
    # Atomic transition: pending → running (prevents double-execution race)
    if not task_manager.transition(task_id, "pending", "running"):
        task = task_manager.get(task_id)
        if not task:
            return JSONResponse({"error": "task not found"}, 404)
        return JSONResponse({"error": "task already running/completed"}, 400)

    # Submit to thread pool (bounded concurrency)
    executor.submit(_execute_task, task_manager.get(task_id))
    return {"success": True, "task_id": task_id, "status": "running"}


@app.get("/health")
async def health():
    return {"status": "ok", "tasks": task_manager.count, "port": PORT}


@app.get("/v1/tools/status")
async def tools_status():
    """Report reachability of ToolA and ToolB (no auth required for monitoring)."""
    client = get_http_client()
    results = {"tool_a": None, "tool_b": None}
    for name, url, timeout in [
        ("tool_a", f"{TOOL_A}/health" if TOOL_A else None, TOOL_A_TIMEOUT),
        ("tool_b", f"{TOOL_B}/health" if TOOL_B else None, TOOL_B_TIMEOUT),
    ]:
        if not url:
            results[name] = {"configured": False}
            continue
        try:
            resp = await client.get(url, timeout=timeout)
            results[name] = {"configured": True, "reachable": resp.status_code == 200, "status_code": resp.status_code}
        except Exception as exc:
            results[name] = {"configured": True, "reachable": False, "error": str(exc)}
    return {"success": True, "tools": results}


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


@app.on_event("shutdown")
async def shutdown():
    executor.shutdown(wait=False, cancel_futures=True)
    if _http_client is not None:
        await _http_client.aclose()


if __name__ == "__main__":
    print(f"AgentOrchestrator starting on :{PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
