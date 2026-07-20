# 插件开发指南

本文档说明如何为 MindFlow Map 开发自定义插件。

## 插件架构

MindFlow Map 使用装饰器模式注册工具，插件本质是一组 `@tool` 装饰的函数。

## 快速开始

1. 复制 `src/mindflow_map/plugins/my_custom_tool.py` 作为模板
2. 实现你的工具函数
3. 在 `PLUGIN_TOOLS` 列表中声明工具
4. 提交 Pull Request

## 工具签名

```python
@tool(name="tool_name", description="工具描述")
async def tool_name(param: str, **kwargs: Any) -> dict:
    """
    工具实现。

    Args:
        param: 参数描述
        **kwargs: 其他可选参数

    Returns:
        包含 success 和 data 的字典
    """
    return {
        "success": True,
        "data": {...},
    }
```

## 最佳实践

- 工具名使用 snake_case
- 返回值必须包含 `success` 字段
- 异常时返回 `{"success": False, "error": "错误信息"}`
- 使用 `logger` 记录关键操作
- 避免阻塞调用，使用 `async/await`

## 测试

```bash
python -m pytest tests/ -k plugin -v
```
