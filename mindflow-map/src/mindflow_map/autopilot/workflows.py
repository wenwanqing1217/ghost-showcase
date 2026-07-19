"""YAML workflow definitions for the autopilot system.

Supports declarative workflow definitions with:
- Multi-step task sequences
- Conditional branching
- Parallel execution
- Human approval gates
- Error handling and retries
- Variable interpolation
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class StepType(str, Enum):
    TASK = "task"
    CONDITION = "condition"
    PARALLEL = "parallel"
    APPROVAL = "approval"
    DELAY = "delay"
    NOTIFY = "notify"


class ConditionOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"


@dataclass
class WorkflowStep:
    """Single step in a workflow."""

    id: str
    type: str
    name: str
    description: str = ""
    agent: str | None = None
    prompt: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    condition: dict[str, Any] | None = None
    on_success: str | None = None
    on_failure: str | None = None
    retry_count: int = 0
    retry_delay: int = 0


@dataclass
class WorkflowDefinition:
    """Complete workflow definition."""

    id: str
    name: str
    description: str
    version: str
    steps: list[WorkflowStep]
    triggers: list[dict[str, Any]]
    variables: dict[str, Any] = field(default_factory=dict)
    timeout: int = 3600
    retry_policy: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowRun:
    """Instance of a running workflow."""

    id: str
    workflow_id: str
    current_step: str | None
    state: dict[str, Any]
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    error: str | None = None


class WorkflowDefinitionLoader:
    """Load workflow definitions from YAML files."""

    def __init__(self, workflows_dir: str | os.PathLike[str] | None = None) -> None:
        self.workflows_dir = Path(workflows_dir) if workflows_dir is not None else Path("workflows")

    def load(self, workflow_id: str) -> WorkflowDefinition | None:
        """Load a workflow by ID."""
        path = self.workflows_dir / f"{workflow_id}.yaml"
        if not path.exists():
            return None
        return self._parse_yaml(path.read_text(encoding="utf-8"))

    def load_all(self) -> list[WorkflowDefinition]:
        """Load all workflows from directory."""
        workflows = []
        if not self.workflows_dir.exists():
            return workflows
        for path in self.workflows_dir.glob("*.yaml"):
            try:
                workflows.append(self._parse_yaml(path.read_text(encoding="utf-8")))
            except (yaml.YAMLError, KeyError):
                continue
        return workflows

    def save(self, workflow: WorkflowDefinition) -> None:
        """Save a workflow definition to YAML."""
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        path = self.workflows_dir / f"{workflow.id}.yaml"
        data = self._to_dict(workflow)
        path.write_text(yaml.dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")

    def _parse_yaml(self, raw: str) -> WorkflowDefinition:
        data = yaml.safe_load(raw)
        steps = []
        for step_data in data.get("steps", []):
            steps.append(
                WorkflowStep(
                    id=step_data["id"],
                    type=step_data["type"],
                    name=step_data["name"],
                    description=step_data.get("description", ""),
                    agent=step_data.get("agent"),
                    prompt=step_data.get("prompt", ""),
                    parameters=step_data.get("parameters", {}),
                    condition=step_data.get("condition"),
                    on_success=step_data.get("on_success"),
                    on_failure=step_data.get("on_failure"),
                    retry_count=int(step_data.get("retry_count", 0)),
                    retry_delay=int(step_data.get("retry_delay", 0)),
                )
            )
        return WorkflowDefinition(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            steps=steps,
            triggers=data.get("triggers", []),
            variables=data.get("variables", {}),
            timeout=int(data.get("timeout", 3600)),
            retry_policy=data.get("retry_policy", {}),
        )

    def _to_dict(self, workflow: WorkflowDefinition) -> dict[str, Any]:
        return {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "version": workflow.version,
            "steps": [
                {
                    "id": step.id,
                    "type": step.type,
                    "name": step.name,
                    "description": step.description,
                    **({"agent": step.agent} if step.agent else {}),
                    **({"prompt": step.prompt} if step.prompt else {}),
                    "parameters": step.parameters,
                    **({"condition": step.condition} if step.condition else {}),
                    **({"on_success": step.on_success} if step.on_success else {}),
                    **({"on_failure": step.on_failure} if step.on_failure else {}),
                    "retry_count": step.retry_count,
                    "retry_delay": step.retry_delay,
                }
                for step in workflow.steps
            ],
            "triggers": workflow.triggers,
            "variables": workflow.variables,
            "timeout": workflow.timeout,
            "retry_policy": workflow.retry_policy,
        }


class WorkflowEngine:
    """Execute workflow definitions."""

    def __init__(self, workflows_dir: str | os.PathLike[str] | None = None) -> None:
        self.loader = WorkflowDefinitionLoader(workflows_dir)
        self._runs: dict[str, WorkflowRun] = {}
        self._runs_file = Path(workflows_dir) / "workflow_runs.json" if workflows_dir else None
        self._load_runs()

    def _load_runs(self) -> None:
        """Persist and reload runs from disk so API instances share state."""
        if not self._runs_file or not self._runs_file.exists():
            return
        try:
            raw = json.loads(self._runs_file.read_text(encoding="utf-8"))
            for item in raw.values():
                self._runs[item["id"]] = WorkflowRun(
                    id=item["id"],
                    workflow_id=item["workflow_id"],
                    current_step=item.get("current_step"),
                    state=item.get("state", {}),
                    status=item.get("status", "running"),
                    started_at=datetime.fromisoformat(item["started_at"]),
                    finished_at=datetime.fromisoformat(item["finished_at"]) if item.get("finished_at") else None,
                    error=item.get("error"),
                )
        except (json.JSONDecodeError, OSError, KeyError):
            pass

    def _persist_runs(self) -> None:
        if not self._runs_file:
            return
        try:
            data = {}
            for run in self._runs.values():
                data[run.id] = {
                    "id": run.id,
                    "workflow_id": run.workflow_id,
                    "current_step": run.current_step,
                    "state": run.state,
                    "status": run.status,
                    "started_at": run.started_at.isoformat(),
                    "finished_at": run.finished_at.isoformat() if run.finished_at else None,
                    "error": run.error,
                }
            self._runs_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass

    def start(self, workflow_id: str, input_data: dict[str, Any] | None = None) -> WorkflowRun | None:
        """Start a workflow execution."""
        definition = self.loader.load(workflow_id)
        if not definition:
            return None

        run = WorkflowRun(
            id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            current_step=definition.steps[0].id if definition.steps else None,
            state={**(definition.variables or {}), **(input_data or {})},
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        self._runs[run.id] = run
        self._persist_runs()
        return run

    def get_run(self, run_id: str) -> WorkflowRun | None:
        """Get a workflow run by ID."""
        return self._runs.get(run_id)

    def list_runs(self, workflow_id: str | None = None) -> list[WorkflowRun]:
        """List workflow runs."""
        runs = list(self._runs.values())
        if workflow_id:
            runs = [r for r in runs if r.workflow_id == workflow_id]
        return sorted(runs, key=lambda r: r.started_at, reverse=True)
