#!/usr/bin/env python3
"""
Ghost Gateway — Unified API Gateway
====================================
Single entry point for all Ghost services:
  - Identity & Memory → Alpha-ID
  - Workflow Engine  → Nebula
  - Registration     → Flow

Design principles:
  - Zero-trust defaults (explicit allowlists, no wildcard CORS in prod)
  - Observable (structured logs, correlation IDs, timing)
  - Resilient (timeouts, circuit-aware health, graceful degradation)
"""

import os
import json
import time
import uuid
import logging
import requests
import httpx
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
from doubao_reader.obsidian_writer import ObsidianWriter
from doubao_reader.knowledge_refiner import refine_conversation, refine_memory
from doubao_reader.obsidian_organizer import run_organization, batch_link_related
from doubao_reader.log_reader import LogReader
import os as _os
ORCHESTRATOR_URL = _os.getenv("ORCHESTRATOR_URL", "http://localhost:19090")

load_dotenv()


# ============================================================
# Configuration
# ============================================================
ALPHAID_URL = os.getenv("ALPHAID_URL", "http://localhost:8000")
NEBULA_URL = os.getenv("NEBULA_URL", "http://localhost:2002")
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:19090")
FLOW_URL = os.getenv("FLOW_URL", "http://localhost:3001")
DEFAULT_ALPHA_ID = os.getenv("DEFAULT_ALPHA_ID", "")
GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", "18080"))
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# ============================================================
# Structured Logger
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("ghost-gateway")


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
# HTTP client (connection pool) — managed in lifespan
# ============================================================
client: httpx.AsyncClient = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle — create client on startup, cleanup on shutdown."""
    global client
    client = httpx.AsyncClient(
        timeout=30.0,
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    )
    logger.info("Gateway started — Alpha-ID=%s Nebula=%s Flow=%s", ALPHAID_URL, NEBULA_URL, FLOW_URL)
    yield
    await client.aclose()
    logger.info("Gateway shutdown complete")


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
# Zero-trust default: in production, wildcard is rejected; in dev, localhost is assumed.
_ALLOWED_ENV = os.getenv("AID_ALLOWED_ORIGINS", "").strip()
if _ALLOWED_ENV == "*":
    if ENVIRONMENT == "production":
        logger.warning("CORS wildcard (*) blocked in production — falling back to localhost only")
        allow_origins = ["http://localhost:3000", "http://localhost:3001", "http://localhost:18080", "http://localhost:8000"]
    else:
        allow_origins = ["*"]
elif _ALLOWED_ENV:
    allow_origins = [o.strip() for o in _ALLOWED_ENV.split(",") if o.strip()]
else:
    # Default: explicit localhost origins (never wildcard unless explicitly set)
    allow_origins = ["http://localhost:3000", "http://localhost:3001", "http://localhost:18080", "http://localhost:8000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

# ============================================================
# Middleware: Correlation ID + Access Log
# ============================================================
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Inject correlation ID for distributed tracing and log all requests."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:12])
    request.state.request_id = request_id
    start = time.time()

    response = await call_next(request)

    duration_ms = round((time.time() - start) * 1000, 1)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "%s %s %s %.1fms [%s]",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        request_id,
    )
    return response


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


def ok(data: dict, request: Request = None) -> JSONResponse:
    """Unified success response — if data contains backend error, return failure status."""
    ts = int(time.time())
    request_id = getattr(request.state, "request_id", None) if request else None
    if has_error(data):
        body = {"success": False, "error": data["_error"], "data": data, "ts": ts}
        if request_id:
            body["request_id"] = request_id
        return JSONResponse(body, status_code=502)
    body = {"success": True, "data": data, "ts": ts}
    if request_id:
        body["request_id"] = request_id
    return JSONResponse(body)


def fail(msg: str, code: int = 500, request: Request = None) -> JSONResponse:
    """Unified failure response."""
    ts = int(time.time())
    request_id = getattr(request.state, "request_id", None) if request else None
    body = {"success": False, "error": msg, "ts": ts}
    if request_id:
        body["request_id"] = request_id
    return JSONResponse(body, status_code=code)


# ============================================================
# Health Check
# ============================================================
@app.get("/health")
async def health(request: Request):
    """Health check - returns component status including Obsidian vault."""
    # Check Alpha-ID
    alphaid_ok = False
    obsidian_ok = False
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            ar = await client.get(f"{ALPHAID_URL}/brain/status")
            alphaid_ok = ar.status_code < 500
    except:
        pass
    
    # Check Obsidian vault
    vault_path = os.environ.get("OBSIDIAN_VAULT", r"D:\Obsidian\Ghost知识库")
    obsidian_ok = os.path.isdir(vault_path) and len(os.listdir(vault_path)) > 0
    
    return ok({
        "gateway": "ok",
        "alphaid": "ok" if alphaid_ok else "error",
        "obsidian": "ok" if obsidian_ok else "not_found",
    }, request)


# ============================================================
# Periodic scanner for Doubao desktop app LevelDB
# ============================================================

import threading

_scanner_started = False

def ensure_scanner():
    global _scanner_started
    if _scanner_started:
        return
    _scanner_started = True
    
    import asyncio
    import time
    
    def scan_loop():
        reader = LogReader()
        time.sleep(10)  # Wait for server to start
        while True:
            try:
                convs = reader.read_all()
                logger.info("Doubao scanner: found %d conversations", len(convs))
                for conv in convs[:5]:  # Limit to 5 per scan
                    payload = conv.to_dict()
                    try:
                        r = requests.post(
                            f"http://localhost:{GATEWAY_PORT}/v1/doubao/capture",
                            json=payload,
                            timeout=5
                        )
                        logger.debug("Scanned: %s", r.status_code)
                    except Exception as e:
                        logger.debug("Scan send error: %s", e)
            except Exception as e:
                logger.error("Doubao scanner error: %s", e)
            # Run Obsidian organization
            try:
                run_organization()
                batch_link_related()
            except Exception as org_err:
                logger.error("Organization error: %s", org_err)
            
            time.sleep(120)  # Scan every 2 minutes
    
    thread = threading.Thread(target=scan_loop, daemon=True)
    thread.start()
    logger.info("Doubao desktop log scanner started")


# Doubao Workspace Page
# ============================================================

@app.get("/v1/doubao")
async def doubao_page(request: Request):
    """Serve the Doubao workspace page."""
    from fastapi.responses import HTMLResponse
    html_path = os.path.join(os.path.dirname(__file__), "doubao_page.html")
    if os.path.exists(html_path):
        html = open(html_path, "r", encoding="utf-8").read()
        return HTMLResponse(content=html)
    return HTMLResponse(content="<h1>Doubao page not found</h1>", status_code=404)


# ============================================================
# Identity & Memory — Proxy to Alpha-ID
# ============================================================

@app.get("/v1/identity")
async def get_identity(request: Request, alpha_id: Optional[str] = None):
    """Get current identity → proxy to Alpha-ID API (public overview or user profile)."""
    aid = alpha_id or DEFAULT_ALPHA_ID
    # Try authenticated profile first, fall back to public stats
    data = await proxy_get(f"/api/v1/identity/{aid}", ALPHAID_URL, headers={"Authorization": "Bearer placeholder"})
    if "_error" in data:
        data = await proxy_get("/api/v1/identity/stats/overview", ALPHAID_URL)
    return ok(data, request)


@app.get("/v1/profile")
async def get_profile(request: Request):
    """Get user profile → proxy to Alpha-ID."""
    data = await proxy_get("/api/profile", ALPHAID_URL)
    return ok(data, request)


@app.get("/v1/brain/status")
async def get_brain_status(request: Request, alpha_id: Optional[str] = None):
    """Get brain status → proxy to Alpha-ID."""
    aid = alpha_id or DEFAULT_ALPHA_ID
    data = await proxy_get(f"/brain/status?alpha_id={aid}", ALPHAID_URL)
    return ok(data, request)


@app.post("/v1/brain/awake")
async def brain_awake(request: Request):
    """Wake up brain → proxy to Alpha-ID."""
    body = await request.json()
    aid = body.get("alpha_id", DEFAULT_ALPHA_ID)
    data = await proxy_post("/brain/awake", ALPHAID_URL, body={"alpha_id": aid})
    return ok(data, request)


@app.get("/v1/network/topology")
async def get_network_topology(request: Request):
    """Get Agent network topology → proxy to Alpha-ID."""
    data = await proxy_get("/network/topology", ALPHAID_URL)
    return ok(data, request)


@app.post("/v1/chat")
async def chat(request: Request):
    """Chat with Agent → proxy to Alpha-ID /chat, auto-register unknown users."""
    ip = _client_ip(request)
    if not _rate_limit_check(f"chat:{ip}", max_requests=10, window=60):
        return fail("Too many requests, please slow down", 429, request)
    body = await request.json()
    aid = body.get("alpha_id", DEFAULT_ALPHA_ID)
    message = body.get("message", "")
    if not message:
        return fail("message required", 400, request)

    # First attempt: proxy to Alpha-ID /chat
    data = await proxy_post("/chat", ALPHAID_URL, body={"alpha_id": aid, "message": message})

    # If user not registered (401), auto-register via /login then retry
    if data.get("_error") and "401" in str(data.get("_error", "")):
        logger.info("Alpha-ID %s not registered, auto-registering...", aid)
        reg_body = {"alpha_id": aid, "device_fingerprint": f"feishu_{aid}"}
        reg_data = await proxy_post("/login", ALPHAID_URL, body=reg_body)
        if not reg_data.get("_error"):
            logger.info("Alpha-ID %s registered, retrying chat...", aid)
            data = await proxy_post("/chat", ALPHAID_URL, body={"alpha_id": aid, "message": message})
        else:
            logger.warning("Auto-register failed for %s: %s", aid, reg_data.get("_error"))

    return ok(data, request)

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
        return fail("text required", 400, request)

    text_lower = text.lower()
    is_identity = any(kw in text_lower for kw in ["身份", "我是谁", "did", "identity", "画像"])

    if is_identity:
        identity = await proxy_get("/api/v1/identity/stats/overview", ALPHAID_URL)
        profile = await proxy_get("/api/profile", ALPHAID_URL)
        return ok({
            "route": "identity",
            "identity": identity,
            "profile_summary": profile.get("profile", {}).get("persona", {}),
        }, request)
    else:
        data = await proxy_post("/chat", ALPHAID_URL, body={"alpha_id": DEFAULT_ALPHA_ID, "message": text})
        return ok({
            "route": "chat",
            "reply": data.get("reply", ""),
            "raw": data,
        }, request)


# ============================================================


# ============================================================
# Doubao Capture
# ============================================================

@app.post("/v1/doubao/capture")
async def doubao_capture(request: Request):
    """Accept Doubao conversation data from LogReader or Ghost Capture."""
    ip = _client_ip(request)
    if ip not in ("127.0.0.1", "::1", "localhost"):
        logger.warning("Rejected doubao capture from non-local IP: %s", ip)
        return fail("Only local requests allowed", 403, request)
    body = await request.json()
    session_id = body.get("session_id", "")
    messages = body.get("messages", [])
    # Refine: dedup, filter noise, auto-tag
    if messages:
        messages = refine_conversation(body.get("metadata", {}), messages)
    if not session_id or not messages:
        return fail("session_id and messages required", 400, request)
    for m in messages:
        if not all(k in m for k in ("role", "content")):
            return fail("Each message must have role and content", 400, request)
    bot_id = body.get("bot_id", "")
    summary = messages[0].get("content", "")[:100]
    last = messages[-1].get("content", "")[:200] if len(messages) > 1 else ""
    memory_payload = {
        "alpha_id": os.getenv("DEFAULT_ALPHA_ID", "Alpha-001"),
        "content": "[Doubao] " + summary + (" ... " + last if last else ""),
        "category": "doubao_chat",
        "sensitivity": 10,
        "source": "doubao",
        "tags": ["doubao", "chat"] + ([bot_id] if bot_id else []),
        "metadata": {
            "session_id": session_id,
            "bot_id": bot_id,
            "captured_at": body.get("captured_at", 0),
            "message_count": len(messages),
            "messages": messages,
        }
    }
    data = await proxy_post("/memory/store", ALPHAID_URL, body=memory_payload)
    
    # Also write to Obsidian vault
    try:
        import asyncio
        ow = ObsidianWriter()
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, lambda: ow.write_conversation(
            metadata=memory_payload.get("metadata", {}),
            messages=messages,
            session_id=session_id,
            bot_id=bot_id,
        ))
    except Exception as ow_err:
        logger.warning("Obsidian write failed (non-fatal): %s", ow_err)
    
    if has_error(data):
        logger.error("Failed to store doubao memory: %s", data.get("_error"))
        return ok({"status": "stored_with_warning", "session_id": session_id, "error": data.get("_error")}, request)
    # Trigger Obsidian organization in background
        try:
            import threading
            threading.Thread(target=run_organization, daemon=True).start()
        except Exception as org_err:
            logger.debug("Organization trigger error: %s", org_err)
        
        logger.info("Doubao conversation %s captured: %d messages", session_id, len(messages))
    return ok({"status": "stored", "session_id": session_id, "message_count": len(messages)}, request)


@app.post("/v1/memory/store")
async def memory_store(request: Request):
    """Store memory -> proxy to Alpha-ID /memory/store."""
    body = await request.json()
    data = await proxy_post("/memory/store", ALPHAID_URL, body=body)
    return ok(data, request)




@app.post("/v1/orchestrator/task/submit")
async def orch_submit(request: Request):
    body = await request.json()
    data = await proxy_post("/v1/task/submit", ORCHESTRATOR_URL, body=body)
    return ok(data, request)


@app.get("/v1/orchestrator/tasks")
async def orch_tasks(request: Request):
    data = await proxy_get("/v1/tasks", ORCHESTRATOR_URL)
    return ok(data, request)


@app.get("/v1/orchestrator/task/{task_id}")
async def orch_task(task_id: str, request: Request):
    data = await proxy_get(f"/v1/task/{task_id}", ORCHESTRATOR_URL)
    return ok(data, request)



@app.get("/v1/memory/graph")
async def memory_graph(request: Request):
    """Return memory knowledge graph for d3.js visualization. Free, no LLM."""
    import sqlite3, json as _json
    memories = {}
    for dbp in ["D:/MW/alphaid/projects/src/assets/alpha_id.db"]:
        if not os.path.exists(dbp):
            continue
        try:
            conn = sqlite3.connect(dbp)
            row = conn.execute("SELECT data FROM collections WHERE collection_name='Alpha-001'").fetchone()
            if row:
                memories.update(_json.loads(row[0]))
            conn.close()
        except Exception as e:
            logger.warning("DB error: %s", e)
    nodes, edges, seen_tags = [], [], {}
    cmap = {"doubao_chat":"#38bdf8","system":"#22c55e","profile_cursor":"#a78bfa","design":"#f59e0b","general":"#64748b"}
    for mid, mem in memories.items():
        if not isinstance(mem, dict):
            continue
        content = str(mem.get("content",""))[:60]
        category = str(mem.get("category","general"))
        source = str(mem.get("source","unknown"))
        tags = mem.get("tags",[]) or []
        if not isinstance(tags, list):
            tags = []
        nodes.append({"id":mid[:12],"label":content,"category":category,"source":source,"color":cmap.get(category,"#64748b"),"tags":tags})
        for tag in tags:
            if tag in seen_tags:
                edges.append({"from":mid[:12],"to":seen_tags[tag][:12],"label":tag})
            else:
                seen_tags[tag] = mid
    return ok({"nodes":nodes,"edges":edges,"stats":{"memories":len(nodes),"connections":len(edges)}}, request)


# Workflow — Proxy to Nebula
# ============================================================

@app.get("/v1/workflows")
async def get_workflows(request: Request):
    """Get workflow templates → proxy to Nebula."""
    data = await proxy_get("/api/v1/workflow/templates", NEBULA_URL)
    return ok(data, request)


@app.post("/v1/workflows/execute")
async def execute_workflow(request: Request):
    """Execute workflow → proxy to Nebula."""
    body = await request.json()
    data = await proxy_post("/api/v1/workflow/execute", NEBULA_URL, body=body)
    return ok(data, request)


# ============================================================
# Registration — Proxy to Flow
# ============================================================

@app.post("/v1/register/send-sms")
async def register_send_sms(request: Request):
    """Send SMS verification code → proxy to flow/api (rate limited: 5 req/60s/IP)."""
    ip = _client_ip(request)
    if not _rate_limit_check(f"sms:{ip}", max_requests=5, window=60):
        return fail("Too many requests, please try again later", 429, request)
    body = await request.json()
    data = await proxy_post("/api/v1/register/send-sms", ALPHAID_URL, body=body)
    return ok(data, request)


@app.post("/v1/register/verify-sms")
async def register_verify_sms(request: Request):
    """Verify SMS code → proxy to flow/api."""
    body = await request.json()
    data = await proxy_post("/api/v1/register/verify-sms", ALPHAID_URL, body=body)
    return ok(data, request)


@app.post("/v1/register/face-verify")
async def register_face_verify(request: Request):
    """Initiate face verification → proxy to flow/api."""
    body = await request.json()
    data = await proxy_post("/api/v1/register/face-verify", ALPHAID_URL, body=body)
    return ok(data, request)


@app.post("/v1/register/face-query")
async def register_face_query(request: Request):
    """Query face verification result → proxy to flow/api."""
    body = await request.json()
    data = await proxy_post("/api/v1/register/face-query", ALPHAID_URL, body=body)
    return ok(data, request)


@app.post("/v1/register/generate-did")
async def register_generate_did(request: Request):
    """Generate decentralized identity DID → proxy to flow/api."""
    body = await request.json()
    data = await proxy_post("/api/v1/register/generate-did", ALPHAID_URL, body=body)
    return ok(data, request)


@app.post("/v1/register/complete")
async def register_complete(request: Request):
    """Complete registration → proxy to flow/api."""
    body = await request.json()
    data = await proxy_post("/api/v1/register/complete", ALPHAID_URL, body=body)
    return ok(data, request)


# ============================================================
# Unified Dashboard
# ============================================================
@app.get("/v1/dashboard")
async def dashboard(request: Request):
    """
    Unified dashboard — single call returns all data needed.
    Parallel requests to all backends, aggregated response.
    """
    import asyncio

    identity, profile = await asyncio.gather(
        proxy_get("/api/v1/identity/stats/overview", ALPHAID_URL),
        proxy_get(f"/api/v1/identity/{DEFAULT_ALPHA_ID}", ALPHAID_URL),
        return_exceptions=True,
    )

    def _to_result(value):
        if isinstance(value, Exception):
            return {"_error": str(value)}
        return value

    identity, profile = (_to_result(v) for v in (identity, profile))

    return ok({
        "identity": {
            "alpha_id": identity.get("founder_alpha_id", DEFAULT_ALPHA_ID),
            "total_users": identity.get("total_users", 0),
            "state": "ready",
        },
        "profile": profile,
    }, request)


# ============================================================
# Startup
# ============================================================

# ============================================================
# Memory Search - directly read Obsidian vault (zero token cost)
# ============================================================

@app.get("/v1/memory/search")
async def memory_search(keyword: str = "", limit: int = 20, request: Request = None):
    """Search the Obsidian vault for memories matching keyword."""
    vault_path = os.environ.get("OBSIDIAN_VAULT", r"D:\Obsidian\Ghost知识库")
    
    results = []
    try:
        for root, dirs, files in os.walk(vault_path):
            for fname in files:
                if not fname.endswith(".md"):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    text = open(fpath, "r", encoding="utf-8").read()
                except:
                    continue
                
                title = fname.replace(".md", "")
                category = os.path.basename(os.path.dirname(fpath))
                date_str = ""
                tags = []
                
                if text.startswith("---"):
                    end_idx = text.find("---", 3)
                    if end_idx > 0:
                        fm = text[3:end_idx]
                        for line in fm.split("\n"):
                            line = line.strip()
                            if line.startswith("title:"):
                                title = line.split(":", 1)[1].strip().strip("\"")
                            elif line.startswith("date:"):
                                date_str = line.split(":", 1)[1].strip()
                            elif line.startswith("  - "):
                                tags.append(line[4:].strip())
                
                content_text = text
                if keyword:
                    if keyword.lower() not in content_text.lower():
                        continue
                    kw_lower = keyword.lower()
                    ctx = max(0, content_text.lower().find(kw_lower) - 100)
                    content_text = content_text[ctx:ctx+250]
                
                results.append({
                    "title": title,
                    "file": fname,
                    "category": category,
                    "date": date_str,
                    "tags": tags,
                    "preview": content_text[:300],
                    "modified": os.path.getmtime(fpath),
                })
                
                if len(results) >= limit:
                    break
            if len(results) >= limit:
                break
    except Exception as e:
        return fail(str(e), 500, request)
    
    results.sort(key=lambda r: r["modified"], reverse=True)
    return ok({"results": results, "total": len(results)}, request)


@app.get("/v1/obsidian/status")
async def obsidian_status(request: Request):
    """Check Obsidian vault status."""
    vault_path = os.environ.get("OBSIDIAN_VAULT", r"D:\Obsidian\Ghost知识库")
    exists = os.path.isdir(vault_path)
    file_count = 0
    recent_file = ""
    if exists:
        for root, dirs, files in os.walk(vault_path):
            for f in files:
                if f.endswith(".md"):
                    file_count += 1
                    fpath = os.path.join(root, f)
                    mtime = os.path.getmtime(fpath)
                    if not recent_file or mtime > os.path.getmtime(os.path.join(vault_path, recent_file)):
                        recent_file = f
    return ok({
        "exists": exists,
        "path": vault_path,
        "file_count": file_count,
        "recent_file": recent_file,
    }, request)
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
