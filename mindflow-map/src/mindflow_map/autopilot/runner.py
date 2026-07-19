"""Task execution runner for the autopilot system.

Provides a structured interface for executing tasks with proper guardrails:
- File operations within project scope
- Test execution
- Git commit with structured messages
"""

from __future__ import annotations

import dataclasses
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .prompt import assemble_prompt


@dataclasses.dataclass
class TaskContext:
    """Context accumulated during task execution."""

    task: str
    role_name: str | None
    system_prompt: str
    user_prompt: str
    safety_notes: list[str]
    allowed: bool
    violations: list[str]
    files_modified: list[str]
    tests_run: bool
    tests_passed: bool
    committed: bool
    commit_sha: str | None
    started_at: datetime
    finished_at: datetime | None


class TaskRunner:
    """Execute a task with role-aware guardrails.

    Example:
        runner = TaskRunner(project_root=Path("."))
        result = runner.run("refactor WorkflowEngine")
        print(result)
    """

    def __init__(
        self,
        project_root: str | os.PathLike[str] | None = None,
        auto_commit: bool = False,
    ) -> None:
        self.project_root = Path(project_root).resolve() if project_root is not None else Path.cwd().resolve()
        self.auto_commit = auto_commit

    def plan(self, task: str, context: dict[str, Any] | None = None) -> TaskContext:
        """Plan a task without executing it.

        Returns a TaskContext describing the matched role, assembled prompt,
        and safety validation result.

        Args:
            task: Task description.
            context: Optional additional context.

        Returns:
            TaskContext with planning details.
        """
        assembled = assemble_prompt(task, context=context)
        now = datetime.now(timezone.utc)
        return TaskContext(
            task=task,
            role_name=assembled.role.display_name if assembled.role else None,
            system_prompt=assembled.system_prompt,
            user_prompt=assembled.user_prompt,
            safety_notes=assembled.safety_notes,
            allowed=assembled.allowed,
            violations=assembled.violations,
            files_modified=[],
            tests_run=False,
            tests_passed=False,
            committed=False,
            commit_sha=None,
            started_at=now,
            finished_at=None,
        )

    def run(self, task: str, context: dict[str, Any] | None = None) -> TaskContext:
        """Plan and record a task execution.

        Note: Actual code changes are produced by the AI operator based on
        the assembled prompt. This runner provides the execution scaffold
        (validation, test invocation, commit).

        Args:
            task: Task description.
            context: Optional additional context.

        Returns:
            TaskContext with execution details.
        """
        task_context = self.plan(task, context=context)

        if not task_context.allowed:
            return task_context

        # Record finish time; file modifications are tracked externally
        # by the AI operator through the runner's helper methods.
        task_context.finished_at = datetime.now(timezone.utc)
        return task_context

    def check_path(self, path: str | os.PathLike[str]) -> Path:
        """Validate that a path is within the project root.

        Args:
            path: File path to validate.

        Returns:
            Resolved Path.

        Raises:
            ValueError: If the path escapes the project root.
        """
        resolved = (self.project_root / path).resolve()
        if not resolved.is_relative_to(self.project_root):
            raise ValueError(
                f"Scope escape blocked: {resolved} is outside project root {self.project_root}"
            )
        return resolved

    def run_tests(self) -> tuple[bool, str]:
        """Run project tests.

        Returns:
            Tuple of (passed, output).
        """
        cwd = self.project_root
        cmd = _detect_test_command(cwd)

        if isinstance(cmd, str):
            cmd = shlex.split(cmd)

        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False,
                shell=False,
            )
            output = result.stdout + "\n" + result.stderr
            return result.returncode == 0, output
        except Exception as exc:  # noqa: BLE001
            return False, str(exc)

    def commit(self, message: str) -> str | None:
        """Stage and commit changes to git.

        Args:
            message: Commit message.

        Returns:
            Commit SHA, or None if commit failed.
        """
        try:
            subprocess.run(["git", "add", "."], cwd=self.project_root, check=True, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.project_root,
                check=True,
                capture_output=True,
                text=True,
            )
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.project_root,
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None


def _detect_test_command(project_root: Path) -> list[str] | str:
    """Detect the appropriate test command for the project."""
    if (project_root / "pyproject.toml").exists() or (project_root / "setup.py").exists():
        return [sys.executable, "-m", "pytest"]
    if (project_root / "package.json").exists():
        return ["npm", "test"]
    return [sys.executable, "-m", "pytest"]
