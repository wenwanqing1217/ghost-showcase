"""
VendorRegistry — maps brand strings to adapter classes.
=========================================================
Central place to register new router brands. Adding a brand is two steps:
  1. Create the adapter subclass in adapters/
  2. Import + register it below
"""

from net_agent_common.adapters.base import BaseRouterAdapter

# ── registry: vendor string → adapter class ──────────────────
_REGISTRY: dict[str, type[BaseRouterAdapter]] = {}


def register(vendor: str):
    """Class decorator that auto-registers an adapter."""
    def decorator(cls: type[BaseRouterAdapter]):
        cls.vendor = vendor
        _REGISTRY[vendor] = cls
        return cls
    return decorator


def get_adapter(vendor: str) -> type[BaseRouterAdapter]:
    """Look up adapter class by vendor string."""
    if vendor not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY.keys()))
        raise ValueError(f"Unknown vendor '{vendor}'. Available: {available}")
    return _REGISTRY[vendor]


def list_vendors() -> list[str]:
    """Return all registered vendor strings."""
    return sorted(_REGISTRY.keys())


# ── built-in registrations ───────────────────────────────────
# NOTE: adapter imports are placed AFTER register() is defined.
# Each adapter class uses @register(vendor) as a decorator,
# which runs at class-definition time (i.e. during import).
# If we imported them above, Python would try to resolve
# 'register' before it exists → circular import error.

from net_agent_common.adapters.openwrt import OpenWrtAdapter  # noqa: E402
from net_agent_common.adapters.xiaomi import XiaomiAdapter  # noqa: E402
from net_agent_common.adapters.tplink import TPLinkWebAdapter  # noqa: E402

# Verify decorators fired correctly
assert OpenWrtAdapter.vendor == "openwrt"
assert XiaomiAdapter.vendor == "xiaomi"
assert TPLinkWebAdapter.vendor == "tplink"
