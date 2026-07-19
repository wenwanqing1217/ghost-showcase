"""Task decomposition and expert assignment for the autopilot system.

This module acts as the 'project manager' that breaks down complex tasks
into subtasks and assigns them to appropriate expert roles from zcode-brain.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .roles import Role, load_roles, match_role


@dataclass
class SubTask:
    """A single decomposed subtask with assigned expert role."""

    description: str
    role: Role | None
    system_prompt: str
    user_prompt: str
    estimated_complexity: str
    suggested_files: list[str]
    test_command: str | None


@dataclass
class TaskPlan:
    """Complete decomposition of a user request into executable subtasks."""

    original_task: str
    summary: str
    subtasks: list[SubTask]
    total_complexity: str
    risks: list[str]
    estimated_duration: str
    generated_at: datetime


class TaskOrchestrator:
    """Decompose tasks and assign expert roles.

    This is the 'brain' of the autopilot system that decides:
    1. What needs to be done
    2. Which expert should do it
    3. What context they need
    """

    def __init__(self, project_root: str | os.PathLike[str]) -> None:
        self.project_root = Path(project_root).resolve()
        self.roles = load_roles()

    def decompose(self, task: str, context: dict[str, Any] | None = None) -> TaskPlan:
        """Break down a complex task into subtasks.

        Args:
            task: Natural language task description.
            context: Optional context about the project state.

        Returns:
            TaskPlan with decomposed subtasks.
        """
        context = context or {}
        task_lower = task.lower()

        # Detect task type and apply decomposition patterns
        if self._is_refactor_task(task_lower):
            return self._decompose_refactor(task, context)
        if self._is_feature_task(task_lower):
            return self._decompose_feature(task, context)
        if self._is_bugfix_task(task_lower):
            return self._decompose_bugfix(task, context)
        if self._is_security_task(task_lower):
            return self._decompose_security(task, context)
        if self._is_devops_task(task_lower):
            return self._decompose_devops(task, context)

        # Default: single subtask with best matching role
        role = match_role(task, roles=self.roles)
        return self._build_plan(
            task=task,
            summary=task,
            subtasks=[
                SubTask(
                    description=task,
                    role=role,
                    system_prompt=role.system_prompt if role else self._default_system_prompt(),
                    user_prompt=task,
                    estimated_complexity="medium",
                    suggested_files=[],
                    test_command=self._detect_test_command(),
                )
            ],
            total_complexity="medium",
            risks=[],
            estimated_duration="1-2 hours",
        )

    def _is_refactor_task(self, task_lower: str) -> bool:
        return any(k in task_lower for k in ["refactor", "重构", "优化", "optimize", "cleanup", "clean up"])

    def _is_feature_task(self, task_lower: str) -> bool:
        return any(k in task_lower for k in ["add", "implement", "create", "build", "新增", "实现", "添加"])

    def _is_bugfix_task(self, task_lower: str) -> bool:
        return any(k in task_lower for k in ["fix", "bug", "error", "修复", "问题", "异常"])

    def _is_security_task(self, task_lower: str) -> bool:
        return any(k in task_lower for k in ["security", "vulnerability", "audit", "安全", "漏洞"])

    def _is_devops_task(self, task_lower: str) -> bool:
        return any(k in task_lower for k in ["deploy", "docker", "ci", "cd", "pipeline", "workflow", "ci/cd"])

    def _decompose_refactor(self, task: str, context: dict[str, Any]) -> TaskPlan:
        backend_role = next((r for r in self.roles if r.name == "backend-architect"), None)
        qa_role = next((r for r in self.roles if r.name == "qa-engineer"), None)

        target = self._extract_target(task)
        suggested_files = self._find_related_files(target)

        subtasks = [
            SubTask(
                description=f"Analyze current {target} implementation and design refactor plan",
                role=backend_role,
                system_prompt=backend_role.system_prompt if backend_role else self._default_system_prompt(),
                user_prompt=f"Analyze the current implementation of {target} and design a refactor plan. Context: {json.dumps(context, ensure_ascii=False)}",
                estimated_complexity="high",
                suggested_files=suggested_files,
                test_command=self._detect_test_command(),
            ),
            SubTask(
                description=f"Implement refactor of {target}",
                role=backend_role,
                system_prompt=backend_role.system_prompt if backend_role else self._default_system_prompt(),
                user_prompt=f"Implement the refactor for {target} according to the design. Maintain backward compatibility.",
                estimated_complexity="high",
                suggested_files=suggested_files,
                test_command=self._detect_test_command(),
            ),
        ]

        if qa_role:
            subtasks.append(
                SubTask(
                    description="Add/update tests for refactored code",
                    role=qa_role,
                    system_prompt=qa_role.system_prompt,
                    user_prompt=f"Add comprehensive tests for the refactored {target}. Cover edge cases and error paths.",
                    estimated_complexity="medium",
                    suggested_files=[f"tests/unit/test_{target}.py"],
                    test_command=self._detect_test_command(),
                )
            )

        return self._build_plan(
            task=task,
            summary=f"Refactor {target} with analysis, implementation, and tests",
            subtasks=subtasks,
            total_complexity="high",
            risks=["Breaking existing API", "Performance regression", "Test coverage gaps"],
            estimated_duration="3-5 hours",
        )

    def _decompose_feature(self, task: str, context: dict[str, Any]) -> TaskPlan:
        backend_role = next((r for r in self.roles if r.name == "backend-architect"), None)
        qa_role = next((r for r in self.roles if r.name == "qa-engineer"), None)

        subtasks = [
            SubTask(
                description="Design feature API and data model",
                role=backend_role,
                system_prompt=backend_role.system_prompt if backend_role else self._default_system_prompt(),
                user_prompt=f"Design the API and data model for: {task}",
                estimated_complexity="medium",
                suggested_files=[],
                test_command=self._detect_test_command(),
            ),
            SubTask(
                description="Implement feature",
                role=backend_role,
                system_prompt=backend_role.system_prompt if backend_role else self._default_system_prompt(),
                user_prompt=f"Implement the feature: {task}",
                estimated_complexity="high",
                suggested_files=[],
                test_command=self._detect_test_command(),
            ),
        ]

        if qa_role:
            subtasks.append(
                SubTask(
                    description="Add tests for new feature",
                    role=qa_role,
                    system_prompt=qa_role.system_prompt,
                    user_prompt=f"Add tests for the new feature: {task}",
                    estimated_complexity="medium",
                    suggested_files=[],
                    test_command=self._detect_test_command(),
                )
            )

        return self._build_plan(
            task=task,
            summary=f"Implement feature: {task}",
            subtasks=subtasks,
            total_complexity="high",
            risks=["Scope creep", "Integration issues"],
            estimated_duration="2-4 hours",
        )

    def _decompose_bugfix(self, task: str, context: dict[str, Any]) -> TaskPlan:
        qa_role = next((r for r in self.roles if r.name == "qa-engineer"), None)
        backend_role = next((r for r in self.roles if r.name == "backend-architect"), None)

        subtasks = [
            SubTask(
                description="Reproduce and diagnose the bug",
                role=qa_role,
                system_prompt=qa_role.system_prompt if qa_role else self._default_system_prompt(),
                user_prompt=f"Reproduce and diagnose: {task}",
                estimated_complexity="medium",
                suggested_files=[],
                test_command=self._detect_test_command(),
            ),
            SubTask(
                description="Implement bug fix",
                role=backend_role,
                system_prompt=backend_role.system_prompt if backend_role else self._default_system_prompt(),
                user_prompt=f"Fix the bug: {task}",
                estimated_complexity="medium",
                suggested_files=[],
                test_command=self._detect_test_command(),
            ),
        ]

        return self._build_plan(
            task=task,
            summary=f"Fix bug: {task}",
            subtasks=subtasks,
            total_complexity="medium",
            risks=["Incomplete fix", "Side effects"],
            estimated_duration="1-3 hours",
        )

    def _decompose_security(self, task: str, context: dict[str, Any]) -> TaskPlan:
        security_role = next((r for r in self.roles if r.name == "security-engineer"), None)
        backend_role = next((r for r in self.roles if r.name == "backend-architect"), None)

        subtasks = [
            SubTask(
                description="Security audit and threat modeling",
                role=security_role,
                system_prompt=security_role.system_prompt if security_role else self._default_system_prompt(),
                user_prompt=f"Perform security audit for: {task}",
                estimated_complexity="high",
                suggested_files=[],
                test_command=self._detect_test_command(),
            ),
        ]

        if backend_role:
            subtasks.append(
                SubTask(
                    description="Implement security fixes",
                    role=backend_role,
                    system_prompt=backend_role.system_prompt,
                    user_prompt=f"Implement security fixes based on audit: {task}",
                    estimated_complexity="high",
                    suggested_files=[],
                    test_command=self._detect_test_command(),
                )
            )

        return self._build_plan(
            task=task,
            summary=f"Security work: {task}",
            subtasks=subtasks,
            total_complexity="high",
            risks=["False positives", "Performance overhead", "Breaking changes"],
            estimated_duration="2-4 hours",
        )

    def _decompose_devops(self, task: str, context: dict[str, Any]) -> TaskPlan:
        devops_role = next((r for r in self.roles if r.name == "devops-engineer"), None)

        return self._build_plan(
            task=task,
            summary=f"DevOps task: {task}",
            subtasks=[
                SubTask(
                    description=task,
                    role=devops_role,
                    system_prompt=devops_role.system_prompt if devops_role else self._default_system_prompt(),
                    user_prompt=task,
                    estimated_complexity="medium",
                    suggested_files=[],
                    test_command=None,
                )
            ],
            total_complexity="medium",
            risks=["Environment differences", "Secret exposure"],
            estimated_duration="1-2 hours",
        )

    def _build_plan(
        self,
        task: str,
        summary: str,
        subtasks: list[SubTask],
        total_complexity: str,
        risks: list[str],
        estimated_duration: str,
    ) -> TaskPlan:
        return TaskPlan(
            original_task=task,
            summary=summary,
            subtasks=subtasks,
            total_complexity=total_complexity,
            risks=risks,
            estimated_duration=estimated_duration,
            generated_at=datetime.now(timezone.utc),
        )

    def _extract_target(self, task: str) -> str:
        match = re.search(r"(?:refactor|重构|优化)\s+(?:the\s+)?([A-Z][a-zA-Z]+)", task)
        if match:
            return match.group(1)
        words = re.findall(r"[A-Z][a-zA-Z]+", task)
        return words[0] if words else "component"

    def _find_related_files(self, target: str) -> list[str]:
        pattern1 = f"**/*{target.lower()}*.py"
        pattern2 = f"**/*{target}*.py"
        files: list[str] = []
        for pattern in [pattern1, pattern2]:
            files.extend(str(p.relative_to(self.project_root)) for p in self.project_root.glob(pattern))
        return files[:10]

    def _detect_test_command(self) -> str | None:
        if (self.project_root / "pyproject.toml").exists() or (self.project_root / "setup.py").exists():
            return "pytest"
        if (self.project_root / "package.json").exists():
            return "npm test"
        return None

    def _default_system_prompt(self) -> str:
        return "You are an expert software engineer. Produce minimal, correct, well-tested changes."
