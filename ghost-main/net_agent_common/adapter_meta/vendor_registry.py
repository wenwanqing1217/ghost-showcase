"""
VendorRegistry — maps brand strings to adapter classes.
=========================================================
Central place to register new router brands. Adding a brand is two steps:
  1. Create the adapter subclass in adapters/
  2. Register it in the _BUILTIN_VENDOR_MODULES map below
"""

import importlib

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


# 内置厂商 → 适配器模块映射。适配器模块仅在首次 get_adapter() 查找时惰性导入，
# 从而避免 vendor_registry ↔ adapters/* 之间的模块级循环导入。
_BUILTIN_VENDOR_MODULES: dict[str, str] = {
    "openwrt": "net_agent_common.adapters.openwrt",
    "tplink": "net_agent_common.adapters.tplink",
    "xiaomi": "net_agent_common.adapters.xiaomi",
}


def list_vendors() -> list[str]:
    """Return all registered vendor strings (lazily importing built-in adapters)."""
    for vendor in _BUILTIN_VENDOR_MODULES:
        if vendor not in _REGISTRY:
            importlib.import_module(_BUILTIN_VENDOR_MODULES[vendor])
    return sorted(_REGISTRY.keys())


def get_adapter(vendor: str) -> type[BaseRouterAdapter]:
    """Look up adapter class by vendor string (lazily imports built-in adapters)."""
    if vendor not in _REGISTRY:
        module_name = _BUILTIN_VENDOR_MODULES.get(vendor)
        if module_name:
            # 导入会触发适配器类上的 @register(vendor) 装饰器
            importlib.import_module(module_name)
    if vendor not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY.keys()))
        raise ValueError(f"Unknown vendor '{vendor}'. Available: {available}")
    return _REGISTRY[vendor]
