"""AgentOrchestrator — 双编程工具协同调度中枢

架构：
  Gateway (:18080) → Orchestrator (:19090)
    → ToolA (生成器, :8081)
    → ToolB (校验优化, :8082)
    → Alpha-ID MemoryStore (:8000)
    → Obsidian

工作模式：
  - 串联: 需求 → AI起草 → ToolA生成 → ToolB优化 → 归档
  - 并行: 同一需求同时发ToolA+ToolB → 对比 → 归档
"""

import os
import json
import time
import uuid
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, asdict

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("orchestrator")

GATEWAY = os.getenv("GATEWAY_URL", "http://localhost:18080")
TOOL_A = os.getenv("TOOL_A_URL", "http://localhost:8081")
TOOL_B = os.getenv("TOOL_B_URL", "http://localhost:8082")
PORT = int(os.getenv("ORCHESTRATOR_PORT", "19090"))


@dataclass
class Task:
    id: str = ""
    status: str = "pending"  # pending/running/success/failed
    requirement: str = ""
    mode: str = "serial"  # serial/parallel
    created_at: float = 0.0
    completed_at: Optional[float] = None
    tool_a_result: Optional[dict] = None
    tool_b_result: Optional[dict] = None
    error: Optional[str] = None


app = FastAPI(title="AgentOrchestrator", version="1.0.0")
_tasks: dict = {}
_tasks_lock = threading.Lock()


def _sync_to_gateway(content: str, category: str = "orchestrator"):
    try:
        with httpx.Client() as c:
            c.post(f"{GATEWAY}/v1/memory/store", json={
                "alpha_id": "Alpha-001",
                "content": content,
                "category": category,
                "sensitivity": 30,
                "source": "orchestrator",
                "tags": ["orchestrator", "task"],
            }, timeout=10)
    except Exception as e:
        logger.warning("sync error: %s", e)


@app.post("/v1/task/submit")
async def submit_task(req: Request):
    body = await req.json()
    requirement = body.get("requirement", "")
    mode = body.get("mode", "serial")
    if not requirement:
        return JSONResponse({"error": "requirement required"}, 400)

    task = Task(
        id=uuid.uuid4().hex[:12],
        requirement=requirement,
        mode=mode,
        created_at=time.time(),
    )
    with _tasks_lock:
        _tasks[task.id] = task

    logger.info("Task %s submitted (mode=%s): %s...", task.id, mode, requirement[:80])
    _sync_to_gateway(f"[Orchestrator] \u65b0\u4efb\u52a1 {task.id}: {requirement[:100]}", "task_submitted")

    return {"success": True, "task_id": task.id, "status": task.status}


@app.get("/v1/task/{task_id}")
async def get_task(task_id: str):
    with _tasks_lock:
        task = _tasks.get(task_id)
    if not task:
        return JSONResponse({"error": "task not found"}, 404)
    return {"success": True, "task": asdict(task)}


@app.get("/v1/tasks")
async def list_tasks(limit: int = 20):
    with _tasks_lock:
        items = sorted(_tasks.values(), key=lambda t: t.created_at, reverse=True)[:limit]
    return {"success": True, "tasks": [asdict(t) for t in items], "total": len(_tasks)}


@app.post("/v1/task/{task_id}/execute")
async def execute_task(task_id: str):
    with _tasks_lock:
        task = _tasks.get(task_id)
    if not task:
        return JSONResponse({"error": "task not found"}, 404)
    if task.status != "pending":
        return JSONResponse({"error": "task already running/completed"}, 400)

    task.status = "running"

    def _run():
        try:
            logger.info("Executing task %s (%s mode)", task.id, task.mode)
            
            if task.mode == "serial":
                # Step 1: AI draft
                # Step 2: ToolA generate
                # Step 3: ToolB optimize
                task.tool_a_result = {"status": "simulated", "message": "ToolA would generate here"}
                task.tool_b_result = {"status": "simulated", "message": "ToolB would optimize here"}
            else:  # parallel
                # Both tools run independently
                task.tool_a_result = {"status": "simulated", "message": "ToolA parallel result"}
                task.tool_b_result = {"status": "simulated", "message": "ToolB parallel result"}
            
            task.status = "success"
            task.completed_at = time.time()
            _sync_to_gateway(f"[Orchestrator] \u4efb\u52a1 {task.id} \u5b8c\u6210", "task_completed")
            logger.info("Task %s completed", task.id)
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            logger.error("Task %s failed: %s", task.id, e)

    threading.Thread(target=_run, daemon=True).start()
    return {"success": True, "task_id": task_id, "status": "running"}


@app.get("/health")
async def health():
    return {"status": "ok", "tasks": len(_tasks), "port": PORT}


if __name__ == "__main__":
    print(f"AgentOrchestrator starting on :{PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
