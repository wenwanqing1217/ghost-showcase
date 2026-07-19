"""Autopilot API route."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse

from mindflow_map.autopilot.orchestrator import TaskOrchestrator
from mindflow_map.autopilot.runner import TaskRunner
from mindflow_map.autopilot.self_loop import SelfLoop

router = APIRouter()


@router.get("/health")
async def autopilot_health() -> dict[str, Any]:
    return {"success": True, "data": {"status": "ok"}}


@router.post("/execute")
async def autopilot_execute(
    body: dict[str, Any] = Body(...),
) -> JSONResponse:
    try:
        task = body.get("task")
        if not task or not isinstance(task, str):
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "task 字段必填且为字符串"},
            )

        project_root = body.get("project_root") or "."
        runner = TaskRunner(project_root=project_root, auto_commit=body.get("auto_commit", False))
        context = body.get("context")

        task_context = runner.plan(task, context=context)
        if not task_context.allowed:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Task failed safety validation",
                    "violations": task_context.violations,
                },
            )

        passed, output = runner.run_tests()
        sha = runner.commit(f"autopilot: {task}") if body.get("auto_commit", False) else None

        return JSONResponse(
            content={
                "success": True,
                "data": {
                    "task": task_context.task,
                    "role_name": task_context.role_name,
                    "allowed": task_context.allowed,
                    "tests_passed": passed,
                    "test_output": output,
                    "commit_sha": sha,
                },
            }
        )
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(status_code=500, content={"success": False, "error": str(exc)})


@router.post("/self-loop")
async def autopilot_self_loop(
    body: dict[str, Any] = Body(...),
) -> JSONResponse:
    try:
        project_root = body.get("project_root") or "."
        max_iterations = int(body.get("max_iterations", 5))
        max_fixes = int(body.get("max_fixes", 3))

        loop = SelfLoop(
            project_root=project_root,
            auto_commit=body.get("auto_commit", False),
            max_fixes_per_iteration=max_fixes,
        )
        result = loop.run(max_iterations=max_iterations)

        return JSONResponse(
            content={
                "success": result.success,
                "data": {
                    "iterations": len(result.iterations),
                    "issues_found": result.total_issues_found,
                    "issues_fixed": result.total_issues_fixed,
                    "issues_skipped": result.total_issues_skipped,
                    "started_at": result.started_at.isoformat(),
                    "finished_at": result.finished_at.isoformat() if result.finished_at else None,
                },
            }
        )
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(status_code=500, content={"success": False, "error": str(exc)})
