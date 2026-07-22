"""Environment variable secret provider."""
import os

from .base import SecretProvider


class EnvSecretProvider(SecretProvider):
    def get(self, name: str, default: str | None = None) -> str | None:
        return os.getenv(name, default)
