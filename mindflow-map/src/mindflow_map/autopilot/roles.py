"""Role matching engine adapted from zcode-brain dispatcher.

Reads expert role definitions from zcode-brain/roles/*.json and matches
incoming task descriptions to the most appropriate expert role.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Role:
    """Expert role definition mirrored from zcode-brain."""

    name: str
    display_name: str
    department: str
    system_prompt: str
    strengths: list[str]
    tools: list[str]
    dispatch_triggers: list[str]


def _default_roles_dir() -> Path:
    """Resolve zcode-brain roles directory relative to workspace root."""
    return Path(__file__).resolve().parents[4] / "zcode-brain" / "roles"


def load_roles(roles_dir: str | os.PathLike[str] | None = None) -> list[Role]:
    """Load all expert role definitions from JSON files.

    Args:
        roles_dir: Directory containing role JSON files.
            Defaults to zcode-brain/roles/ relative to workspace root.

    Returns:
        List of loaded Role instances.
    """
    roles_path = Path(roles_dir) if roles_dir is not None else _default_roles_dir()
    roles: list[Role] = []

    if not roles_path.exists():
        return roles

    for path in sorted(roles_path.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            roles.append(
                Role(
                    name=raw["name"],
                    display_name=raw["displayName"],
                    department=raw["department"],
                    system_prompt=raw["systemPrompt"],
                    strengths=list(raw.get("strengths", [])),
                    tools=list(raw.get("tools", [])),
                    dispatch_triggers=list(raw.get("dispatchTriggers", [])),
                )
            )
        except (json.JSONDecodeError, KeyError):
            continue

    return roles


def match_role(task_description: str, roles: Iterable[Role] | None = None) -> Role | None:
    """Match a task description to the best expert role.

    Uses keyword scoring identical to zcode-brain's role-matcher.ts.

    Args:
        task_description: Natural language task description.
        roles: Optional pre-loaded roles. If omitted, roles are loaded from disk.

    Returns:
        Best matching Role, or None if no trigger keywords match.
    """
    if roles is None:
        roles = load_roles()

    lower_task = task_description.lower()
    best_match: Role | None = None
    best_score = 0

    for role in roles:
        score = sum(1 for trigger in role.dispatch_triggers if trigger in lower_task)
        if score > 0 and score > best_score:
            best_score = score
            best_match = role

    return best_match
