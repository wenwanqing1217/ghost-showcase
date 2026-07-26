"""
Net-Agent Adapter Layer
=======================
All router brand adapters inherit from BaseRouterAdapter.
To add a new brand: create a subclass + register in vendor_registry.py.
"""

from .base import BaseRouterAdapter
from .openwrt import OpenWrtAdapter
from .xiaomi import XiaomiAdapter
from .tplink import TPLinkWebAdapter

__all__ = [
    "BaseRouterAdapter",
    "OpenWrtAdapter",
    "XiaomiAdapter",
    "TPLinkWebAdapter",
]
