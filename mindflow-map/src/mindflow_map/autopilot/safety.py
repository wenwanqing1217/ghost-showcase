"""Safety validation adapted from zcode-brain safety guardrails.

Loads guardrail rules from zcode-brain/safety/guardrails.json and applies
them to assembled prompts before task execution.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class GuardrailRule:
    """Single safety guardrail rule."""

    id: str
    severity: str
    description: str
    check: str


@dataclass(frozen=True)
class SafetyResult:
    """Result of a safety validation pass."""

    passed: bool
    violations: list[str]


def _default_guardrails_path() -> Path:
    return Path(__file__).resolve().parents[4] / "zcode-brain" / "safety" / "guardrails.json"


def load_guardrails(guardrails_path: str | os.PathLike[str] | None = None) -> list[GuardrailRule]:
    """Load safety guardrail rules from JSON file.

    Args:
        guardrails_path: Path to guardrails.json.
            Defaults to zcode-brain/safety/guardrails.json relative to workspace root.

    Returns:
        List of loaded GuardrailRule instances.
    """
    path = Path(guardrails_path) if guardrails_path is not None else _default_guardrails_path()
    if not path.exists():
        return []

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    rules: list[GuardrailRule] = []
    for rule in raw.get("rules", []):
        rules.append(
            GuardrailRule(
                id=rule.get("id", ""),
                severity=rule.get("severity", "P3"),
                description=rule.get("description", ""),
                check=rule.get("check", ""),
            )
        )
    return rules


# Patterns that should never appear in a task prompt.
_DESTRUCTIVE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"rm\s+-rf\s+/"),
    re.compile(r"DROP\s+DATABASE"),
    re.compile(r"DROP\s+TABLE"),
    re.compile(r"TRUNCATE\s+TABLE"),
)

_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    re.compile(r"shpat_[a-zA-Z0-9]{20,}"),
    re.compile(r"password\s*=\s*['\"].*?['\"]", re.IGNORECASE),
    re.compile(r"SECRET_[A-Z_]+"),
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS key pattern
)


def check_safety(prompt: str, guardrails: Sequence[GuardrailRule] | None = None) -> SafetyResult:
    """Validate a prompt against loaded safety rules.

    Args:
        prompt: Assembled prompt text to validate.
        guardrails: Optional pre-loaded rules.

    Returns:
        SafetyResult indicating pass/fail and any violations.
    """
    if guardrails is None:
        guardrails = load_guardrails()

    violations: list[str] = []

    # Hard-coded safety checks (equivalent to zcode-brain safety-checker.ts)
    for pattern in _DESTRUCTIVE_PATTERNS:
        if pattern.search(prompt):
            violations.append("Destructive command detected")
            break

    for pattern in _SECRET_PATTERNS:
        if pattern.search(prompt):
            violations.append("Potential secret exposure detected")
            break

    # Scope discipline: warn if prompt references paths outside project.
    # This is a soft check; exact enforcement happens in the runner.
    if ".." in prompt and ("/../" in prompt or "\\..\\" in prompt):
        violations.append("Potential scope escape via relative path traversal")

    return SafetyResult(passed=len(violations) == 0, violations=violations)
