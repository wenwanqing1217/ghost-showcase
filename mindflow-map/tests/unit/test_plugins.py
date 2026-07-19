"""Plugin SDK 与 WorkflowEngine 集成测试"""

from __future__ import annotations

import pytest

from mindflow_map.plugins import ToolRegistry, tool, get_global_registry
from mindflow_map.plugins.registry import ToolDefinition
from mindflow_map.workflows.engine import Tool, WorkflowEngine


class _DummyTool(Tool):
    """测试用工具"""

    async def execute(self, params: dict[str, object]) -> dict[str, object]:
        return {"type": "dummy", "params": params}


class _ConflictingTool(Tool):
    """与内置工具同名的测试工具"""

    async def execute(self, params: dict[str, object]) -> dict[str, object]:
        return {"type": "conflicting"}


class TestToolRegistry:
    """ToolRegistry 基础功能"""

    def test_register_and_get(self) -> None:
        registry = ToolRegistry()
        definition = registry.register(_DummyTool, name="custom-tool")

        assert definition.name == "custom-tool"
        assert registry.get("custom-tool") is definition
        assert registry.get("missing") is None

    def test_list_tools_returns_definitions(self) -> None:
        registry = ToolRegistry()
        registry.register(_DummyTool, name="tool-a")
        registry.register(_DummyTool, name="tool-b")

        names = {d.name for d in registry.list_tools()}
        assert names == {"tool-a", "tool-b"}

    def test_create_tool_instantiates_class(self) -> None:
        registry = ToolRegistry()
        registry.register(_DummyTool, name="custom-tool")

        instance = registry.create_tool("custom-tool")
        assert isinstance(instance, _DummyTool)
        assert registry.create_tool("missing") is None

    def test_clear_removes_all_tools(self) -> None:
        registry = ToolRegistry()
        registry.register(_DummyTool, name="tool-a")
        registry.register(_DummyTool, name="tool-b")
        registry.clear()

        assert registry.list_tools() == []
        assert registry.get("tool-a") is None


class TestToolDecorator:
    """@tool 装饰器与全局注册表"""

    def setup_method(self) -> None:
        get_global_registry().clear()

    def test_decorator_registers_tool(self) -> None:
        @tool(name="decorated-tool")
        class DecoratedTool(Tool):
            async def execute(self, params: dict[str, object]) -> dict[str, object]:
                return {}

        registry = get_global_registry()
        definition = registry.get("decorated-tool")
        assert definition is not None
        assert definition.name == "decorated-tool"
        assert definition.tool_cls is DecoratedTool

    def test_decorator_preserves_class(self) -> None:
        @tool(name="decorated-tool")
        class DecoratedTool(Tool):
            async def execute(self, params: dict[str, object]) -> dict[str, object]:
                return {}

        assert issubclass(DecoratedTool, Tool)

    def test_decorator_custom_metadata(self) -> None:
        @tool(name="tagged-tool", description="custom", tags=["a", "b"], version="2.0.0")
        class TaggedTool(Tool):
            async def execute(self, params: dict[str, object]) -> dict[str, object]:
                return {}

        definition = get_global_registry().get("tagged-tool")
        assert definition is not None
        assert definition.description == "custom"
        assert definition.tags == ["a", "b"]
        assert definition.version == "2.0.0"

    def test_decorator_falls_back_to_class_doc(self) -> None:
        @tool()
        class DocTool(Tool):
            """My docstring tool."""

            async def execute(self, params: dict[str, object]) -> dict[str, object]:
                return {}

        definition = get_global_registry().get("DocTool")
        assert definition is not None
        assert definition.description == "My docstring tool."


class TestWorkflowEnginePluginIntegration:
    """WorkflowEngine 与插件 SDK 集成"""

    def setup_method(self) -> None:
        get_global_registry().clear()

    def test_builtin_tools_loaded_by_default(self) -> None:
        engine = WorkflowEngine()
        assert set(engine.tools) == {"map", "douyin", "shopify", "shortdramas"}

    def test_plugin_tools_loaded_from_registry(self) -> None:
        @tool(name="plugin-tool")
        class PluginTool(Tool):
            async def execute(self, params: dict[str, object]) -> dict[str, object]:
                return {}

        engine = WorkflowEngine()
        assert "plugin-tool" in engine.tools
        assert isinstance(engine.tools["plugin-tool"], PluginTool)

    def test_conflicting_plugin_tool_is_skipped(self) -> None:
        @tool(name="map")
        class ConflictingMapTool(Tool):
            async def execute(self, params: dict[str, object]) -> dict[str, object]:
                return {}

        engine = WorkflowEngine()
        assert "map" in engine.tools
        assert not isinstance(engine.tools["map"], ConflictingMapTool)

    def test_register_plugin_tool_dynamically(self) -> None:
        engine = WorkflowEngine()

        class DynamicTool(Tool):
            async def execute(self, params: dict[str, object]) -> dict[str, object]:
                return {}

        engine.register_plugin_tool(DynamicTool, name="dynamic-tool", description="dynamic")
        assert "dynamic-tool" in engine.tools
        assert isinstance(engine.tools["dynamic-tool"], DynamicTool)

    def test_register_plugin_tool_conflict_skipped(self) -> None:
        engine = WorkflowEngine()

        class AnotherMap(Tool):
            async def execute(self, params: dict[str, object]) -> dict[str, object]:
                return {}

        engine.register_plugin_tool(AnotherMap, name="map")
        assert "map" in engine.tools
        assert not isinstance(engine.tools["map"], AnotherMap)
