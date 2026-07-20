"""MindFlow Map 插件模板。"""

from __future__ import annotations

import logging
from typing import Any

from mindflow_map.plugins.registry import tool

logger = logging.getLogger(__name__)


@tool(name="my_custom_tool", description="我的自定义工具描述")
async def my_custom_tool(param: str, **kwargs: Any) -> dict:
    """
    自定义工具实现。

    Args:
        param: 参数描述
        **kwargs: 其他可选参数

    Returns:
        工具执行结果字典
    """
    logger.info("Executing my_custom_tool with param=%s", param)
    # 在这里实现你的工具逻辑
    result = {
        "success": True,
        "data": {
            "param": param,
            "result": "工具执行结果",
        },
    }
    return result


# 工具清单
PLUGIN_TOOLS = [
    my_custom_tool,
]
