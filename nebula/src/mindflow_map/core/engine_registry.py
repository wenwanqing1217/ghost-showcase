"""
工作流引擎注册表 — 单一引用点，消除模块级可变全局变量

H14 修复：将分散在 4 个模块的 `workflow_engine = None` 统一收口到此注册表。
所有消费者通过 `get_workflow_engine()` 获取引擎，不再持有模块级副本。
"""

from typing import Optional
from mindflow_map.workflows.engine import WorkflowEngine

# 单一引擎引用（由 main.py lifespan 注入）
_engine: Optional[WorkflowEngine] = None


def set_engine(engine: WorkflowEngine):
    """注册全局工作流引擎（仅在 lifespan 启动时调用一次）"""
    global _engine
    _engine = engine


def get_workflow_engine() -> WorkflowEngine:
    """获取全局工作流引擎。未初始化时抛出 RuntimeError。"""
    if _engine is None:
        raise RuntimeError(
            "WorkflowEngine 未初始化。"
            "请确保 main.py lifespan 已调用 set_engine()。"
        )
    return _engine


def has_engine() -> bool:
    """检查引擎是否已注册"""
    return _engine is not None
