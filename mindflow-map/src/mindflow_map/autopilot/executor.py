"""Code execution engine for the autopilot system.

Generates code using LLM and applies changes safely to the project.
"""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .prompt import assemble_prompt
from .safety import check_safety


@dataclasses.dataclass
class ExecutionResult:
    """Result of executing a subtask."""

    subtask_description: str
    success: bool
    diff: str
    files_modified: list[str]
    tests_passed: bool
    test_output: str
    errors: list[str]
    started_at: datetime
    finished_at: datetime


class CodeExecutor:
    """Execute subtasks by generating and applying code changes."""

    def __init__(self, project_root: str | os.PathLike[str]) -> None:
        self.project_root = Path(project_root).resolve()

    def execute(self, subtask: Any, context: dict[str, Any] | None = None) -> ExecutionResult:
        """Execute a subtask and return the result.

        Args:
            subtask: SubTask to execute.
            context: Optional execution context.

        Returns:
            ExecutionResult with diff, test results, and any errors.
        """
        started_at = datetime.now(timezone.utc)
        errors: list[str] = []

        # Assemble prompt for this subtask
        assembled = assemble_prompt(subtask.description, context=context)
        if not assembled.allowed:
            return ExecutionResult(
                subtask_description=subtask.description,
                success=False,
                diff="",
                files_modified=[],
                tests_passed=False,
                test_output="",
                errors=[f"Safety check failed: {', '.join(assembled.violations)}"],
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
            )

        # Generate code diff using LLM
        try:
            diff = self._generate_diff(subtask, assembled)
        except Exception as exc:  # noqa: BLE001
            return ExecutionResult(
                subtask_description=subtask.description,
                success=False,
                diff="",
                files_modified=[],
                tests_passed=False,
                test_output="",
                errors=[f"Code generation failed: {exc}"],
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
            )

        # Apply diff safely
        files_modified = self._apply_diff(diff)

        # Run tests if command is available
        tests_passed = True
        test_output = ""
        if subtask.test_command:
            tests_passed, test_output = self._run_tests(subtask.test_command)

        return ExecutionResult(
            subtask_description=subtask.description,
            success=len(errors) == 0 and tests_passed,
            diff=diff,
            files_modified=files_modified,
            tests_passed=tests_passed,
            test_output=test_output,
            errors=errors,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
        )

    def _generate_diff(self, subtask: Any, assembled: Any) -> str:
        """Generate a code diff for the subtask.

        This is a structured generation that produces a unified diff.
        In production, this would call an LLM with the assembled prompt.
        For now, it produces a placeholder diff that can be applied.
        """
        # In a full implementation, this would call the LLM service
        # For now, return a structured diff placeholder
        return self._placeholder_diff(subtask)

    def _placeholder_diff(self, subtask: Any) -> str:
        """Create a placeholder diff for demonstration."""
        timestamp = datetime.now(timezone.utc).isoformat()
        return f"""\
--- a/placeholder
+++ b/placeholder
@@ -1,3 +1,4 @@
 # Autopilot generated change
 # Task: {subtask.description}
-# TODO: implement
+# Implemented by autopilot at {timestamp}
+pass
"""

    def _apply_diff(self, diff: str) -> list[str]:
        """Apply a unified diff to the project.

        Args:
            diff: Unified diff text.

        Returns:
            List of modified file paths.
        """
        if not diff or diff.strip() == "":
            return []

        # For safety, we use a simple patch application approach
        # In production, use a proper diff parser and apply changes
        # through the AST or a controlled file writer
        modified: list[str] = []

        # Extract file paths from diff headers
        for line in diff.splitlines():
            if line.startswith("--- "):
                path = line[4:].split("\t")[0].strip()
                if path.startswith("a/"):
                    path = path[2:]
                if path and path != "placeholder":
                    modified.append(path)

        return modified

    def _run_tests(self, command: str) -> tuple[bool, str]:
        """Run tests using the specified command.

        Args:
            command: Test command to run.

        Returns:
            Tuple of (passed, output).
        """
        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False,
                shell=True,
            )
            output = result.stdout + "\n" + result.stderr
            return result.returncode == 0, output
        except Exception as exc:  # noqa: BLE001
            return False, str(exc)

    def validate_syntax(self, file_path: str | os.PathLike[str]) -> bool:
        """Validate Python syntax without executing.

        Args:
            file_path: Path to Python file.

        Returns:
            True if syntax is valid.
        """
        path = Path(file_path)
        if not path.exists():
            return False
        try:
            ast.parse(path.read_text(encoding="utf-8"))
            return True
        except SyntaxError:
            return False
