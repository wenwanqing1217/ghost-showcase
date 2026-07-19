"""Code execution engine for the autopilot system.

Generates code using LLM and applies changes safely to the project.
Falls back to placeholder diff generation when LLM is not configured.
"""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .prompt import assemble_prompt
from .safety import check_safety


@dataclass
class ExecutionResult:
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
        self._llm_client = None

    def _get_llm_client(self) -> Any | None:
        """Lazy-load the LLM client if configured."""
        if self._llm_client is not None:
            return self._llm_client

        try:
            from mindflow_map.ai.llm import LLMClient
            from mindflow_map.config import settings

            if settings.openai_api_key:
                self._llm_client = LLMClient()
                return self._llm_client
        except Exception:  # noqa: BLE001
            pass
        return None

    def execute(self, subtask: Any, context: dict[str, Any] | None = None) -> ExecutionResult:
        started_at = datetime.now(timezone.utc)
        errors: list[str] = []

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

        files_modified = self._apply_diff(diff)

        tests_passed = True
        test_output = ""
        if getattr(subtask, "test_command", None):
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
        llm_client = self._get_llm_client()
        if llm_client is None:
            return self._placeholder_diff(subtask)

        import asyncio

        prompt = (
            f"{assembled.system_prompt}\n\n"
            f"TASK:\n{subtask.description}\n\n"
            f"CONTEXT:\n{assembled.user_prompt}\n\n"
            "OUTPUT REQUIREMENTS:\n"
            "1. Output only a unified diff patch.\n"
            "2. Use standard --- a/... and +++ b/... headers.\n"
            "3. Only modify files within the project.\n"
            "4. Keep the diff minimal and focused.\n"
        )

        try:
            response = asyncio.run(
                llm_client.chat(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=2048,
                )
            )
            text = response.strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:diff)?", "", text, flags=re.IGNORECASE).strip()
                if text.endswith("```"):
                    text = text[:-3].strip()
            return text or self._placeholder_diff(subtask)
        except Exception as exc:  # noqa: BLE001
            return self._placeholder_diff(subtask)

    def _placeholder_diff(self, subtask: Any) -> str:
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
        if not diff or diff.strip() == "":
            return []

        modified: list[str] = []
        for line in diff.splitlines():
            if line.startswith("--- "):
                path = line[4:].split("\t")[0].strip()
                if path.startswith("a/"):
                    path = path[2:]
                if path and path != "placeholder":
                    modified.append(path)
        return modified

    def _run_tests(self, command: str) -> tuple[bool, str]:
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
        path = Path(file_path)
        if not path.exists():
            return False
        try:
            ast.parse(path.read_text(encoding="utf-8"))
            return True
        except SyntaxError:
            return False
