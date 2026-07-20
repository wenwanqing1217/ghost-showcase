"""HashiCorp Vault secret provider (placeholder)."""
from .base import SecretProvider


class VaultSecretProvider(SecretProvider):
    def __init__(self, url: str, token: str, path_prefix: str = "secret/mindflow-map"):
        self.url = url
        self.token = token
        self.path_prefix = path_prefix
        self._cache: dict[str, str] = {}

    def get(self, name: str, default: str | None = None) -> str | None:
        full_path = f"{self.path_prefix}/{name}"
        return self._cache.get(full_path, default)
