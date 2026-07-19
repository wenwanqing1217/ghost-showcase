"""Tests for the autopilot package."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mindflow_map.autopilot.prompt import assemble_prompt
from mindflow_map.autopilot.roles import Role, load_roles, match_role
from mindflow_map.autopilot.safety import (
    GuardrailRule,
    SafetyResult,
    check_safety,
    load_guardrails,
)


class TestRoleLoading:
    def test_load_roles_returns_list(self) -> None:
        roles = load_roles()
        assert isinstance(roles, list)

    def test_load_roles_contains_expected_roles(self) -> None:
        roles = load_roles()
        names = {role.name for role in roles}
        expected = {"backend-architect", "devops-engineer", "qa-engineer", "security-engineer"}
        assert expected.issubset(names)

    def test_role_dataclass_fields(self) -> None:
        roles = load_roles()
        for role in roles:
            assert role.name
            assert role.display_name
            assert role.system_prompt
            assert isinstance(role.dispatch_triggers, list)


class TestRoleMatching:
    def setup_method(self) -> None:
        self.roles = load_roles()

    def test_match_backend_task(self) -> None:
        role = match_role("refactor the WorkflowEngine backend", roles=self.roles)
        assert role is not None
        assert role.name == "backend-architect"

    def test_match_devops_task(self) -> None:
        role = match_role("create a CI/CD workflow with docker", roles=self.roles)
        assert role is not None
        assert role.name == "devops-engineer"

    def test_match_qa_task(self) -> None:
        role = match_role("fix failing tests and add coverage", roles=self.roles)
        assert role is not None
        assert role.name == "qa-engineer"

    def test_match_security_task(self) -> None:
        role = match_role("security audit and vulnerability scan", roles=self.roles)
        assert role is not None
        assert role.name == "security-engineer"

    def test_no_match_returns_none(self) -> None:
        role = match_role("make the logo sparkle", roles=self.roles)
        assert role is None

    def test_empty_task_returns_none(self) -> None:
        role = match_role("", roles=self.roles)
        assert role is None


class TestSafety:
    def test_load_guardrails_returns_list(self) -> None:
        rules = load_guardrails()
        assert isinstance(rules, list)

    def test_guardrails_contain_no_destructive_commands(self) -> None:
        rules = load_guardrails()
        ids = {rule.id for rule in rules}
        assert "no-destructive-commands" in ids

    def test_check_safety_passes_for_normal_prompt(self) -> None:
        result = check_safety("Refactor the workflow engine for better maintainability.")
        assert result.passed is True
        assert result.violations == []

    def test_check_safety_blocks_destructive_command(self) -> None:
        result = check_safety("Run rm -rf / to clean the server")
        assert result.passed is False
        assert any("Destructive" in v for v in result.violations)

    def test_check_safety_blocks_secret_patterns(self) -> None:
        result = check_safety("Use API key sk-0123456789abcdefghijklmnop for testing")
        assert result.passed is False
        assert any("secret" in v.lower() for v in result.violations)

    def test_check_safety_blocks_drop_database(self) -> None:
        result = check_safety("Execute DROP DATABASE production;")
        assert result.passed is False


class TestPromptAssembly:
    def test_assemble_prompt_returns_assembled_prompt(self) -> None:
        assembled = assemble_prompt("Refactor the workflow engine")
        assert assembled.role is not None
        assert assembled.system_prompt
        assert "Refactor the workflow engine" in assembled.user_prompt
        assert assembled.allowed is True

    def test_assemble_prompt_matches_backend_role(self) -> None:
        assembled = assemble_prompt("design a new api route")
        assert assembled.role is not None
        assert assembled.role.name == "backend-architect"

    def test_assemble_prompt_rejects_unsafe_task(self) -> None:
        assembled = assemble_prompt("run rm -rf / to clean everything")
        assert assembled.allowed is False
        assert assembled.violations

    def test_assemble_prompt_includes_safety_notes(self) -> None:
        assembled = assemble_prompt("add input validation")
        assert isinstance(assembled.safety_notes, list)
        assert len(assembled.safety_notes) > 0

    def test_assemble_prompt_with_context(self) -> None:
        assembled = assemble_prompt("fix the bug", context={"file": "engine.py", "error": "null pointer"})
        assert "engine.py" in assembled.user_prompt
        assert "null pointer" in assembled.user_prompt


class TestTaskRunner:
    def test_plan_returns_task_context(self, tmp_path: Path) -> None:
        from mindflow_map.autopilot.runner import TaskRunner

        runner = TaskRunner(project_root=tmp_path)
        ctx = runner.plan("refactor backend api engine")
        assert ctx.task == "refactor backend api engine"
        assert ctx.role_name == "Backend Architect"
        assert ctx.allowed is True
        assert ctx.finished_at is None

    def test_run_updates_finished_at(self, tmp_path: Path) -> None:
        from mindflow_map.autopilot.runner import TaskRunner

        runner = TaskRunner(project_root=tmp_path)
        ctx = runner.run("add unit tests")
        assert ctx.finished_at is not None

    def test_check_path_within_project(self, tmp_path: Path) -> None:
        from mindflow_map.autopilot.runner import TaskRunner

        runner = TaskRunner(project_root=tmp_path)
        target = runner.check_path("src/mindflow_map/workflows/engine.py")
        assert target.is_relative_to(tmp_path)

    def test_check_path_escapes_project(self, tmp_path: Path) -> None:
        from mindflow_map.autopilot.runner import TaskRunner

        runner = TaskRunner(project_root=tmp_path)
        with pytest.raises(ValueError):
            runner.check_path("../../etc/passwd")
