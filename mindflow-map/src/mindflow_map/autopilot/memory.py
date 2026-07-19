"""Memory system for the autopilot system.

Provides persistent memory across tasks, allowing the system to learn
from past executions and improve over time.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class MemoryEntry:
    """A single memory entry."""

    id: str
    task: str
    context: dict[str, Any]
    result: dict[str, Any]
    success: bool
    timestamp: datetime
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class MemoryStore:
    """Persistent memory store for autopilot experiences."""

    def __init__(self, storage_path: str | os.PathLike[str] | None = None) -> None:
        self.storage_path = Path(storage_path) if storage_path is not None else Path("memory/autopilot.json")
        self._entries: list[MemoryEntry] = []
        self._load()

    def _load(self) -> None:
        if self.storage_path.exists():
            try:
                raw = json.loads(self.storage_path.read_text(encoding="utf-8"))
                for entry in raw:
                    self._entries.append(
                        MemoryEntry(
                            id=entry["id"],
                            task=entry["task"],
                            context=entry.get("context", {}),
                            result=entry.get("result", {}),
                            success=entry.get("success", False),
                            timestamp=datetime.fromisoformat(entry["timestamp"]),
                            tags=list(entry.get("tags", [])),
                            metadata=dict(entry.get("metadata", {})),
                        )
                    )
            except (json.JSONDecodeError, KeyError, OSError):
                self._entries = []

    def _save(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        raw = []
        for entry in self._entries:
            raw.append(
                {
                    "id": entry.id,
                    "task": entry.task,
                    "context": entry.context,
                    "result": entry.result,
                    "success": entry.success,
                    "timestamp": entry.timestamp.isoformat(),
                    "tags": entry.tags,
                    "metadata": entry.metadata,
                }
            )
        self.storage_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")

    def store(self, entry: MemoryEntry) -> None:
        """Store a memory entry."""
        self._entries.append(entry)
        self._save()

    def query(self, task: str, limit: int = 5) -> list[MemoryEntry]:
        """Query memory for similar past tasks."""
        task_lower = task.lower()
        scored = []
        for entry in self._entries:
            score = sum(1 for word in task_lower.split() if word in entry.task.lower())
            if score > 0:
                scored.append((score, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored[:limit]]

    def get_recent(self, limit: int = 10) -> list[MemoryEntry]:
        """Get recent memory entries."""
        return sorted(self._entries, key=lambda e: e.timestamp, reverse=True)[:limit]

    def get_success_rate(self, tag: str | None = None) -> float:
        """Calculate success rate for tasks."""
        entries = self._entries
        if tag:
            entries = [e for e in entries if tag in e.tags]
        if not entries:
            return 0.0
        return sum(1 for e in entries if e.success) / len(entries)


class LearningEngine:
    """Learn from past executions to improve future performance."""

    def __init__(self, memory: MemoryStore) -> None:
        self.memory = memory

    def suggest_improvements(self, task: str) -> list[str]:
        """Suggest improvements based on past similar tasks."""
        similar = self.memory.query(task, limit=5)
        suggestions: list[str] = []
        for entry in similar:
            if not entry.success:
                suggestions.append(f"Past similar task failed: {entry.task}. Consider: {entry.result.get('error', 'unknown error')}")
            else:
                if entry.result.get("duration"):
                    suggestions.append(f"Past success: {entry.task} took {entry.result['duration']}")
        return suggestions

    def recommend_role(self, task: str) -> str | None:
        """Recommend an expert role based on past success."""
        similar = self.memory.query(task, limit=10)
        role_success: dict[str, tuple[int, int]] = {}
        for entry in similar:
            role = entry.metadata.get("role", "unknown")
            if role not in role_success:
                role_success[role] = (0, 0)
            successes, total = role_success[role]
            role_success[role] = (successes + (1 if entry.success else 0), total + 1)
        best_role = max(role_success.items(), key=lambda x: x[1][0] / max(x[1][1], 1), default=None)
        if best_role and best_role[1][1] >= 2:
            return best_role[0]
        return None
