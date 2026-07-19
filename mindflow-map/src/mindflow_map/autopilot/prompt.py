"""Prompt assembly adapted from zcode-brain dispatcher.

Combines role system prompts, task context, and safety requirements into
a single validated prompt ready for execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .roles import Role, match_role
from .safety import check_safety, load_guardrails


@dataclass(frozen=True)
class AssembledPrompt:
    """Fully assembled prompt with role and safety context."""

    role: Role | None
    system_prompt: str
    user_prompt: str
    safety_notes: list[str]
    violations: list[str]
    allowed: bool


def assemble_prompt(
    task_description: str,
    context: dict[str, Any] | None = None,
    roles: list[Role] | None = None,
) -> AssembledPrompt:
    """Assemble a validated prompt for task execution.

    Args:
        task_description: The raw task description from the user.
        context: Optional additional context (file paths, error output, etc.).
        roles: Optional pre-loaded roles for matching.

    Returns:
        AssembledPrompt containing role, prompts, safety notes, and validation result.
    """
    matched_role = match_role(task_description, roles=roles)

    if matched_role:
        system_prompt = matched_role.system_prompt
    else:
        system_prompt = (
            "You are a helpful expert software engineer. "
            "Analyze the task carefully and produce minimal, correct changes."
        )

    context_block = ""
    if context:
        context_block = f"\n\nContext:\n{_format_context(context)}\n"

    # Load safety notes from guardrails descriptions.
    guardrails = load_guardrails()
    safety_notes = [rule.description for rule in guardrails]
    safety_block = ""
    if safety_notes:
        safety_block = "\n\nSafety requirements:\n" + "\n".join(
            f"{i + 1}. {note}" for i, note in enumerate(safety_notes)
        ) + "\n"

    user_prompt = f"{task_description}{context_block}{safety_block}"

    safety_result = check_safety(user_prompt, guardrails=guardrails)

    return AssembledPrompt(
        role=matched_role,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        safety_notes=safety_notes,
        violations=safety_result.violations,
        allowed=safety_result.passed,
    )


def _format_context(context: dict[str, Any]) -> str:
    """Format context dict into a readable block."""
    lines: list[str] = []
    for key, value in context.items():
        if isinstance(value, (list, dict)):
            lines.append(f"{key}:\n{_serialize_value(value)}")
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines)


def _serialize_value(value: Any, indent: int = 2) -> str:
    """Serialize a value to a readable string."""
    if isinstance(value, str):
        return value
    try:
        import json

        return json.dumps(value, ensure_ascii=False, indent=indent)
    except TypeError:
        return str(value)
