"""Enhanced health check with dependency status."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter

from mindflow_map.config_validator import check_all

logger = logging.getLogger(__name__)

router = APIRouter()


def _check_database() -> Dict[str, Any]:
    """Check database connectivity."""
    try:
        from mindflow_map.memory.store import MemoryStore
        from mindflow_map.config import settings

        store = MemoryStore()
        return {
            "status": "ok",
            "url": settings.database_url.split("?")[0].rsplit("/", 1)[0] + "/...",
        }
    except Exception as exc:  # noqa: BLE001
        logger.debug("Database health check failed: %s", exc)
        return {"status": "error", "error": str(exc)}


def _check_llm() -> Dict[str, Any]:
    """Check LLM configuration."""
    try:
        from mindflow_map.config import settings

        if not settings.openai_api_key:
            return {"status": "not_configured", "message": "OPENAI_API_KEY not set"}

        return {
            "status": "configured",
            "model": settings.ai_model,
            "base_url": settings.openai_base_url,
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": str(exc)}


@router.get("/")
async def health_check():
    """
    Basic health check endpoint.

    Returns service status, version, and timestamp.
    For load balancer health checks.
    """
    return {
        "status": "ok",
        "service": "mindflow-map",
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/livez")
async def liveness():
    """
    Kubernetes liveness probe.

    Returns 200 if the service is running.
    """
    return {"status": "ok"}


@router.get("/readyz")
async def readiness():
    """
    Kubernetes readiness probe.

    Checks if the service is ready to accept traffic.
    """
    platform_status = check_all()
    configured_platforms = [p for p, info in platform_status.items() if info.get("configured")]

    return {
        "status": "ready",
        "service": "mindflow-map",
        "platforms_configured": configured_platforms,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/healthz")
async def healthz():
    """
    Comprehensive health check with dependency status.

    Returns detailed status of all system dependencies.
    """
    return {
        "status": "healthy",
        "service": "mindflow-map",
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dependencies": {
            "database": _check_database(),
            "llm": _check_llm(),
        },
        "platforms": check_all(),
    }


@router.get("/config")
async def config_status():
    """Platform configuration status."""
    return check_all()
