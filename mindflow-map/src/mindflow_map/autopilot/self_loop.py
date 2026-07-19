"""Self-loop / continuous autonomous improvement for the autopilot system.

This module provides:
- Codebase scanning (lint, tests, static analysis)
- Issue prioritization
- Autonomous fix generation and application
- Verification and commit
- Continuous loop with configurable max iterations
"""

from __future__ import annotations

import dataclasses
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .orchestrator import TaskOrchestrator
from .executor import CodeExecutor
from .git_workflow import GitWorkflow
from .prompt import assemble_prompt
from .safety import check_safety


@dataclasses.dataclass
class Issue:
    """Detected issue in the codebase."""

    id: str
    category: str
    severity: str
    description: str
    file_path: str
    line_number: int | None
    fix_description: str | None
    auto_fixable: bool


@dataclasses.dataclass
class LoopIteration:
    """Single iteration of the self-loop."""

    iteration: int
    started_at: datetime
    finished_at: datetime | None
    issues_scanned: int
    issues_found: int
    issues_fixed: int
    issues_skipped: int
    tests_passed: bool
    test_output: str
    committed: bool
    commit_sha: str | None
    errors: list[str]


@dataclasses.dataclass
class LoopResult:
    """Final result of the self-loop run."""

    iterations: list[LoopIteration]
    total_issues_found: int
    total_issues_fixed: int
    total_issues_skipped: int
    success: bool
    started_at: datetime
    finished_at: datetime | None


class CodebaseScanner:
    """Scan the codebase for issues."""

    def __init__(self, project_root: str | os.PathLike[str]) -> None:
        self.project_root = Path(project_root).resolve()

    def scan(self) -> list[Issue]:
        """Scan the codebase for issues.

        Returns:
            List of detected issues.
        """
        issues: list[Issue] = []

        # Run linting
        issues.extend(self._run_lint())

        # Run tests
        issues.extend(self._run_tests_scan())

        # Run type checking if available
        issues.extend(self._run_type_check())

        # Scan for common code smells
        issues.extend(self._scan_code_smells())

        return issues

    def _run_lint(self) -> list[Issue]:
        issues: list[Issue] = []
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "--co", "-q"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                issues.append(
                    Issue(
                        id="lint-001",
                        category="lint",
                        severity="P2",
                        description="Pytest collection failed",
                        file_path="",
                        line_number=None,
                        fix_description="Fix test collection errors",
                        auto_fixable=False,
                    )
                )
        except Exception:  # noqa: BLE001
            pass

        # Check for common Python issues
        for py_file in self.project_root.rglob("*.py"):
            if "node_modules" in str(py_file) or "__pycache__" in str(py_file):
                continue
            try:
                text = py_file.read_text(encoding="utf-8")
                rel = str(py_file.relative_to(self.project_root))

                if "print(" in text and "tests/" not in rel:
                    issues.append(
                        Issue(
                            id=f"print-{py_file.name}",
                            category="code_smell",
                            severity="P3",
                            description="Debug print statement found",
                            file_path=rel,
                            line_number=None,
                            fix_description="Remove debug print statement",
                            auto_fixable=True,
                        )
                    )

                if "import *" in text:
                    issues.append(
                        Issue(
                            id=f"star-import-{py_file.name}",
                            category="code_smell",
                            severity="P3",
                            description="Wildcard import found",
                            file_path=rel,
                            line_number=None,
                            fix_description="Replace wildcard import with explicit imports",
                            auto_fixable=False,
                        )
                    )

                if "except:" in text or "except Exception:" in text:
                    issues.append(
                        Issue(
                            id=f"bare-except-{py_file.name}",
                            category="reliability",
                            severity="P2",
                            description="Bare except clause found",
                            file_path=rel,
                            line_number=None,
                            fix_description="Use specific exception types",
                            auto_fixable=False,
                        )
                    )
            except OSError:
                continue

        return issues

    def _run_tests_scan(self) -> list[Issue]:
        issues: list[Issue] = []
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-x", "--tb=short"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                # Parse pytest output for failures
                for line in result.stdout.splitlines():
                    if "FAILED" in line:
                        test_name = line.split("FAILED ")[-1].strip()
                        issues.append(
                            Issue(
                                id=f"test-{abs(hash(test_name))}",
                                category="test_failure",
                                severity="P1",
                                description=f"Test failed: {test_name}",
                                file_path="",
                                line_number=None,
                                fix_description="Fix failing test",
                                auto_fixable=False,
                            )
                        )
                        break
        except Exception:  # noqa: BLE001
            pass
        return issues

    def _run_type_check(self) -> list[Issue]:
        issues: list[Issue] = []
        # Try mypy if available
        try:
            result = subprocess.run(
                ["mypy", "src"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                for line in result.stdout.splitlines():
                    if ": error:" in line:
                        parts = line.split(":")
                        file_path = parts[0] if parts else ""
                        issues.append(
                            Issue(
                                id=f"type-{abs(hash(line))}",
                                category="type_error",
                                severity="P2",
                                description=f"Type error: {line}",
                                file_path=file_path,
                                line_number=None,
                                fix_description="Fix type error",
                                auto_fixable=False,
                            )
                        )
                        break
        except FileNotFoundError:
            pass
        return issues

    def _scan_code_smells(self) -> list[Issue]:
        issues: list[Issue] = []
        # Scan for TODOs, FIXMEs, large files, etc.
        for py_file in self.project_root.rglob("*.py"):
            if "node_modules" in str(py_file) or "__pycache__" in str(py_file):
                continue
            try:
                text = py_file.read_text(encoding="utf-8")
                lines = text.splitlines()
                if len(lines) > 500:
                    issues.append(
                        Issue(
                            id=f"long-{py_file.name}",
                            category="code_smell",
                            severity="P3",
                            description=f"File too long: {len(lines)} lines",
                            file_path=str(py_file.relative_to(self.project_root)),
                            line_number=None,
                            fix_description="Consider splitting into smaller modules",
                            auto_fixable=False,
                        )
                    )
            except OSError:
                continue
        return issues


class IssuePrioritizer:
    """Prioritize issues for fixing."""

    SEVERITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}

    def prioritize(self, issues: list[Issue]) -> list[Issue]:
        """Sort issues by severity and auto-fixability.

        Args:
            issues: List of issues to prioritize.

        Returns:
            Sorted list of issues.
        """
        return sorted(
            issues,
            key=lambda i: (
                self.SEVERITY_ORDER.get(i.severity, 99),
                0 if i.auto_fixable else 1,
                i.id,
            ),
        )


class SelfLoop:
    """Autonomous self-improvement loop for the codebase.

    Example:
        loop = SelfLoop(project_root=".")
        result = loop.run(max_iterations=5)
        print(f"Fixed {result.total_issues_fixed} issues")
    """

    def __init__(
        self,
        project_root: str | os.PathLike[str],
        auto_commit: bool = False,
        max_fixes_per_iteration: int = 3,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.auto_commit = auto_commit
        self.max_fixes_per_iteration = max_fixes_per_iteration

        self.scanner = CodebaseScanner(project_root)
        self.prioritizer = IssuePrioritizer()
        self.orchestrator = TaskOrchestrator(project_root)
        self.executor = CodeExecutor(project_root)
        self.git_workflow = GitWorkflow(project_root)

    def run(self, max_iterations: int = 5) -> LoopResult:
        """Run the self-improvement loop.

        Args:
            max_iterations: Maximum number of iterations to run.

        Returns:
            LoopResult with summary of all iterations.
        """
        started_at = datetime.now(timezone.utc)
        iterations: list[LoopIteration] = []
        total_found = 0
        total_fixed = 0
        total_skipped = 0

        for iteration_num in range(1, max_iterations + 1):
            iteration = self._run_iteration(iteration_num)
            iterations.append(iteration)

            total_found += iteration.issues_found
            total_fixed += iteration.issues_fixed
            total_skipped += iteration.issues_skipped

            # Stop if no issues found or all fixed
            if iteration.issues_found == 0 or iteration.issues_fixed == 0:
                break

        finished_at = datetime.now(timezone.utc)
        success = all(it.tests_passed for it in iterations) if iterations else False

        return LoopResult(
            iterations=iterations,
            total_issues_found=total_found,
            total_issues_fixed=total_fixed,
            total_issues_skipped=total_skipped,
            success=success,
            started_at=started_at,
            finished_at=finished_at,
        )

    def _run_iteration(self, iteration_num: int) -> LoopIteration:
        """Run a single iteration of the loop."""
        started_at = datetime.now(timezone.utc)
        errors: list[str] = []

        # Scan for issues
        issues = self.scanner.scan()
        prioritized = self.prioritizer.prioritize(issues)

        # Limit fixes per iteration
        to_fix = prioritized[: self.max_fixes_per_iteration]
        skipped = len(prioritized) - len(to_fix)

        # Fix issues
        fixed = 0
        for issue in to_fix:
            try:
                if self._fix_issue(issue):
                    fixed += 1
                else:
                    skipped += 1
            except Exception as exc:  # noqa: BLE001
                errors.append(f"Failed to fix {issue.id}: {exc}")
                skipped += 1

        # Run tests
        tests_passed = True
        test_output = ""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-q"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False,
            )
            test_output = result.stdout + "\n" + result.stderr
            tests_passed = result.returncode == 0
        except Exception as exc:  # noqa: BLE001
            tests_passed = False
            test_output = str(exc)
            errors.append(f"Test execution failed: {exc}")

        # Commit if enabled and tests passed
        committed = False
        commit_sha = None
        if self.auto_commit and tests_passed and fixed > 0:
            try:
                commit = self.git_workflow.commit(f"autopilot: self-loop iteration {iteration_num} - fixed {fixed} issues")
                committed = commit.succeeded
                commit_sha = commit.sha
            except Exception as exc:  # noqa: BLE001
                errors.append(f"Commit failed: {exc}")

        return LoopIteration(
            iteration=iteration_num,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            issues_scanned=len(issues),
            issues_found=len(prioritized),
            issues_fixed=fixed,
            issues_skipped=skipped,
            tests_passed=tests_passed,
            test_output=test_output,
            committed=committed,
            commit_sha=commit_sha,
            errors=errors,
        )

    def _fix_issue(self, issue: Issue) -> bool:
        """Attempt to fix an issue.

        Args:
            issue: Issue to fix.

        Returns:
            True if fix was applied successfully.
        """
        if not issue.auto_fixable or not issue.file_path:
            return False

        # Assemble prompt for the fix
        task = f"Fix issue: {issue.description} in {issue.file_path}. {issue.fix_description or ''}"
        assembled = assemble_prompt(task)
        if not assembled.allowed:
            return False

        # Execute the fix
        result = self.executor.execute(
            type(
                "SubTask",
                (object,),
                {
                    "description": task,
                    "test_command": None,
                    "role": assembled.role,
                    "system_prompt": assembled.system_prompt,
                    "user_prompt": assembled.user_prompt,
                },
            )()
        )

        return result.success
