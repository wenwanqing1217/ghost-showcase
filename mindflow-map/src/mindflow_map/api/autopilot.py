"""Autopilot API route."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse

from mindflow_map.autopilot.orchestrator import TaskOrchestrator
from mindflow_map.autopilot.runner import TaskRunner
from mindflow_map.autopilot.self_loop import SelfLoop
from mindflow_map.autopilot.workflows import WorkflowDefinition, WorkflowDefinitionLoader, WorkflowEngine, WorkflowStep
from mindflow_map.autopilot.scheduler import WorkflowScheduler, ScheduledJob

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


@router.get("/workflows")
async def list_workflows(workflows_dir: str = "workflows") -> JSONResponse:
    try:
        loader = WorkflowDefinitionLoader(workflows_dir)
        definitions = loader.load_all()
        return JSONResponse(
            content={
                "success": True,
                "data": {
                    "workflows": [
                        {
                            "id": wf.id,
                            "name": wf.name,
                            "description": wf.description,
                            "version": wf.version,
                            "steps": len(wf.steps),
                            "triggers": wf.triggers,
                        }
                        for wf in definitions
                    ]
                },
            }
        )
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(status_code=500, content={"success": False, "error": str(exc)})


@router.post("/workflows")
async def create_workflow(body: dict[str, Any] = Body(...), workflows_dir: str = "workflows") -> JSONResponse:
    try:
        loader = WorkflowDefinitionLoader(workflows_dir)
        steps_data = body.get("steps", [])
        steps = [
            WorkflowStep(
                id=step["id"],
                type=step.get("type", "task"),
                name=step.get("name", ""),
                description=step.get("description", ""),
                prompt=step.get("prompt", ""),
                agent=step.get("agent"),
                parameters=step.get("parameters", {}),
            )
            for step in steps_data
        ]
        workflow = WorkflowDefinition(
            id=body["id"],
            name=body["name"],
            description=body.get("description", ""),
            version=body.get("version", "1.0.0"),
            steps=steps,
            triggers=body.get("triggers", []),
            variables=body.get("variables", {}),
        )
        loader.save(workflow)
        return JSONResponse(
            content={
                "success": True,
                "data": {
                    "id": workflow.id,
                    "name": workflow.name,
                    "steps": len(workflow.steps),
                },
            }
        )
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(status_code=500, content={"success": False, "error": str(exc)})


@router.post("/workflows/{workflow_id}/start")
async def start_workflow(workflow_id: str, body: dict[str, Any] = Body(...), workflows_dir: str = "workflows") -> JSONResponse:
    try:
        engine = WorkflowEngine(workflows_dir=workflows_dir)
        run = engine.start(workflow_id, body.get("input_data"))
        if run is None:
            return JSONResponse(status_code=404, content={"success": False, "error": "workflow not found"})
        return JSONResponse(
            content={
                "success": True,
                "data": {
                    "run_id": run.id,
                    "workflow_id": run.workflow_id,
                    "status": run.status,
                    "state": run.state,
                },
            }
        )
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(status_code=500, content={"success": False, "error": str(exc)})


@router.get("/workflows/{workflow_id}/runs")
async def list_workflow_runs(workflow_id: str, workflows_dir: str = "workflows") -> JSONResponse:
    try:
        engine = WorkflowEngine(workflows_dir=workflows_dir)
        runs = engine.list_runs(workflow_id=workflow_id)
        return JSONResponse(
            content={
                "success": True,
                "data": {
                    "runs": [
                        {
                            "id": run.id,
                            "status": run.status,
                            "current_step": run.current_step,
                            "started_at": run.started_at.isoformat(),
                            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
                            "error": run.error,
                        }
                        for run in runs
                    ]
                },
            }
        )
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(status_code=500, content={"success": False, "error": str(exc)})


@router.post("/scheduler/jobs")
async def create_scheduled_job(body: dict[str, Any] = Body(...)) -> JSONResponse:
    try:
        workflows_dir = body.get("workflows_dir", "workflows")
        storage_path = body.get("storage_path", "scheduled_jobs.json")
        engine = WorkflowEngine(workflows_dir=workflows_dir)
        scheduler = WorkflowScheduler(workflow_engine=engine, storage_path=storage_path)
        job = scheduler.schedule(
            workflow_id=body["workflow_id"],
            cron_expression=body["cron_expression"],
            input_data=body.get("input_data", {}),
        )
        return JSONResponse(
            content={
                "success": True,
                "data": {
                    "id": job.id,
                    "workflow_id": job.workflow_id,
                    "cron_expression": job.cron_expression,
                    "next_run_at": job.next_run_at.isoformat() if job.next_run_at else None,
                },
            }
        )
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(status_code=500, content={"success": False, "error": str(exc)})


@router.get("/scheduler/jobs")
async def list_scheduled_jobs(storage_path: str = "scheduled_jobs.json") -> JSONResponse:
    try:
        scheduler = WorkflowScheduler(workflow_engine=WorkflowEngine(), storage_path=storage_path)
        jobs = scheduler.list_jobs()
        return JSONResponse(
            content={
                "success": True,
                "data": {
                    "jobs": [
                        {
                            "id": job.id,
                            "workflow_id": job.workflow_id,
                            "cron_expression": job.cron_expression,
                            "enabled": job.enabled,
                            "last_run_at": job.last_run_at.isoformat() if job.last_run_at else None,
                            "next_run_at": job.next_run_at.isoformat() if job.next_run_at else None,
                        }
                        for job in jobs
                    ]
                },
            }
        )
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(status_code=500, content={"success": False, "error": str(exc)})
