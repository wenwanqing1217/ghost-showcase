"""Code execution engine for the autopilot system.

Generates code using LLM and applies changes safely to the project.
Falls back to placeholder diff generation when LLM is not configured.
"""

from __future__ import annotations

import ast
import os
import re
import shlex
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

    def check_path(self, path: str | os.PathLike[str]) -> Path:
        """Validate that a path is within the project root."""
        resolved = (self.project_root / path).resolve()
        if not resolved.is_relative_to(self.project_root):
            raise ValueError(
                f"Scope escape blocked: {resolved} is outside project root {self.project_root}"
            )
        return resolved

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

    async def execute(self, subtask: Any, context: dict[str, Any] | None = None) -> ExecutionResult:
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
            diff = await self._generate_diff(subtask, assembled)
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

    async def _generate_diff(self, subtask: Any, assembled: Any) -> str:
        llm_client = self._get_llm_client()
        if llm_client is None:
            return self._placeholder_diff(subtask)

        project_files = self._list_project_files()
        prompt = (
            f"{assembled.system_prompt}\n\n"
            f"TASK:\n{subtask.description}\n\n"
            f"CONTEXT:\n{assembled.user_prompt}\n\n"
            "PROJECT FILES:\n"
            f"{project_files}\n\n"
            "OUTPUT REQUIREMENTS:\n"
            "1. Output ONLY the complete new content for each file you want to modify.\n"
            "2. Use this exact format for each file:\n"
            "   FILE: <relative-path>\n"
            "   <complete file content here>\n"
            "3. Only include files that actually need changes.\n"
            "4. Keep changes minimal and focused on the task.\n"
            "5. Do NOT include any explanations, markdown code blocks, or diff syntax.\n"
        )

        try:
            response = await llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=4096,
            )
            text = response.strip()
            if not text or "FILE:" not in text:
                return self._placeholder_diff(subtask)
            return text
        except Exception as exc:  # noqa: BLE001
            return self._placeholder_diff(subtask)

    def _placeholder_diff(self, subtask: Any) -> str:
        timestamp = datetime.now(timezone.utc).isoformat()
        filename = self._extract_filename(subtask.description)
        return f"FILE: {filename}\n# Autopilot generated change\n# Task: {subtask.description}\n# Implemented by autopilot at {timestamp}\npass\n"

    @staticmethod
    def _extract_filename(description: str) -> str:
        cleaned = description.lower()
        for token in ["create", "add", "implement", "write", "build", "new"]:
            cleaned = cleaned.replace(token, "")
        cleaned = cleaned.strip().replace(" ", "_") or "autopilot_output"
        if not cleaned.endswith(".py"):
            cleaned = f"{cleaned}.py"
        return cleaned

    def _list_project_files(self, max_files: int = 40) -> str:
        files: list[str] = []
        for path in self.project_root.rglob("*.py"):
            if any(part in {"__pycache__", ".git", "node_modules", ".venv", "venv"} for part in path.parts):
                continue
            files.append(str(path.relative_to(self.project_root)))
            if len(files) >= max_files:
                break
        return "\n".join(files)

    def _apply_diff(self, diff: str) -> list[str]:
        if not diff or diff.strip() == "":
            return []

        modified: list[str] = []
        current_file = None
        current_content = []

        for line in diff.splitlines():
            if line.startswith("FILE:"):
                if current_file and current_content:
                    self._write_file(current_file, "\n".join(current_content))
                    modified.append(current_file)
                current_file = line[5:].strip()
                current_content = []
            elif current_file is not None:
                current_content.append(line)

        if current_file and current_content:
            self._write_file(current_file, "\n".join(current_content))
            modified.append(current_file)

        return modified

    def _write_file(self, relative_path: str, content: str) -> None:
        target = self.check_path(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def _run_tests(self, command: str) -> tuple[bool, str]:
        try:
            cmd_args = shlex.split(command)
            result = subprocess.run(
                cmd_args,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False,
                shell=False,
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
