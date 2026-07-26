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

# Ensure project root is on path (for importing config, auth, etc.)
sys.path.insert(0, os.path.dirname(__file__))

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import (
    NET_AGENT_HOST,
    NET_AGENT_PORT,
    GATEWAY_URL,
)
from api.routes import router as net_router
from db.models import init_db
from db.sqlite_store import DB_PATH
from utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: ensure DB exists. Shutdown: cleanup."""
    import sqlite3
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)
    conn.close()
    logger.info("Net-Agent database ready at %s", DB_PATH)
    logger.info("Net-Agent server started — listening on %s:%d", NET_AGENT_HOST, NET_AGENT_PORT)
    logger.info("Upstream: Gateway at %s", GATEWAY_URL)
    yield
    logger.info("Net-Agent server shutdown complete")


app = FastAPI(
    title="Net-Agent Server",
    description="Ghost Network Operations Service — /v1/net/*",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — match Gateway's allowlist for consistency
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


# ── health check ────────────────────────────────────────────
@app.get("/health")
async def health():
    """Liveness probe."""
    return {"service": "net-agent", "status": "ok"}


# ── mount all /v1/net routes ──────────────────────────────
app.include_router(net_router)


# ── startup banner ─────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print(f"""
╔══════════════════════════════════════════════════╗
║           Net-Agent Server v1.0.0                ║
║   Ghost Network Operations Service               ║
╠══════════════════════════════════════════════════╣
║   Port:      {NET_AGENT_PORT}                                ║
║   DB:        {DB_PATH}  ║
║   Gateway:   {GATEWAY_URL}    ║
╚══════════════════════════════════════════════════╝
    """)
    uvicorn.run(app, host=NET_AGENT_HOST, port=NET_AGENT_PORT)
