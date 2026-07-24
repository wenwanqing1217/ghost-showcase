"""自定义 OpenAPI Schema 配置。"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def custom_openapi(app: FastAPI) -> dict[str, Any]:
    """为 FastAPI 应用生成增强版 OpenAPI Schema。"""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # ------------------------------------------------------------------
    # Info
    # ------------------------------------------------------------------
    openapi_schema["info"]["x-api-version"] = "v1"
    openapi_schema["info"]["contact"] = {
        "name": "MindFlow Team",
        "email": "team@mindflow.ai",
        "url": "https://github.com/mindflow/mindflow-map",
    }
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }

    # ------------------------------------------------------------------
    # Servers
    # ------------------------------------------------------------------
    openapi_schema["servers"] = [
        {"url": "/", "description": "当前服务"},
        {"url": "https://api.mindflow.ai", "description": "生产环境"},
    ]

    # ------------------------------------------------------------------
    # Security Schemes
    # ------------------------------------------------------------------
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Bearer Token 认证，通过 `Authorization: Bearer <token>` 传递。",
        },
        "TenantAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-Tenant-ID",
            "description": "租户标识，服务间调用时使用。",
        },
    }

    # 全局安全要求（health 端点除外）
    openapi_schema["security"] = [{"BearerAuth": []}, {"TenantAuth": []}]

    # ------------------------------------------------------------------
    # Tag Descriptions
    # ------------------------------------------------------------------
    openapi_schema["tags"] = [
        {"name": "健康检查", "description": "服务健康状态与依赖检查，供负载均衡器和 K8s 探针使用。"},
        {"name": "地图", "description": "地点搜索、路线规划、地理编码等地图相关能力。"},
        {"name": "工作流", "description": "AI 工作流执行与模板管理。"},
        {"name": "微信", "description": "微信公众号/小程序回调接口。"},
        {"name": "自动化", "description": "抖音短剧发布、Shopify 店铺运营等自动化任务。"},
        {"name": "短剧预审", "description": "短剧内容预审核与回调通知。"},
        {"name": "streaming", "description": "SSE 流式响应接口，用于实时事件推送。"},
        {"name": "approvals", "description": "多级审批流程与历史记录。"},
        {"name": "events", "description": "飞书与微信事件订阅回调。"},
    ]

    # ------------------------------------------------------------------
    # 为 health 端点移除安全要求
    # ------------------------------------------------------------------
    _remove_security_for_health(openapi_schema)

    # ------------------------------------------------------------------
    # 为需要认证的端点添加安全要求
    # ------------------------------------------------------------------
    _apply_security_requirements(openapi_schema)

    # ------------------------------------------------------------------
    # 统一响应示例
    # ------------------------------------------------------------------
    _add_response_examples(openapi_schema)

    app.openapi_schema = openapi_schema
    return app.openapi_schema


def _remove_security_for_health(schema: dict[str, Any]) -> None:
    """health 端点不需要认证。"""
    paths = schema.get("paths", {})
    for path, methods in paths.items():
        if path.startswith("/health"):
            for method_info in methods.values():
                if isinstance(method_info, dict):
                    method_info.pop("security", None)


def _apply_security_requirements(schema: dict[str, Any]) -> None:
    """为需要认证的端点添加安全要求。"""
    # 默认安全要求：Bearer + Tenant
    security = [{"BearerAuth": []}, {"TenantAuth": []}]

    paths = schema.get("paths", {})
    for path, methods in paths.items():
        if path.startswith("/health") or path == "/" or path == "/workspace":
            continue
        for method_info in methods.values():
            if isinstance(method_info, dict) and "security" not in method_info:
                method_info["security"] = security


def _add_response_examples(schema: dict[str, Any]) -> None:
    """为常见响应模式添加示例。"""
    # 通用成功响应
    success_example = {
        "success": True,
        "data": None,
        "error": None,
        "code": None,
    }

    # 通用错误响应
    error_example = {
        "success": False,
        "data": None,
        "error": "Not Found",
        "code": "NOT_FOUND",
    }

    # 在 components 中注册示例
    if "components" not in schema:
        schema["components"] = {}

    if "examples" not in schema["components"]:
        schema["components"]["examples"] = {}

    schema["components"]["examples"]["SuccessResponse"] = {
        "value": success_example,
        "summary": "成功响应",
    }
    schema["components"]["examples"]["ErrorResponse"] = {
        "value": error_example,
        "summary": "错误响应",
    }
