"""Factory function for secret providers."""

from __future__ import annotations

import os

from .base import SecretProvider
from .env import EnvSecretProvider
from .kubernetes import KubernetesSecretProvider
from .vault import VaultSecretProvider


def get_secret_provider() -> SecretProvider:
    """Return secret provider based on SECRET_PROVIDER env var."""
    provider_type = os.getenv("SECRET_PROVIDER", "env").lower()

    if provider_type == "vault":
        vault_url = os.getenv("VAULT_URL", "http://localhost:8200")
        vault_token = os.getenv("VAULT_TOKEN", "")
        path_prefix = os.getenv("VAULT_PATH_PREFIX", "secret/mindflow-map")
        return VaultSecretProvider(url=vault_url, token=vault_token, path_prefix=path_prefix)

    if provider_type == "kubernetes":
        secret_name = os.getenv("K8S_SECRET_NAME", "mindflow-map-secrets")
        return KubernetesSecretProvider(secret_name=secret_name)

    return EnvSecretProvider()

