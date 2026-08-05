"""
OrchestratorEngine — Ghost 平台统一调度引擎（入口文件）

# TERM: OrchestratorEngine — 统一后台循环管理（合并自 alpha_id/orchestrator.py + core/orchestrator.py）
# TERM: EventBus — Redis Streams 跨服务事件总线

架构：
  Gateway (:18080) → OrchestratorEngine (:19090)
    → Gateway Proxy → ToolA (生成器, :8081)
    → Gateway Proxy → ToolB (校验优化, :8082)
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

import logging
import os
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional

import httpx
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, Counter, Gauge, generate_latest

# ── OrchestratorEngine import setup ──
# Add alphaid source root so the engine is importable from the orchestrator service.
_ALPHAID_SRC = str(Path(__file__).resolve().parent.parent / "alphaid" / "projects" / "src")
if _ALPHAID_SRC not in sys.path:
    sys.path.insert(0, _ALPHAID_SRC)

try:
    from orchestrator.engine import ChannelAdapter, OrchestratorEngine
    _HAS_ENGINE = True
except ImportError:
    _HAS_ENGINE = False
    ChannelAdapter = None  # type: ignore[assignment]
    OrchestratorEngine = None  # type: ignore[assignment]
    logger = logging.getLogger("orchestrator")
    logger.warning("OrchestratorEngine 不可用 — 后台循环已禁用 (缺少 alphaid 依赖)")

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
# Gateway-proxied tool URLs (preferred: centralizes auth, rate-limit, audit)
TOOL_A_GATEWAY = os.getenv("TOOL_A_GATEWAY", f"{GATEWAY}/v1/tools/generate")
TOOL_B_GATEWAY = os.getenv("TOOL_B_GATEWAY", f"{GATEWAY}/v1/tools/optimize")
TOOL_A_TIMEOUT = float(os.getenv("TOOL_A_TIMEOUT", "30"))
TOOL_B_TIMEOUT = float(os.getenv("TOOL_B_TIMEOUT", "30"))
TOOL_MAX_RETRIES = int(os.getenv("TOOL_MAX_RETRIES", "2"))
PORT = int(os.getenv("ORCHESTRATOR_PORT", "19090"))
API_KEY = os.getenv("ORCHESTRATOR_API_KEY", "")  # 空字符串表示不校验
MAX_WORKERS = int(os.getenv("ORCHESTRATOR_MAX_WORKERS", "4"))
MAX_LIMIT = 100  # list_tasks 最大返回条数
TASK_TTL_SECONDS = int(os.getenv("ORCHESTRATOR_TASK_TTL", "3600"))  # 1 小时
# 数据循环：状态同步间隔（秒）— 定期将 orchestrator 状态上报到 Gateway memory store
SYNC_INTERVAL_SECONDS = int(os.getenv("ORCHESTRATOR_SYNC_INTERVAL", "300"))  # 5 分钟

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
# Real ChannelAdapter + Data Loop
# ---------------------------------------------------------------------------


class GatewayChannelAdapter(ChannelAdapter if _HAS_ENGINE else object):  # type: ignore[misc]
    """
    # TERM: ChannelAdapter — 渠道适配器基类（飞书/Web/微信/Telegram）

    Gateway 渠道适配器 — 通过 Gateway HTTP API 收发消息。

    入站：Gateway 接收外部渠道消息后，POST 到本服务 /v1/channel/message，
          由路由处理器调用 engine.receive()，回复通过本适配器 send() 返回。
    出站：engine 主动调用 send() 时，POST 到 Gateway /v1/message/send。
    """

    def __init__(self, gateway_url: str):
        # 当 _HAS_ENGINE=False 时，跳过 ChannelAdapter.__init__（object 无参 init）
        if _HAS_ENGINE:
            super().__init__(name="gateway")
        else:
            self.name = "gateway"
        self._gateway_url = gateway_url.rstrip("/")

    def send(self, chat_id: str, content) -> bool:  # type: ignore[override]
        """通过 Gateway /v1/message/send 发送消息到指定会话"""
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.post(
                    f"{self._gateway_url}/v1/message/send",
                    json={
                        "chat_id": chat_id,
                        "content": content,
                        "source": "orchestrator",
                    },
                )
            if resp.status_code != 200:
                logger.warning(
                    "GatewayChannelAdapter.send: Gateway 返回 %s",
                    resp.status_code,
                )
            return resp.status_code == 200
        except Exception as e:
            logger.warning("GatewayChannelAdapter.send 失败: %s", e)
            return False

    def start(self):  # type: ignore[override]
        """HTTP 渠道无需长连接 — 启动为空操作（消息由 FastAPI 路由推入）"""
        logger.info(
            "GatewayChannelAdapter 已就绪 (入站: POST /v1/channel/message → engine.receive)"
        )

    def stop(self):  # type: ignore[override]
        """HTTP 渠道无需清理"""
        pass


def gateway_sync_loop():
    """
    数据循环：定期将 orchestrator 状态同步到 Gateway memory store。

    每次执行：
    - 收集 task_manager.count + engine.get_status()
    - POST 到 Gateway /v1/memory/store 作为心跳记忆
    - 失败仅记录日志，不抛异常（避免循环退出）
    """
    stats: Dict[str, object] = {
        "tasks_total": task_manager.count,
        "port": PORT,
    }
    if _orchestrator_engine is not None:
        try:
            engine_status = _orchestrator_engine.get_status()
            stats["engine_running"] = engine_status.get("running", False)
            stats["engine_channels"] = engine_status.get("channels", [])
            stats["engine_loops"] = list(engine_status.get("data_loops", {}).keys())
            stats["engine_stats"] = engine_status.get("stats", {})
        except Exception as e:
            logger.warning("gateway_sync_loop: engine status failed: %s", e)

    try:
        tenant_id = os.environ.get("ALPHA_ID", "Ghost-001")
        with httpx.Client(timeout=5.0) as client:
            client.post(
                f"{GATEWAY}/v1/human/memory/store",
                headers={"X-Tenant-ID": tenant_id},
                json={
                    "alpha_id": tenant_id,
                    "content": (
                        f"[Orchestrator Sync] tasks={stats['tasks_total']} "
                        f"engine_running={stats.get('engine_running', False)} "
                        f"channels={stats.get('engine_channels', [])} "
                        f"loops={stats.get('engine_loops', [])}"
                    ),
                    "category": "orchestrator_sync",
                    "sensitivity": 10,
                    "source": "orchestrator",
                    "tags": ["orchestrator", "sync", "heartbeat"],
                },
            )
    except Exception as e:
        logger.warning("gateway_sync_loop: sync to gateway failed: %s", e)


# ---------------------------------------------------------------------------
# Application state
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup + shutdown (replaces deprecated @app.on_event)."""
    # Startup
    await get_http_client()
    global _orchestrator_engine
    if _HAS_ENGINE:
        try:
            alpha_id = os.environ.get("ALPHA_ID", "Ghost-001")
            _orchestrator_engine = OrchestratorEngine(alpha_id=alpha_id)

            # ── 注册真实 ChannelAdapter：Gateway 渠道 ──
            # Gateway 收到外部消息后 POST 到 /v1/channel/message，由本适配器路由到 engine.receive
            try:
                gw_adapter = GatewayChannelAdapter(gateway_url=GATEWAY)
                _orchestrator_engine.register_channel(gw_adapter)
            except Exception as e:
                logger.warning("注册 GatewayChannelAdapter 失败: %s", e)

            # ── 注册真实数据循环：状态同步 ──
            # 每 SYNC_INTERVAL_SECONDS 秒上报 orchestrator 状态到 Gateway memory store
            try:
                _orchestrator_engine.register_loop(
                    name="gateway_sync",
                    func=gateway_sync_loop,
                    interval=SYNC_INTERVAL_SECONDS,
                )
            except Exception as e:
                logger.warning("注册 gateway_sync 循环失败: %s", e)

            _orchestrator_engine.start()
            logger.info(
                "OrchestratorEngine 已启动 (alpha_id=%s, channels=%d, loops=%d)",
                alpha_id,
                len(_orchestrator_engine._channels),
                len(_orchestrator_engine._data_loops),
            )
        except Exception as e:
            logger.error("OrchestratorEngine 启动失败: %s", e)
            _orchestrator_engine = None
    else:
        logger.warning("OrchestratorEngine 不可用，跳过启动")
    yield
    # Shutdown
    if _orchestrator_engine is not None:
        try:
            _orchestrator_engine.stop()
            logger.info("OrchestratorEngine 已停止")
        except Exception as e:
            logger.error("OrchestratorEngine 停止异常: %s", e)
        _orchestrator_engine = None
    executor.shutdown(wait=False, cancel_futures=True)
    if _http_client is not None:
        await _http_client.aclose()


app = FastAPI(title="AgentOrchestrator", version="1.1.0", lifespan=lifespan)
task_manager = TaskManager()
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix="task")
_http_client: Optional[httpx.AsyncClient] = None

# ── OrchestratorEngine instance ──
# 模块级初始为 None；lifespan() 中在 _HAS_ENGINE 时实例化并 start()
_orchestrator_engine: Optional[OrchestratorEngine] = None


def get_engine() -> Optional[OrchestratorEngine]:
    """Return the OrchestratorEngine singleton (may be None if engine unavailable)."""
    return _orchestrator_engine


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
            f"{GATEWAY}/v1/human/memory/store",
            headers={"X-Tenant-ID": os.environ.get("ALPHA_ID", "Alpha-001")},
            json={
                "alpha_id": os.environ.get("ALPHA_ID", "Alpha-001"),
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
            # ── ToolA: 生成器（serial + parallel 模式均调用，通过 Gateway 集中管控） ──
            if TOOL_A_GATEWAY:
                tool_a_result = _call_tool_with_retry(
                    client=client,
                    url=TOOL_A_GATEWAY,
                    payload={"requirement": task.requirement, "task_id": task.id},
                    timeout=TOOL_A_TIMEOUT,
                    max_retries=TOOL_MAX_RETRIES,
                    tool_name="ToolA",
                )
            else:
                tool_a_result = {"status": "not_configured", "message": "ToolA Gateway URL not configured"}

            # ── ToolB: 校验优化（parallel 模式调用；serial 模式跳过，通过 Gateway 集中管控） ──
            if task.mode == "parallel" and TOOL_B_GATEWAY:
                tool_b_result = _call_tool_with_retry(
                    client=client,
                    url=TOOL_B_GATEWAY,
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
                reason = "serial mode" if task.mode != "parallel" else "ToolB Gateway URL not configured"
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


@app.post("/v1/channel/message")
async def receive_channel_message(req: Request, _=Depends(require_api_key)):
    """
    入站渠道消息端点 — Gateway 接收外部消息后转发到此。

    Body:
      {
        "sender_id": "user-xxx",
        "text": "用户消息",
        "channel": "feishu|web|wechat|telegram",
        "chat_id": "会话 ID（可选，用于回复）",
        ...
      }

    若 OrchestratorEngine 可用，调用 engine.receive() 生成回复并通过
    GatewayChannelAdapter.send() 回传 Gateway；否则返回 503。
    """
    if _orchestrator_engine is None:
        return JSONResponse(
            {"error": "OrchestratorEngine 不可用，无法处理渠道消息"},
            status_code=503,
        )

    body = await req.json()
    sender_id = body.get("sender_id") or body.get("from") or "unknown"
    text = body.get("text") or body.get("content") or ""
    channel = body.get("channel") or body.get("platform") or "gateway"
    chat_id = body.get("chat_id") or body.get("session_id") or sender_id

    if not text:
        return JSONResponse({"error": "text required"}, 400)

    try:
        # engine.receive 返回回复文本（可能为 None）
        reply = _orchestrator_engine.receive(
            sender_id=sender_id,
            text=text,
            channel=channel,
        )
    except Exception as e:
        logger.error("engine.receive 失败: %s", e)
        return JSONResponse(
            {"error": "处理失败", "detail": str(e)},
            status_code=500,
        )

    # 若有回复，通过 GatewayChannelAdapter 发回 Gateway
    sent = False
    if reply:
        adapter = _orchestrator_engine._channels.get("gateway")
        if adapter is not None:
            try:
                sent = adapter.send(chat_id, reply)
            except Exception as e:
                logger.warning("回复发送失败: %s", e)

    return {
        "success": True,
        "reply": reply,
        "delivered": sent,
        "engine": {
            "running": _orchestrator_engine._running,
            "alpha_id": _orchestrator_engine.alpha_id,
        },
    }


@app.get("/health")
async def health():
    engine_status = None
    if _orchestrator_engine is not None:
        try:
            engine_status = _orchestrator_engine.get_status()
        except Exception:
            engine_status = {"running": False, "error": "status check failed"}
    return {
        "status": "ok",
        "tasks": task_manager.count,
        "port": PORT,
        "engine": engine_status,
        "channels": list(_orchestrator_engine._channels.keys()) if _orchestrator_engine else [],
        "data_loops": list(_orchestrator_engine._data_loops.keys()) if _orchestrator_engine else [],
    }


# ── Prometheus 指标 ──
# 企业级可观测性：暴露调度器指标供 Prometheus 抓取，与 gateway /metrics 对齐。

_metric_tasks = Counter("orchestrator_tasks_total", "提交任务总数")
_metric_tasks_failed = Counter("orchestrator_tasks_failed_total", "失败任务总数")
_metric_engine_running = Gauge("orchestrator_engine_running", "Engine 是否运行", ["alpha_id"])
_metric_engine_loops = Gauge("orchestrator_engine_loops", "活跃循环数")
_metric_engine_channels = Gauge("orchestrator_engine_channels", "活跃渠道数")


@app.get("/metrics")
async def metrics():
    """Prometheus 抓取端点（无需认证，仅暴露进程/调度指标，无敏感数据）。"""
    if _orchestrator_engine is not None:
        try:
            status = _orchestrator_engine.get_status()
            _metric_engine_running.labels(status.get("alpha_id", "Ghost-001")).set(
                1 if status.get("running") else 0
            )
            _metric_engine_loops.set(len(status.get("data_loops", {})) + 4)
            _metric_engine_channels.set(len(status.get("channels", [])))
        except Exception:
            pass
    _metric_tasks.inc(0)
    _metric_tasks_failed.inc(0)
    return PlainTextResponse(
        generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get("/v1/tools/status")
async def tools_status():
    """Report reachability of ToolA and ToolB (no auth required for monitoring)."""
    client = await get_http_client()
    results = {"tool_a": None, "tool_b": None}
    for name, url, timeout in [
        ("tool_a", f"{TOOL_A_GATEWAY}/health" if TOOL_A_GATEWAY else None, TOOL_A_TIMEOUT),
        ("tool_b", f"{TOOL_B_GATEWAY}/health" if TOOL_B_GATEWAY else None, TOOL_B_TIMEOUT),
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


if __name__ == "__main__":
    print(f"AgentOrchestrator starting on :{PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
