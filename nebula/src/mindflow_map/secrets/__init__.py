"""Secret provider for MindFlow Map."""

import os


class EnvSecretProvider:
    """Simple environment variable secret provider."""

    def get(self, name: str, default: str = "") -> str:
        """Get a secret value from environment variables."""
        value = os.environ.get(name, default)
        return value if value is not None else default


def get_secret_provider():
    """Return the secret provider instance."""
    return EnvSecretProvider()
