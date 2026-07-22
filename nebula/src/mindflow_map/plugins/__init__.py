"""Plugin SDK for mindflow-map.

Provides decorator-based tool registration and discovery.
"""

from mindflow_map.plugins.registry import ToolRegistry, tool, get_global_registry

__all__ = ["ToolRegistry", "tool", "get_global_registry"]
