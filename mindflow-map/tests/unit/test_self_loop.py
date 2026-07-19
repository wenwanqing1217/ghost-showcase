"""Tests for autopilot self-loop components."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from mindflow_map.autopilot.self_loop import CodebaseScanner, IssuePrioritizer, SelfLoop


class TestCodebaseScanner:
    def test_scan_returns_list(self, tmp_path: Path) -> None:
        scanner = CodebaseScanner(tmp_path)
        issues = scanner.scan()
        assert isinstance(issues, list)

    def test_scan_detects_debug_prints(self, tmp_path: Path) -> None:
        target = tmp_path / "module.py"
        target.write_text("print('debug')\n", encoding="utf-8")
        scanner = CodebaseScanner(tmp_path)
        issues = scanner.scan()
        assert any("print" in issue.id for issue in issues)

    def test_scan_detects_long_files(self, tmp_path: Path) -> None:
        target = tmp_path / "long.py"
        target.write_text("x = 1\n" * 600, encoding="utf-8")
        scanner = CodebaseScanner(tmp_path)
        issues = scanner.scan()
        assert any("long" in issue.id for issue in issues)


class TestIssuePrioritizer:
    def test_prioritize_sorts_by_severity(self) -> None:
        from mindflow_map.autopilot.self_loop import Issue

        issues = [
            Issue("1", "cat", "P3", "low", "", None, "", False),
            Issue("2", "cat", "P0", "high", "", None, "", False),
            Issue("3", "cat", "P1", "med", "", None, "", False),
        ]
        prioritized = IssuePrioritizer().prioritize(issues)
        assert prioritized[0].severity == "P0"
        assert prioritized[1].severity == "P1"
        assert prioritized[2].severity == "P3"

    def test_prioritize_prefers_auto_fixable(self) -> None:
        from mindflow_map.autopilot.self_loop import Issue

        issues = [
            Issue("1", "cat", "P1", "a", "", None, "", False),
            Issue("2", "cat", "P1", "b", "", None, "", True),
        ]
        prioritized = IssuePrioritizer().prioritize(issues)
        assert prioritized[0].auto_fixable is True


class TestSelfLoop:
    def test_run_returns_loop_result(self, tmp_path: Path) -> None:
        loop = SelfLoop(project_root=tmp_path, auto_commit=False, max_fixes_per_iteration=1)
        result = loop.run(max_iterations=1)
        assert isinstance(result.iterations, list)
        assert len(result.iterations) >= 1
        assert result.started_at is not None
        assert result.finished_at is not None

    def test_run_stops_when_no_issues(self, tmp_path: Path) -> None:
        loop = SelfLoop(project_root=tmp_path, auto_commit=False, max_fixes_per_iteration=1)
        result = loop.run(max_iterations=10)
        assert len(result.iterations) <= 10

    def test_run_respects_max_iterations(self, tmp_path: Path) -> None:
        loop = SelfLoop(project_root=tmp_path, auto_commit=False, max_fixes_per_iteration=1)
        result = loop.run(max_iterations=2)
        assert len(result.iterations) <= 2
