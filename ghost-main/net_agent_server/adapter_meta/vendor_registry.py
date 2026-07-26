"""
VendorRegistry — maps brand strings to adapter classes.
=========================================================
Central place to register new router brands. Adding a brand is two steps:
  1. Create the adapter subclass in adapters/
  2. Import + register it below
"""

from adapters.base import BaseRouterAdapter
from adapters.openwrt import OpenWrtAdapter
from adapters.xiaomi import XiaomiAdapter
from adapters.tplink import TPLinkWebAdapter

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
# (decorator-based auto-registration is used inside each adapter file)

# Ensure all adapters run their @register decorator
# (these imports trigger decorator execution)
assert OpenWrtAdapter.vendor == "openwrt"
assert XiaomiAdapter.vendor == "xiaomi"
assert TPLinkWebAdapter.vendor == "tplink"
