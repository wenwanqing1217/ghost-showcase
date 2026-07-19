"""Observability dashboard data provider for autopilot."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class DashboardProvider:
    """Provide data for the observability dashboard."""

    def __init__(self, project_root: str | os.PathLike[str]) -> None:
        self.project_root = Path(project_root).resolve()

    def get_health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_workflow_summary(self) -> dict[str, Any]:
        return {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
        }

    def get_agent_status(self) -> dict[str, Any]:
        return {
            "active_agents": 0,
            "available_roles": [],
        }

    def get_memory_insights(self) -> dict[str, Any]:
        return {
            "total_entries": 0,
            "success_rate": 0.0,
        }

    def get_approval_summary(self) -> dict[str, Any]:
        return {
            "pending_approvals": 0,
            "approved": 0,
            "rejected": 0,
        }

    def get_dashboard_data(self) -> dict[str, Any]:
        return {
            "health": self.get_health(),
            "workflows": self.get_workflow_summary(),
            "agents": self.get_agent_status(),
            "memory": self.get_memory_insights(),
            "approvals": self.get_approval_summary(),
        }
