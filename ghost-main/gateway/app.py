#!/usr/bin/env python3
"""
Ghost Gateway — Unified API Gateway
====================================
Single entry point for all Ghost services:
  - Identity & Memory → Alpha-ID
  - Workflow Engine  → Nebula
  - Registration     → Flow
"""

import os
import json
import time
import httpx
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# Configuration
# ============================================================
ALPHAID_URL = os.getenv("ALPHAID_URL", "http://localhost:8000")
NEBULA_URL = os.getenv("NEBULA_URL", "http://localhost:2002")
FLOW_URL = os.getenv("FLOW_URL", "http://localhost:3001")
DEFAULT_ALPHA_ID = os.getenv("DEFAULT_ALPHA_ID", "")
GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", "18080"))

# ============================================================
# Rate Limiting (in-memory sliding window)
# ============================================================
_rate_buckets: dict = defaultdict(list)
_RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "5"))
_RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))


def _rate_limit_check(key: str, max_requests: int = None, window: int = None) -> bool:
    """Check rate limit. Returns True if allowed, False if exceeded."""
    now = time.time()
    max_req = max_requests or _RATE_LIMIT_MAX
    win = window or _RATE_LIMIT_WINDOW

    bucket = _rate_buckets[key]
    cutoff = now - win
    _rate_buckets[key] = [t for t in bucket if t > cutoff]

    if len(_rate_buckets[key]) >= max_req:
        return False
    _rate_buckets[key].append(now)
    return True


def _client_ip(request: Request) -> str:
    """Get client real IP (proxy-aware)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ============================================================
# FastAPI Application
# ============================================================
app = FastAPI(
    title="Ghost Gateway",
    description="Ghost Unified API Gateway — Identity + Workflow + Registration",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS: explicit allowlist via AID_ALLOWED_ORIGINS env var (comma-separated)
_allowed_origins = os.getenv("AID_ALLOWED_ORIGINS", "*")
if _allowed_origins == "*":
    allow_origins = ["*"]
else:
    allow_origins = [o.strip() for o in _allowed_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# HTTP client (connection pool) — managed in lifespan
client: httpx.AsyncClient = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle — create client on startup, cleanup on shutdown."""
    global client
    client = httpx.AsyncClient(timeout=30.0, limits=httpx.Limits(max_connections=100, max_keepalive_connections=20))
    yield
    await client.aclose()


# ============================================================
# Utility Functions
# ============================================================
async def proxy_get(path: str, base_url: str, headers: dict = None) -> dict:
    """Proxy GET request to backend."""
    try:
        resp = await client.get(f"{base_url}{path}", headers=headers or {})
        if resp.status_code == 200:
            return resp.json()
        return {"_error": f"backend returned {resp.status_code}", "_raw": resp.text[:200]}
    except Exception as e:
        return {"_error": f"backend unreachable: {str(e)}"}


async def proxy_post(path: str, base_url: str, body: dict = None, headers: dict = None) -> dict:
    """Proxy POST request to backend."""
    try:
        resp = await client.post(f"{base_url}{path}", json=body or {}, headers=headers or {})
        if resp.status_code in (200, 201):
            return resp.json()
        return {"_error": f"backend returned {resp.status_code}", "_raw": resp.text[:200]}
    except Exception as e:
        return {"_error": f"backend unreachable: {str(e)}"}


def has_error(data: dict) -> bool:
    """Check if proxy response contains a backend error."""
    return isinstance(data, dict) and "_error" in data


def unwrap_flow_response(data: dict) -> dict:
    """
    Unpack flow/api's {success, data/error} envelope into Gateway unified envelope.
    flow/api returns {success: true, data: {...}} or {success: false, error: "..."}.
    """
    if not isinstance(data, dict):
        return data
    if data.get("success") is False:
        return {"_error": data.get("error", "flow/api returned failure")}
    if data.get("success") is True and "data" in data:
        return data["data"]
    return data


def ok(data: dict) -> JSONResponse:
    """Unified success response — if data contains backend error, return failure status."""
    if has_error(data):
        return JSONResponse({"success": False, "error": data["_error"], "data": data, "ts": int(time.time())}, status_code=502)
    return JSONResponse({"success": True, "data": data, "ts": int(time.time())})


def fail(msg: str, code: int = 500) -> JSONResponse:
    """Unified failure response."""
    return JSONResponse({"success": False, "error": msg, "ts": int(time.time())}, status_code=code)


# ============================================================
# Health Check
# ============================================================
@app.get("/health")
async def health():
    """Gateway health check + backend connectivity status."""
    result = {
        "gateway": "ok",
        "alphaid": "unknown",
        "nebula": "unknown",
        "flow": "unknown",
    }
    # Check alphaid
    try:
        r = await client.get(f"{ALPHAID_URL}/health", timeout=3)
        result["alphaid"] = "ok" if r.status_code == 200 else f"error({r.status_code})"
    except:
        result["alphaid"] = "unreachable"
    # Check nebula
    try:
        r = await client.get(f"{NEBULA_URL}/health", timeout=3)
        result["nebula"] = "ok" if r.status_code == 200 else f"error({r.status_code})"
    except:
        result["nebula"] = "unreachable"
    # Check flow
    try:
        r = await client.get(f"{FLOW_URL}/api/health", timeout=3)
        result["flow"] = "ok" if r.status_code in (200, 404) else f"error({r.status_code})"
    except:
        result["flow"] = "unreachable"
    return ok(result)


# ============================================================
# Identity & Memory — Proxy to Alpha-ID
# ============================================================

@app.get("/v1/identity")
async def get_identity(alpha_id: Optional[str] = None):
    """Get current identity → proxy to Alpha-ID."""
    aid = alpha_id or DEFAULT_ALPHA_ID
    data = await proxy_get("/identity", ALPHAID_URL, headers={"X-Alpha-ID": aid})
    return ok(data)


@app.get("/v1/profile")
async def get_profile():
    """Get user profile → proxy to Alpha-ID."""
    data = await proxy_get("/api/profile", ALPHAID_URL)
    return ok(data)


@app.get("/v1/brain/status")
async def get_brain_status(alpha_id: Optional[str] = None):
    """Get brain status → proxy to Alpha-ID."""
    aid = alpha_id or DEFAULT_ALPHA_ID
    data = await proxy_get(f"/brain/status?alpha_id={aid}", ALPHAID_URL)
    return ok(data)


@app.post("/v1/brain/awake")
async def brain_awake(request: Request):
    """Wake up brain → proxy to Alpha-ID."""
    body = await request.json()
    aid = body.get("alpha_id", DEFAULT_ALPHA_ID)
    data = await proxy_post("/brain/awake", ALPHAID_URL, body={"alpha_id": aid})
    return ok(data)


@app.get("/v1/network/topology")
async def get_network_topology():
    """Get Agent network topology → proxy to Alpha-ID."""
    data = await proxy_get("/network/topology", ALPHAID_URL)
    return ok(data)


@app.post("/v1/chat")
async def chat(request: Request):
    """Chat with Agent → proxy to Alpha-ID /chat."""
    body = await request.json()
    aid = body.get("alpha_id", DEFAULT_ALPHA_ID)
    message = body.get("message", "")
    if not message:
        return fail("message required", 400)
    data = await proxy_post("/chat", ALPHAID_URL, body={"alpha_id": aid, "message": message})
    return ok(data)


@app.post("/v1/intent/parse")
async def parse_intent(request: Request):
    """
    Intent parsing — gateway-level smart routing.
    Routes to backend based on intent:
      - Identity/Memory → Alpha-ID
      - General chat → Alpha-ID /chat
    """
    body = await request.json()
    text = body.get("text", "").strip()
    if not text:
        return fail("text required", 400)

    text_lower = text.lower()
    is_identity = any(kw in text_lower for kw in ["身份", "我是谁", "did", "identity", "画像"])

    if is_identity:
        identity = await proxy_get("/identity", ALPHAID_URL, headers={"X-Alpha-ID": DEFAULT_ALPHA_ID})
        profile = await proxy_get("/api/profile", ALPHAID_URL)
        return ok({
            "route": "identity",
            "identity": identity,
            "profile_summary": profile.get("profile", {}).get("persona", {}),
        })
    else:
        data = await proxy_post("/chat", ALPHAID_URL, body={"alpha_id": DEFAULT_ALPHA_ID, "message": text})
        return ok({
            "route": "chat",
            "reply": data.get("reply", ""),
            "raw": data,
        })


# ============================================================
# Workflow — Proxy to Nebula
# ============================================================

@app.get("/v1/workflows")
async def get_workflows():
    """Get workflow templates → proxy to Nebula."""
    data = await proxy_get("/api/v1/workflow/templates", NEBULA_URL)
    return ok(data)


@app.post("/v1/workflows/execute")
async def execute_workflow(request: Request):
    """Execute workflow → proxy to Nebula."""
    body = await request.json()
    data = await proxy_post("/api/v1/workflow/execute", NEBULA_URL, body=body)
    return ok(data)


# ============================================================
# Registration — Proxy to Flow
# ============================================================

@app.post("/v1/register/send-sms")
async def register_send_sms(request: Request):
    """Send SMS verification code → proxy to flow/api (rate limited: 5 req/60s/IP)."""
    ip = _client_ip(request)
    if not _rate_limit_check(f"sms:{ip}", max_requests=5, window=60):
        return fail("Too many requests, please try again later", 429)
    body = await request.json()
    data = await proxy_post("/api/register/send-sms", FLOW_URL, body=body)
    return ok(unwrap_flow_response(data))


@app.post("/v1/register/verify-sms")
async def register_verify_sms(request: Request):
    """Verify SMS code → proxy to flow/api."""
    body = await request.json()
    data = await proxy_post("/api/register/verify-sms", FLOW_URL, body=body)
    return ok(unwrap_flow_response(data))


@app.post("/v1/register/face-verify")
async def register_face_verify(request: Request):
    """Initiate face verification → proxy to flow/api."""
    body = await request.json()
    data = await proxy_post("/api/register/face-verify", FLOW_URL, body=body)
    return ok(unwrap_flow_response(data))


@app.post("/v1/register/face-query")
async def register_face_query(request: Request):
    """Query face verification result → proxy to flow/api."""
    body = await request.json()
    data = await proxy_post("/api/register/face-query", FLOW_URL, body=body)
    return ok(unwrap_flow_response(data))


@app.post("/v1/register/generate-did")
async def register_generate_did(request: Request):
    """Generate decentralized identity DID → proxy to flow/api."""
    body = await request.json()
    data = await proxy_post("/api/register/generate-did", FLOW_URL, body=body)
    return ok(unwrap_flow_response(data))


@app.post("/v1/register/complete")
async def register_complete(request: Request):
    """Complete registration → proxy to flow/api."""
    body = await request.json()
    data = await proxy_post("/api/register/complete-registration", FLOW_URL, body=body)
    return ok(unwrap_flow_response(data))


# ============================================================
# Unified Dashboard
# ============================================================
@app.get("/v1/dashboard")
async def dashboard():
    """
    Unified dashboard — single call returns all data needed.
    Parallel requests to all backends, aggregated response.
    """
    import asyncio

    identity, brain, topology, profile = await asyncio.gather(
        proxy_get("/identity", ALPHAID_URL, headers={"X-Alpha-ID": DEFAULT_ALPHA_ID}),
        proxy_get(f"/brain/status?alpha_id={DEFAULT_ALPHA_ID}", ALPHAID_URL),
        proxy_get("/network/topology", ALPHAID_URL),
        proxy_get("/api/profile", ALPHAID_URL),
        return_exceptions=True,
    )

    def _to_result(value):
        if isinstance(value, Exception):
            return {"_error": str(value)}
        return value

    identity, brain, topology, profile = (
        _to_result(v) for v in (identity, brain, topology, profile)
    )

    return ok({
        "identity": {
            "alpha_id": identity.get("alpha_id", DEFAULT_ALPHA_ID),
            "did": topology.get("my_did", "unknown"),
            "state": brain.get("state", "unknown"),
        },
        "brain": brain,
        "network": topology,
        "profile": profile,
    })


# ============================================================
# Startup
# ============================================================
if __name__ == "__main__":
    import uvicorn
    print(f"""
╔══════════════════════════════════════════════════╗
║           Ghost Gateway v2.0.0                   ║
║   Unified API Gateway                            ║
╠══════════════════════════════════════════════════╣
║   Port:     {GATEWAY_PORT}                                ║
║   Alpha-ID: {ALPHAID_URL}    ║
║   Nebula:   {NEBULA_URL}       ║
║   Flow:     {FLOW_URL}       ║
╚══════════════════════════════════════════════════╝
    """)
    uvicorn.run(app, host="0.0.0.0", port=GATEWAY_PORT)
