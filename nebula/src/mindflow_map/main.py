"""FastAPI 主入口 - MindFlow Map 后端服务"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from mindflow_map.config import settings
from mindflow_map.config_validator import check_all
from mindflow_map.api import approvals, automation, events, health, map, streaming, workflow, feishu_webhook
from mindflow_map.api.openapi_config import custom_openapi
from mindflow_map.core.metrics import get_metrics
from mindflow_map.logging_config import setup_logging
from mindflow_map.middleware.audit import AuditMiddleware
from mindflow_map.middleware.auth import AuthMiddleware
from mindflow_map.middleware.correlation_id import CorrelationIdMiddleware
from mindflow_map.middleware.error_handler import register_error_handlers
from mindflow_map.middleware.prometheus import PrometheusMiddleware
from mindflow_map.middleware.rate_limit import RateLimitMiddleware
from mindflow_map.models.session import init_db, close_db, get_database
from mindflow_map.workflows.engine import WorkflowEngine

logger = logging.getLogger(__name__)

# 飞书客户端引用（延迟初始化）
_feishu_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _feishu_client

    # 配置结构化日志（幂等）
    setup_logging()

    # 启动时校验平台配置
    status = check_all()
    for platform, info in status.items():
        if not info["configured"]:
            logger.warning("平台配置缺失 [%s]: %s", platform, info["message"])
        else:
            logger.info("平台配置就绪 [%s]", platform)

    # 初始化数据库
    await init_db()
    logger.info("Database initialized")

    # 初始化共享工作流引擎（统一注册到 EngineRegistry）
    engine = WorkflowEngine()
    engine._main_loop = asyncio.get_running_loop()
    app.state.workflow_engine = engine
    app.state._main_loop = engine._main_loop
    # H14 修复：统一使用 EngineRegistry，不再注入到各模块的全局变量
    from mindflow_map.core.engine_registry import set_engine
    set_engine(engine)

    # 启动飞书长连接机器人（后台线程）
    try:
        from mindflow_map.api import feishu as feishu_module
        feishu_module.feishu_client.set_gateway_url("http://localhost:18080")
        feishu_module.feishu_client.start()
        _feishu_client = feishu_module.feishu_client
        logger.info("飞书机器人长连接已启动")
    except Exception:
        logger.debug("飞书机器人启动失败（可能未配置）", exc_info=True)

    yield

    # 关闭时释放资源
    if _feishu_client:
        _feishu_client.stop()
    # 关闭共享 httpx 客户端
    from mindflow_map.api.feishu_sender import FeishuSender
    
    await FeishuSender.close_shared_client()
    
    await engine.shutdown()
    try:
        await engine.alpha_id_client.close()
    except Exception:
        pass
    await close_db()


app = FastAPI(
    title=settings.app_name,
    description="MindFlow Map - AI智能地图助理",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# 使用自定义 OpenAPI Schema
app.openapi = lambda: custom_openapi(app)

# CORS - 允许可信来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:2002",      # MindFlow Map 自身
        "http://localhost:3000",      # MindFlow Web
        "http://127.0.0.1:2002",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 审计日志中间件
db = get_database()
app.add_middleware(AuditMiddleware, db=db)

# 认证中间件（支持 Bearer Token 和 Header 认证）
app.add_middleware(AuthMiddleware, db=db)

# 限流中间件
_rate_limit_window = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
_rate_limit_max = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "100"))
app.add_middleware(RateLimitMiddleware, window_seconds=_rate_limit_window, max_requests=_rate_limit_max)

# Prometheus 指标采集中间件
app.add_middleware(PrometheusMiddleware)

# Correlation ID 中间件（最外层）
app.add_middleware(CorrelationIdMiddleware)

# 注册统一错误处理器
register_error_handlers(app)

# 静态文件
static_dir = Path(__file__).resolve().parent.parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 挂载可视化工作流编辑器
editor_dir = Path(__file__).resolve().parent.parent.parent / "workflow-editor" / "dist"
if editor_dir.exists():
    app.mount("/editor", StaticFiles(directory=str(editor_dir), html=True), name="workflow-editor")

# 路由
app.include_router(health.router, prefix="/health", tags=["健康检查"])
app.include_router(map.router, prefix="/api/v1/map", tags=["地图"])
app.include_router(workflow.router, prefix="/api/v1/workflow", tags=["工作流"])
# wechat router not available
app.include_router(automation.router, prefix="/api/v1/automation", tags=["自动化"])
# app.include_router(shortdramas... commented out
app.include_router(streaming.router, prefix="/api/v1/streaming", tags=["streaming"])
app.include_router(approvals.router, prefix="/api/v1/approvals", tags=["approvals"])
app.include_router(events.router, prefix="/api/v1/events", tags=["events"])
app.include_router(feishu_webhook.router, prefix="/api/v1", tags=["飞书"])


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


@app.get("/metrics")
async def metrics():
    """Prometheus metrics 端点。"""
    registry = get_metrics()
    return PlainTextResponse(content=registry.render(), media_type="text/plain; version=0.0.4")




