"""Workflow scheduler with cron-like triggers for the autopilot system.

Supports scheduling workflow executions using simple cron expressions.
"""

from __future__ import annotations

import json
import os
import re
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .workflows import YamlWorkflowEngine, WorkflowRun


class CronExpression:
    """Simple cron expression parser supporting standard 5-field cron.

    Format: minute hour day month weekday
    Each field can be: * , - / or a number
    """

    def __init__(self, expression: str) -> None:
        self.original = expression
        parts = expression.strip().split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {expression!r}. Expected 5 fields.")
        self.minute, self.hour, self.day, self.month, self.weekday = parts

    def matches(self, dt: datetime) -> bool:
        return (
            self._field_matches(self.minute, dt.minute, 0, 59)
            and self._field_matches(self.hour, dt.hour, 0, 23)
            and self._field_matches(self.day, dt.day, 1, 31)
            and self._field_matches(self.month, dt.month, 1, 12)
            and self._field_matches(self.weekday, dt.weekday(), 0, 6)
        )

    def _field_matches(self, field: str, value: int, min_val: int, max_val: int) -> bool:
        if field == "*":
            return True
        for part in field.split(","):
            if "/" in part:
                start, step = part.split("/", 1)
                start_val = int(start) if start else min_val
                if value >= start_val and (value - start_val) % int(step) == 0:
                    return True
            elif "-" in part:
                start, end = part.split("-", 1)
                if int(start) <= value <= int(end):
                    return True
            else:
                if int(part) == value:
                    return True
        return False


@dataclass
class ScheduledJob:
    """A scheduled workflow execution job."""

    id: str
    workflow_id: str
    cron_expression: str
    input_data: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None


class WorkflowScheduler:
    """Schedule and manage recurring workflow executions."""

    def __init__(self, workflow_engine: YamlWorkflowEngine, storage_path: str | os.PathLike[str] | None = None) -> None:
        self.workflow_engine = workflow_engine
        self.storage_path = Path(storage_path) if storage_path is not None else Path("scheduled_jobs.json")
        self._jobs: dict[str, ScheduledJob] = {}
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._load_jobs()

    def start(self) -> None:
        """Start the scheduler background thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the scheduler background thread."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    def schedule(self, workflow_id: str, cron_expression: str, input_data: dict[str, Any] | None = None) -> ScheduledJob:
        """Schedule a workflow to run on a cron schedule."""
        job = ScheduledJob(
            id=str(__import__("uuid").uuid4()),
            workflow_id=workflow_id,
            cron_expression=cron_expression,
            input_data=input_data or {},
        )
        self._update_next_run(job)
        with self._lock:
            self._jobs[job.id] = job
        self._persist_jobs()
        return job

    def cancel(self, job_id: str) -> bool:
        """Cancel a scheduled job."""
        with self._lock:
            if job_id not in self._jobs:
                return False
            del self._jobs[job_id]
        self._persist_jobs()
        return True

    def list_jobs(self, workflow_id: str | None = None) -> list[ScheduledJob]:
        """List scheduled jobs."""
        with self._lock:
            jobs = list(self._jobs.values())
        if workflow_id:
            jobs = [job for job in jobs if job.workflow_id == workflow_id]
        return jobs

    def _run_loop(self) -> None:
        """Background loop checking for jobs to run."""
        while not self._stop_event.is_set():
            now = datetime.now(timezone.utc)
            with self._lock:
                jobs = list(self._jobs.values())
            for job in jobs:
                if not job.enabled:
                    continue
                if job.next_run_at and now >= job.next_run_at:
                    self._trigger_job(job)
                    job.last_run_at = now
                    self._update_next_run(job)
                    self._persist_jobs()
            self._stop_event.wait(30)

    def _trigger_job(self, job: ScheduledJob) -> WorkflowRun | None:
        """Trigger a workflow execution."""
        try:
            return self.workflow_engine.start(job.workflow_id, job.input_data)
        except Exception:  # noqa: BLE001
            return None

    def _update_next_run(self, job: ScheduledJob) -> None:
        try:
            cron = CronExpression(job.cron_expression)
            now = datetime.now(timezone.utc)
            # Start searching from the next minute
            candidate = now.replace(second=0, microsecond=0) + __import__("datetime").timedelta(minutes=1)
            # Bounded search: up to 2 years (covers all reasonable cron patterns)
            end_year = candidate.year + 2
            while candidate.year < end_year:
                if cron.matches(candidate):
                    job.next_run_at = candidate
                    return
                candidate += __import__("datetime").timedelta(minutes=1)
            job.next_run_at = None
        except ValueError:
            job.next_run_at = None

    def _persist_jobs(self) -> None:
        try:
            data = {}
            with self._lock:
                for job in self._jobs.values():
                    data[job.id] = {
                        "id": job.id,
                        "workflow_id": job.workflow_id,
                        "cron_expression": job.cron_expression,
                        "input_data": job.input_data,
                        "enabled": job.enabled,
                        "created_at": job.created_at.isoformat(),
                        "last_run_at": job.last_run_at.isoformat() if job.last_run_at else None,
                        "next_run_at": job.next_run_at.isoformat() if job.next_run_at else None,
                    }
            self.storage_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass

    def _load_jobs(self) -> None:
        if not self.storage_path.exists():
            return
        try:
            raw = json.loads(self.storage_path.read_text(encoding="utf-8"))
            with self._lock:
                for item in raw.values():
                    job = ScheduledJob(
                        id=item["id"],
                        workflow_id=item["workflow_id"],
                        cron_expression=item["cron_expression"],
                        input_data=item.get("input_data", {}),
                        enabled=item.get("enabled", True),
                        created_at=datetime.fromisoformat(item["created_at"]),
                        last_run_at=datetime.fromisoformat(item["last_run_at"]) if item.get("last_run_at") else None,
                        next_run_at=datetime.fromisoformat(item["next_run_at"]) if item.get("next_run_at") else None,
                    )
                    self._jobs[job.id] = job
        except (json.JSONDecodeError, OSError, KeyError):
            pass
