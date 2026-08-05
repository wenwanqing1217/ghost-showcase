"""Plugin SDK for mindflow-map.

Provides decorator-based tool registration and discovery.
"""

from mindflow_map.plugins.registry import ToolRegistry, get_global_registry, tool

__all__ = ["ToolRegistry", "get_global_registry", "tool"]
