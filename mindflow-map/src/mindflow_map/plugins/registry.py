"""Tool registry and plugin SDK for mindflow-map.

Provides a decorator-based plugin system for registering new workflow tools
without modifying the core engine code.

Example:
    @tool(name="my-tool", description="Does something")
    class MyTool(Tool):
        async def execute(self, context: ToolContext) -> ToolResult:
            ...
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Type

from mindflow_map.workflows.engine import Tool


@dataclass
class ToolDefinition:
    """Metadata for a registered tool."""
    name: str
    description: str
    tool_cls: Type[Tool]
    tags: List[str] = field(default_factory=list)
    version: str = "1.0.0"


class ToolRegistry:
    """Central registry for workflow tools.

    Tools can be registered explicitly or discovered via the @tool decorator.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDefinition] = {}

    def register(
        self,
        tool_cls: Type[Tool],
        name: str | None = None,
        description: str | None = None,
        tags: List[str] | None = None,
        version: str = "1.0.0",
    ) -> ToolDefinition:
        """Register a tool class.

        Args:
            tool_cls: Tool implementation class.
            name: Optional override for tool name.
            description: Optional override for tool description.
            tags: Optional tags for grouping/filtering.
            version: Tool version string.

        Returns:
            The created ToolDefinition.
        """
        resolved_name = name or getattr(tool_cls, "name", tool_cls.__name__)
        resolved_description = description or inspect.getdoc(tool_cls) or ""
        definition = ToolDefinition(
            name=resolved_name,
            description=resolved_description,
            tool_cls=tool_cls,
            tags=tags or [],
            version=version,
        )
        self._tools[resolved_name] = definition
        return definition

    def get(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool definition by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[ToolDefinition]:
        """List all registered tools."""
        return list(self._tools.values())

    def create_tool(self, name: str, **kwargs: Any) -> Optional[Tool]:
        """Instantiate a registered tool by name."""
        definition = self._tools.get(name)
        if definition is None:
            return None
        return definition.tool_cls(**kwargs)

    def clear(self) -> None:
        """Remove all registered tools."""
        self._tools.clear()


def tool(
    name: str | None = None,
    description: str | None = None,
    tags: List[str] | None = None,
    version: str = "1.0.0",
) -> Callable[[Type[Tool]], Type[Tool]]:
    """Decorator to register a Tool subclass in the global registry.

    Args:
        name: Optional tool name override.
        description: Optional description override.
        tags: Optional tags for grouping.
        version: Tool version string.

    Returns:
        Decorator function that registers the tool and returns the class unchanged.
    """
    def decorator(tool_cls: Type[Tool]) -> Type[Tool]:
        registry = getattr(tool_cls, "_registry", None) or _global_registry
        registry.register(
            tool_cls=tool_cls,
            name=name,
            description=description,
            tags=tags,
            version=version,
        )
        return tool_cls
    return decorator


# Global registry instance
_global_registry = ToolRegistry()


def get_global_registry() -> ToolRegistry:
    """Return the global tool registry."""
    return _global_registry
