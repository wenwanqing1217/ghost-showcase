"""Kubernetes secret provider."""
import os
from typing import Optional

from .base import SecretProvider


class KubernetesSecretProvider(SecretProvider):
    SECRETS_DIR = "/run/secrets"

    def __init__(self, secret_name: Optional[str] = None):
        self.secret_name = secret_name

    def _load_from_file(self, key: str) -> Optional[str]:
        if not self.secret_name:
            return None
        secret_path = os.path.join(self.SECRETS_DIR, self.secret_name, key)
        try:
            with open(secret_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except (FileNotFoundError, PermissionError, OSError):
            return None

    def get(self, name: str, default: str | None = None) -> str | None:
        value = self._load_from_file(name)
        if value is not None:
            return value
        return os.getenv(name, default)
