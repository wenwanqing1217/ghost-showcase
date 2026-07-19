"""Tests for autopilot scheduler and workflow API."""

from __future__ import annotations

import json
import datetime

import pytest

from mindflow_map.autopilot.scheduler import CronExpression, ScheduledJob, WorkflowScheduler
from mindflow_map.autopilot.workflows import WorkflowDefinitionLoader, WorkflowEngine, WorkflowStep, WorkflowDefinition


class TestCronExpression:
    def test_matches_exact_minute(self) -> None:
        cron = CronExpression("5 * * * *")
        assert cron.matches(datetime.datetime(2024, 1, 1, 12, 5)) is True
        assert cron.matches(datetime.datetime(2024, 1, 1, 12, 6)) is False

    def test_matches_every_minute(self) -> None:
        cron = CronExpression("* * * * *")
        assert cron.matches(datetime.datetime(2024, 1, 1, 12, 5)) is True
        assert cron.matches(datetime.datetime(2024, 1, 1, 12, 6)) is True

    def test_rejects_invalid_expression(self) -> None:
        with pytest.raises(ValueError):
            CronExpression("* * *")


class TestWorkflowScheduler:
    def test_schedule_persists_job(self, tmp_path: Path) -> None:
        engine = WorkflowEngine(workflows_dir=tmp_path)
        scheduler = WorkflowScheduler(workflow_engine=engine, storage_path=tmp_path / "jobs.json")
        scheduler.stop = lambda: None
        job = scheduler.schedule("wf1", "*/5 * * * *")
        assert job.workflow_id == "wf1"
        assert scheduler.list_jobs() == [job]

    def test_list_jobs_filters_by_workflow(self, tmp_path: Path) -> None:
        engine = WorkflowEngine(workflows_dir=tmp_path)
        scheduler = WorkflowScheduler(workflow_engine=engine, storage_path=tmp_path / "jobs.json")
        scheduler.stop = lambda: None
        scheduler.schedule("wf1", "*/5 * * * *")
        scheduler.schedule("wf2", "*/10 * * * *")
        assert len(scheduler.list_jobs()) == 2
        assert len(scheduler.list_jobs(workflow_id="wf1")) == 1

    def test_cancel_removes_job(self, tmp_path: Path) -> None:
        engine = WorkflowEngine(workflows_dir=tmp_path)
        scheduler = WorkflowScheduler(workflow_engine=engine, storage_path=tmp_path / "jobs.json")
        scheduler.stop = lambda: None
        job = scheduler.schedule("wf1", "*/5 * * * *")
        assert scheduler.cancel(job.id) is True
        assert scheduler.list_jobs() == []


class TestAutopilotWorkflowAPI:
    def test_list_workflows(self, tmp_path: Path) -> None:
        from fastapi.testclient import TestClient
        from mindflow_map.api.autopilot import router
        from mindflow_map.main import app

        loader = WorkflowDefinitionLoader(tmp_path)
        wf = WorkflowDefinition(
            id="api-wf", name="API Workflow", description="", version="1.0.0",
            steps=[WorkflowStep(id="s1", type="task", name="Lint", prompt="run lint")],
            triggers=[],
        )
        loader.save(wf)

        client = TestClient(app)
        response = client.get("/api/v1/autopilot/workflows", params={"workflows_dir": str(tmp_path)})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["workflows"]) == 1
        assert data["data"]["workflows"][0]["id"] == "api-wf"

    def test_create_and_start_workflow(self, tmp_path: Path) -> None:
        from fastapi.testclient import TestClient
        from mindflow_map.main import app

        client = TestClient(app)
        create_resp = client.post(
            "/api/v1/autopilot/workflows",
            params={"workflows_dir": str(tmp_path)},
            json={
                "id": "created-wf",
                "name": "Created",
                "description": "created via api",
                "version": "1.0.0",
                "steps": [{"id": "s1", "type": "task", "name": "Echo", "prompt": "echo"}],
                "triggers": [],
            },
        )
        assert create_resp.status_code == 200
        assert create_resp.json()["data"]["id"] == "created-wf"

        start_resp = client.post(
            "/api/v1/autopilot/workflows/created-wf/start",
            params={"workflows_dir": str(tmp_path)},
            json={"input_data": {"key": "value"}},
        )
        assert start_resp.status_code == 200
        assert start_resp.json()["success"] is True

    def test_list_workflow_runs(self, tmp_path: Path) -> None:
        from fastapi.testclient import TestClient
        from mindflow_map.main import app

        loader = WorkflowDefinitionLoader(tmp_path)
        wf = WorkflowDefinition(
            id="runs-wf", name="Runs", description="", version="1.0.0",
            steps=[WorkflowStep(id="s1", type="task", name="Lint", prompt="run lint")],
            triggers=[],
        )
        loader.save(wf)

        client = TestClient(app)
        start_resp = client.post(
            "/api/v1/autopilot/workflows/runs-wf/start",
            params={"workflows_dir": str(tmp_path)},
            json={"input_data": {}},
        )
        assert start_resp.status_code == 200

        response = client.get("/api/v1/autopilot/workflows/runs-wf/runs", params={"workflows_dir": str(tmp_path)})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["runs"]) >= 1

    def test_scheduler_job_lifecycle(self, tmp_path: Path) -> None:
        from fastapi.testclient import TestClient
        from mindflow_map.main import app

        client = TestClient(app)
        create_resp = client.post(
            "/api/v1/autopilot/scheduler/jobs",
            json={
                "workflow_id": "sched-wf",
                "cron_expression": "*/10 * * * *",
                "input_data": {},
                "workflows_dir": str(tmp_path),
                "storage_path": str(tmp_path / "jobs.json"),
            },
        )
        assert create_resp.status_code == 200
        job_id = create_resp.json()["data"]["id"]

        list_resp = client.get(
            "/api/v1/autopilot/scheduler/jobs",
            params={"storage_path": str(tmp_path / "jobs.json")},
        )
        assert list_resp.status_code == 200
        jobs = list_resp.json()["data"]["jobs"]
        assert any(job["id"] == job_id for job in jobs)
