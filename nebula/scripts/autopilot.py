"""Autopilot CLI for autonomous task execution.

Usage:
    python -m mindflow_map.autopilot "refactor WorkflowEngine"
    python scripts/autopilot.py "add rate limiting to wechat API"
    python scripts/autopilot.py --dry-run "fix memory leak in douyin automation"

The CLI uses zcode-brain's expert role definitions and safety guardrails
to execute tasks with proper validation, testing, and commit workflows.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow running as a script from the repository root without installation.
_HERE = Path(__file__).resolve()
_ROOT = _HERE.parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from mindflow_map.autopilot.runner import TaskRunner


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="autopilot",
        description="Autonomous task execution using zcode-brain agent architecture.",
    )
    parser.add_argument("task", help="Natural language task description to execute")
    parser.add_argument(
        "--project-root",
        default=None,
        help="Path to project root. Defaults to auto-detected mindflow-map directory.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan the task without executing or committing changes",
    )
    parser.add_argument(
        "--auto-commit",
        action="store_true",
        help="Automatically commit changes after task execution",
    )
    parser.add_argument(
        "--run-tests",
        action="store_true",
        default=True,
        help="Run tests after task execution (default: True)",
    )
    parser.add_argument(
        "--no-tests",
        action="store_true",
        help="Skip test execution",
    )
    parser.add_argument(
        "--context",
        default=None,
        help="Optional JSON context string to include in the prompt",
    )
    parser.add_argument(
        "--self-loop",
        action="store_true",
        help="Run autonomous self-improvement loop (scan, fix, test, commit)",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=5,
        help="Maximum iterations for self-loop (default: 5)",
    )
    parser.add_argument(
        "--max-fixes",
        type=int,
        default=3,
        help="Maximum fixes per iteration (default: 3)",
    )
    return parser


def _auto_detect_project_root() -> Path:
    """Auto-detect the project root by looking for pyproject.toml or setup.py."""
    current = Path.cwd().resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "pyproject.toml").exists() or (candidate / "setup.py").exists():
            return candidate
    return current


def _parse_context(raw: str | None) -> dict[str, object] | None:
    if not raw:
        return None
    import json

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"[autopilot] Invalid JSON context: {exc}")
        return None


def _print_banner(task: str) -> None:
    print("=" * 72)
    print("  MindFlow Autopilot")
    print("  Powered by zcode-brain agent architecture")
    print("=" * 72)
    print(f"  Task : {task}")
    print(f"  Time : {datetime.now(timezone.utc).isoformat()}")
    print("=" * 72)
    print()


def _print_context(execution_context) -> None:
    print("[autopilot] Role matching")
    print(f"  matched role : {execution_context.role_name or 'general engineer'}")
    print(f"  allowed      : {execution_context.allowed}")
    if execution_context.violations:
        print(f"  violations   : {', '.join(execution_context.violations)}")
    print()
    print("[autopilot] Prompt")
    print(f"  system: {execution_context.system_prompt[:120]}...")
    print(f"  user  : {execution_context.user_prompt[:120]}...")
    print()
    if execution_context.safety_notes:
        print("[autopilot] Safety notes")
        for note in execution_context.safety_notes:
            print(f"  - {note}")
        print()


def _print_test_result(passed: bool, output: str) -> None:
    status = "passed" if passed else "failed"
    print(f"[autopilot] Tests {status}")
    if output:
        for line in output.splitlines()[:50]:
            print(f"  {line}")


def _print_commit_result(sha: str | None) -> None:
    if sha:
        print(f"[autopilot] Committed: {sha}")
    else:
        print("[autopilot] Commit skipped or failed")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    project_root = (
        Path(args.project_root).resolve()
        if args.project_root is not None
        else _auto_detect_project_root()
    )

    runner = TaskRunner(project_root=project_root, auto_commit=args.auto_commit)

    context = _parse_context(args.context)

    _print_banner(args.task)

    # Planning phase
    task_context = runner.plan(args.task, context=context)
    _print_context(task_context)

    if not task_context.allowed:
        print("[autopilot] Blocked: task failed safety validation")
        return 2

    if args.self_loop:
        print("[autopilot] Starting self-loop mode")
        print(f"  max iterations : {args.max_iterations}")
        print(f"  max fixes/iter : {args.max_fixes}")
        print()

        from mindflow_map.autopilot.self_loop import SelfLoop

        loop = SelfLoop(
            project_root=project_root,
            auto_commit=args.auto_commit,
            max_fixes_per_iteration=args.max_fixes,
        )
        result = loop.run(max_iterations=args.max_iterations)

        print()
        print("[autopilot] Self-loop complete")
        print(f"  iterations     : {len(result.iterations)}")
        print(f"  issues found   : {result.total_issues_found}")
        print(f"  issues fixed   : {result.total_issues_fixed}")
        print(f"  issues skipped : {result.total_issues_skipped}")
        print(f"  success        : {result.success}")

        for it in result.iterations:
            status = "passed" if it.tests_passed else "failed"
            print(f"    iter {it.iteration}: {it.issues_fixed} fixed, tests {status}")
            if it.errors:
                for err in it.errors:
                    print(f"      error: {err}")

        return 0 if result.success else 1

    if args.dry_run:
        print("[autopilot] Dry run complete. No changes made.")
        return 0

    # Execution phase
    print("[autopilot] Executing task...")
    print("  Note: actual code changes should be applied by the AI operator")
    print("        using the assembled prompt above.")
    print()

    # Run tests unless explicitly skipped
    if not args.no_tests and args.run_tests:
        print("[autopilot] Running tests...")
        passed, output = runner.run_tests()
        _print_test_result(passed, output)
        print()
    else:
        print("[autopilot] Tests skipped")
        print()

    # Commit if requested
    if args.auto_commit:
        print("[autopilot] Committing changes...")
        sha = runner.commit(f"autopilot: {args.task}")
        _print_commit_result(sha)
        print()

    print("[autopilot] Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
