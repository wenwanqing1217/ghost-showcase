"""本地开发启动脚本（Windows）。"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from mindflow_map.config import settings
from mindflow_map.config_validator import check_all
from mindflow_map.main import app
from mindflow_map.models.session import init_db, close_db
from mindflow_map.workflows.engine import WorkflowEngine

logger = logging.getLogger(__name__)


async def main() -> None:
    """本地开发启动流程。"""
    logging.basicConfig(level=logging.INFO)
    logger.info("🚀 启动 MindFlow Map 开发环境...")

    # 校验配置
    status = check_all()
    for platform, info in status.items():
        if not info["configured"]:
            logger.warning("⚠️  平台配置缺失 [%s]: %s", platform, info["message"])
        else:
            logger.info("✅ 平台配置就绪 [%s]", platform)

    # 初始化数据库
    await init_db()
    logger.info("✅ 数据库初始化完成")

    # 启动工作流引擎
    engine = WorkflowEngine()
    logger.info("✅ 工作流引擎初始化完成")

    logger.info("=" * 60)
    logger.info("📋 服务信息：")
    logger.info("  - API 文档: http://localhost:8000/docs")
    logger.info("  - ReDoc:    http://localhost:8000/redoc")
    logger.info("  - Metrics:  http://localhost:8000/metrics")
    logger.info("  - Editor:   http://localhost:8000/editor")
    logger.info("=" * 60)
    logger.info("💡 提示：运行 'make dev' 启动开发服务器")

    # 清理
    await close_db()
    await engine.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
