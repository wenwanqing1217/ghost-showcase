"""
Net-Agent Adapter Layer
=======================
All router brand adapters inherit from BaseRouterAdapter.
To add a new brand: create a subclass + register in vendor_registry.py.

NOTE: Subclass imports are intentionally deferred. Importing them here
would create a circular dependency at module load time:

    adapters/__init__ → adapters.openwrt → adapter_meta.vendor_registry
                         (needs @register)      (still loading)

Import adapters directly by path when needed:
    from net_agent_common.adapters.openwrt import OpenWrtAdapter
"""

from .base import BaseRouterAdapter

__all__ = [
    "BaseRouterAdapter",
]
