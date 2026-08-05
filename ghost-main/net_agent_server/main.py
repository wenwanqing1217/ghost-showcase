#!/usr/bin/env python3
"""
Net-Agent Server — Entry Point
================================
Standalone FastAPI microservice for network operations.
Integrates with Ghost Gateway via /v1/net/* route forwarding.

Run:
    python main.py
    # or
    uvicorn main:app --host 0.0.0.0 --port 18180
"""

import os
import sys

# __file__ = ghost-main/net_agent_server/main.py
# We need ghost-main/ on path for net_agent_common imports,
# and net_agent_server/ on path for api/ imports.
_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)  # ghost-main/
sys.path.insert(0, _PARENT)
sys.path.insert(0, _HERE)

from contextlib import asynccontextmanager

from api.routes import router as net_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from net_agent_common.config.settings import (
    GATEWAY_URL,
    NET_AGENT_HOST,
    NET_AGENT_PORT,
    validate_security_settings,
)
from net_agent_common.db.models import init_db
from net_agent_common.db.sqlite_store import DB_PATH
from net_agent_common.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: ensure DB exists + validate security. Shutdown: cleanup."""
    # 安全：启动时校验 JWT 密钥配置，不满足则拒绝启动
    validate_security_settings()
    import sqlite3
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)
    conn.close()
    logger.info("Net-Agent database ready at %s", DB_PATH)
    logger.info("Net-Agent server started \u2014 listening on %s:%d", NET_AGENT_HOST, NET_AGENT_PORT)
    logger.info("Upstream: Gateway at %s", GATEWAY_URL)
    yield
    logger.info("Net-Agent server shutdown complete")


app = FastAPI(
    title="Net-Agent Server",
    description="Ghost Network Operations Service \u2014 /v1/net/*",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:18080",
        "http://localhost:8000",
        "http://localhost:18180",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)


@app.get("/health")
async def health():
    return {"service": "net-agent", "status": "ok"}


app.include_router(net_router)


if __name__ == "__main__":
    import uvicorn
    print("""
\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557
\u2551           Net-Agent Server v1.0.0                \u2551
\u2551   Ghost Network Operations Service               \u2551
\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d
    """)
    uvicorn.run(app, host=NET_AGENT_HOST, port=NET_AGENT_PORT)
