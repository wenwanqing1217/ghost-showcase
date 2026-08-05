#!/usr/bin/env python3
"""
Gateway Configuration
=======================
Centralized environment-driven configuration.
All service URLs, ports, and runtime settings live here.
"""

import logging
import os

logger = logging.getLogger("ghost-gateway")

# --- Service URLs ---
# 默认值对应 docker-compose 中的服务名和端口
# 本地开发可通过环境变量覆盖为 localhost
ALPHAID_URL = os.getenv("ALPHAID_URL", "http://alphaid:8000")
NEBULA_URL = os.getenv("NEBULA_URL", "http://nebula:2002")
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://orchestrator:19090")
FLOW_URL = os.getenv("FLOW_URL", "http://flow:3036")
NETAGENT_URL = os.getenv("NETAGENT_URL", "http://netagent:18180")
DS_URL = os.getenv("DS_URL", "http://ghost-ds:3000")
TOOL_A_URL = os.getenv("TOOL_A_URL", "http://tool-a:8081")
TOOL_B_URL = os.getenv("TOOL_B_URL", "http://tool-b:8082")
MONEYPRINTER_URL = os.getenv("MONEYPRINTER_URL", "http://moneyprinter:8080")
MONEYPRINTER_PUBLIC_URL = os.getenv("MONEYPRINTER_PUBLIC_URL", "http://localhost:8080")

# --- Upload-Post (跨平台视频发布：TikTok / Instagram / YouTube) ---
# 文档: https://docs.upload-post.com
# 在 upload-post.com 注册获取 API Key 和 Username
UPLOAD_POST_API_KEY = os.getenv("UPLOAD_POST_API_KEY", "")
UPLOAD_POST_USERNAME = os.getenv("UPLOAD_POST_USERNAME", "")
UPLOAD_POST_API_BASE = os.getenv("UPLOAD_POST_API_BASE", "https://api.upload-post.com")

# --- Game Generation ---
GAME_STORAGE_DIR = os.getenv("GAME_STORAGE_DIR", "/app/generated_games")
GAME_PUBLIC_URL = os.getenv("GAME_PUBLIC_URL", "http://localhost:18080/games")

# --- Identity ---
DEFAULT_ALPHA_ID = os.getenv("DEFAULT_ALPHA_ID", "")
AUTH_MASTER_KEY = os.getenv("AUTH_MASTER_KEY", "")

# --- Runtime ---
GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", "18080"))
GATEWAY_HOST = os.getenv("GATEWAY_HOST", "0.0.0.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# --- Rate Limiting ---
_RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "5"))
_RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))


# --- CORS ---
def get_allowed_origins() -> list[str]:
    """
    Compute allowed CORS origins based on environment.
    Zero-trust default: wildcard (*) is rejected in production.

    Priority:
      1. Explicit AID_ALLOWED_ORIGINS env var (comma-separated)
      2. Development: localhost defaults
      3. Production: empty list (must be explicitly configured)
    """
    allowed_env = os.getenv("AID_ALLOWED_ORIGINS", "").strip()
    localhost_origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:18080",
        "http://localhost:8000",
    ]
    if allowed_env == "*":
        if ENVIRONMENT == "production":
            # Wildcard in production is a security risk — require explicit origins
            logger.warning(
                "AID_ALLOWED_ORIGINS=* rejected in production. "
                "Set explicit origins or leave unset for secure default."
            )
            return []
        return ["*"]
    if allowed_env:
        return [o.strip() for o in allowed_env.split(",") if o.strip()]
    # Default: localhost for dev, empty for production
    if ENVIRONMENT == "production":
        return []
    return localhost_origins


# --- WorldMonitor (Global Intelligence API) ---
WORLDMONITOR_API_KEY = os.getenv("WORLDMONITOR_API_KEY", "")
WORLDMONITOR_BASE_URL = os.getenv(
    "WORLDMONITOR_BASE_URL", "https://api.worldmonitor.app"
)
WORLDMONITOR_MCP_URL = os.getenv("WORLDMONITOR_MCP_URL", "https://worldmonitor.app/mcp")
