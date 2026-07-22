"""Integration tests for the autopilot API route."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from mindflow_map.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestAutopilotAPI:
    def test_health_endpoint(self, client: TestClient) -> None:
        response = client.get("/api/v1/autopilot/health")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "ok"

    def test_execute_endpoint_requires_task(self, client: TestClient) -> None:
        with patch("mindflow_map.api.autopilot.TaskRunner") as MockRunner:
            mock_runner = MagicMock()
            mock_runner.plan.return_value = MagicMock(
                allowed=False,
                violations=["Safety check failed"],
                task="",
                role_name=None,
            )
            MockRunner.return_value = mock_runner

            response = client.post("/api/v1/autopilot/execute", json={})
            assert response.status_code in (200, 400)
            data = response.json()
            assert data.get("success") is False

    def test_execute_endpoint_valid_task(self, client: TestClient) -> None:
        with patch("mindflow_map.api.autopilot.TaskRunner") as MockRunner:
            mock_runner = MagicMock()
            mock_runner.plan.return_value = MagicMock(
                allowed=True,
                violations=[],
                task="refactor WorkflowEngine",
                role_name="Backend Architect",
            )
            mock_runner.run_tests.return_value = (True, "tests passed")
            mock_runner.commit.return_value = "abc123"
            MockRunner.return_value = mock_runner

            response = client.post("/api/v1/autopilot/execute", json={"task": "refactor WorkflowEngine"})
            assert response.status_code == 200
            data = response.json()
            assert data.get("success") is True

    def test_self_loop_endpoint(self, client: TestClient) -> None:
        with patch("mindflow_map.api.autopilot.SelfLoop") as MockLoop:
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.iterations = []
            mock_result.total_issues_found = 0
            mock_result.total_issues_fixed = 0
            mock_result.total_issues_skipped = 0
            mock_result.started_at = MagicMock(isoformat=lambda: "2024-01-01T00:00:00")
            mock_result.finished_at = MagicMock(isoformat=lambda: "2024-01-01T00:01:00")
            MockLoop.return_value.run.return_value = mock_result

            response = client.post(
                "/api/v1/autopilot/self-loop",
                json={"project_root": ".", "max_iterations": 1, "max_fixes": 1},
            )
            assert response.status_code == 200
            data = response.json()
            assert data.get("success") is True
