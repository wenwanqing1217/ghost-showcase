"""FastAPI 主入口 - MindFlow Map 后端服务"""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from mindflow_map.config import settings
from mindflow_map.config_validator import check_all
from mindflow_map.api import automation, autopilot, health, map, shortdramas, wechat, workflow
from mindflow_map.workflows.engine import WorkflowEngine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时校验平台配置
    status = check_all()
    for platform, info in status.items():
        if not info["configured"]:
            logger.warning(
                "平台配置缺失 [%s]: %s",
                platform,
                info["message"],
            )
        else:
            logger.info("平台配置就绪 [%s]", platform)

    # 初始化共享工作流引擎
    engine = WorkflowEngine()
    app.state.workflow_engine = engine
    app.state._main_loop = asyncio.get_running_loop()
    wechat.workflow_engine = engine
    workflow.workflow_engine = engine
    # 注入共享引擎到飞书长连接客户端，避免重复创建
    try:
        from mindflow_map.api import feishu as feishu_module
        feishu_module.feishu_client.set_workflow_engine(engine)
    except Exception:
        logger.debug("Feishu client not available or failed to inject workflow engine", exc_info=True)

    yield

    # 关闭时释放资源
    await engine.shutdown()
    try:
        await engine.alpha_id_client.close()
    except Exception:
        pass


app = FastAPI(
    title=settings.app_name,
    description="MindFlow Map - AI智能地图助理",
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS - 仅允许可信来源，避免通配符 + 凭证的组合
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件
static_dir = Path(__file__).resolve().parent.parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 路由
app.include_router(health.router, prefix="/health", tags=["健康检查"])
app.include_router(map.router, prefix="/api/v1/map", tags=["地图"])
app.include_router(workflow.router, prefix="/api/v1/workflow", tags=["工作流"])
app.include_router(wechat.router, prefix="/api/v1/wechat", tags=["微信"])
app.include_router(automation.router, prefix="/api/v1/automation", tags=["自动化"])
app.include_router(shortdramas.router, prefix="/api/v1/shortdramas", tags=["短剧预审"])
app.include_router(autopilot.router, prefix="/api/v1/autopilot", tags=["autopilot"])


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "workspace": "/workspace",
    }


@app.get("/workspace", response_class=HTMLResponse)
async def workspace(request: Request):
    """MindFlow Workspace 统一工作台"""
    templates_dir = Path(__file__).resolve().parent.parent.parent / "templates"
    workspace_file = templates_dir / "workspace.html"
    if not workspace_file.exists():
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace_file.read_text(encoding="utf-8")
