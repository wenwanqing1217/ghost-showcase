"""Base secret provider abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod


class SecretProvider(ABC):
    """Abstract base for secret backends."""

    @abstractmethod
    def get(self, name: str, default: str | None = None) -> str | None:
        """Return secret value or default."""
        raise NotImplementedError
