"""Autopilot system leveraging zcode-brain agent architecture.

This module provides an autonomous task execution framework that:
1. Reads zcode-brain role definitions and safety guardrails
2. Matches tasks to expert roles
3. Assembles validated prompts
4. Executes tasks with proper guardrails
5. Runs tests and commits changes
"""

from .roles import load_roles, match_role
from .safety import load_guardrails, check_safety
from .prompt import assemble_prompt
from .runner import TaskRunner

__all__ = [
    "load_roles",
    "match_role",
    "load_guardrails",
    "check_safety",
    "assemble_prompt",
    "TaskRunner",
]
