"""Flow Workflow Layer — /v1/agent/flow/* routes.

Proxies to the Flow service (Fastify on :3036) which provides:
  - /health                                health check
  - /workflow/templates…                   workflow template management & execution
  - /aid/capabilities, /aid/sessions/*      AID (Agent Interaction Dialog) sessions
  - /map/search, /map/pois, /map/routes/*   map POI search & route planning
  - /computer-use/status, /computer-use/*   browser automation tasks

Flow returns {success, data/error} envelopes; unwrap_flow_response
converts these to the Gateway's unified envelope.
"""

import logging

from fastapi import APIRouter, Request

from services.proxy import (
    proxy_get,
    proxy_post,
    ok,
    fail,
    unwrap_flow_response,
    get_client,
    filter_headers,
)

import config

logger = logging.getLogger("ghost-gateway")

router = APIRouter(prefix="/v1/agent/flow", tags=["flow"])


# ── Health ──


@router.get("/health")
async def flow_health(request: Request):
    """Proxy health check to Flow service."""
    data = await proxy_get("/health", config.FLOW_URL)
    return ok(unwrap_flow_response(data), request)


# ── Workflow Templates ──


@router.get("/templates")
async def list_templates(request: Request):
    """List available workflow templates."""
    data = await proxy_get("/workflow/templates", config.FLOW_URL)
    return ok(unwrap_flow_response(data), request)


@router.get("/templates/{template_id}")
async def get_template(template_id: str, request: Request):
    """Get a specific workflow template by ID."""
    data = await proxy_get(f"/workflow/templates/{template_id}", config.FLOW_URL)
    return ok(unwrap_flow_response(data), request)


@router.post("/execute")
async def execute_workflow(request: Request):
    """Execute a workflow — auto-matches template or returns 404."""
    body = await request.json()
    headers = filter_headers(dict(request.headers))
    data = await proxy_post("/workflow/execute", config.FLOW_URL, body, headers)
    return ok(unwrap_flow_response(data), request)


@router.get("/executions")
async def list_executions(request: Request):
    """List all workflow executions."""
    data = await proxy_get("/workflow/executions", config.FLOW_URL)
    return ok(unwrap_flow_response(data), request)


@router.get("/executions/{execution_id}")
async def get_execution(execution_id: str, request: Request):
    """Get a specific workflow execution by ID."""
    data = await proxy_get(f"/workflow/executions/{execution_id}", config.FLOW_URL)
    return ok(unwrap_flow_response(data), request)


# ── AID (Agent Interaction Dialog) ──


@router.get("/aid/capabilities")
async def aid_capabilities(request: Request):
    """Get AID agent capabilities."""
    data = await proxy_get("/aid/capabilities", config.FLOW_URL)
    return ok(unwrap_flow_response(data), request)


@router.post("/aid/sessions")
async def create_aid_session(request: Request):
    """Create a new AID session."""
    body = (
        await request.json()
        if request.headers.get("content-length", "0") != "0"
        else {}
    )
    headers = filter_headers(dict(request.headers))
    data = await proxy_post("/aid/sessions", config.FLOW_URL, body, headers)
    return ok(unwrap_flow_response(data), request)


@router.get("/aid/sessions/{session_id}")
async def get_aid_session(session_id: str, request: Request):
    """Get AID session state."""
    data = await proxy_get(f"/aid/sessions/{session_id}", config.FLOW_URL)
    return ok(unwrap_flow_response(data), request)


@router.post("/aid/sessions/{session_id}/messages")
async def post_aid_message(session_id: str, request: Request):
    """Send a message to an AID session."""
    body = await request.json()
    headers = filter_headers(dict(request.headers))
    data = await proxy_post(
        f"/aid/sessions/{session_id}/messages", config.FLOW_URL, body, headers
    )
    return ok(unwrap_flow_response(data), request)


@router.delete("/aid/sessions/{session_id}")
async def delete_aid_session(session_id: str, request: Request):
    """Delete an AID session."""
    client = get_client()
    try:
        resp = await client.delete(f"{config.FLOW_URL}/aid/sessions/{session_id}")
        if resp.status_code == 200:
            return ok(unwrap_flow_response(resp.json()), request)
        return fail(f"Flow returned {resp.status_code}", resp.status_code, request)
    except Exception as e:
        return fail(f"Flow unreachable: {str(e)}", 502, request)


# ── Map / POI ──


@router.get("/map/search")
async def map_search(request: Request, q: str = "", lat: float = 0.0, lon: float = 0.0):
    """Search POIs by keyword and optional location."""
    data = await proxy_get(f"/map/search?q={q}&lat={lat}&lon={lon}", config.FLOW_URL)
    return ok(unwrap_flow_response(data), request)


@router.get("/map/pois")
async def list_pois(request: Request):
    """List all POIs."""
    data = await proxy_get("/map/pois", config.FLOW_URL)
    return ok(unwrap_flow_response(data), request)


@router.post("/map/routes")
async def create_route(request: Request):
    """Plan a route between POIs."""
    body = await request.json()
    headers = filter_headers(dict(request.headers))
    data = await proxy_post("/map/routes", config.FLOW_URL, body, headers)
    return ok(unwrap_flow_response(data), request)


@router.get("/map/routes")
async def list_routes(request: Request):
    """List all saved routes."""
    data = await proxy_get("/map/routes", config.FLOW_URL)
    return ok(unwrap_flow_response(data), request)


@router.get("/map/routes/{route_id}")
async def get_route(route_id: str, request: Request):
    """Get a specific route by ID."""
    data = await proxy_get(f"/map/routes/{route_id}", config.FLOW_URL)
    return ok(unwrap_flow_response(data), request)


@router.delete("/map/routes/{route_id}")
async def delete_route(route_id: str, request: Request):
    """Delete a saved route."""
    client = get_client()
    try:
        resp = await client.delete(f"{config.FLOW_URL}/map/routes/{route_id}")
        if resp.status_code == 200:
            return ok(unwrap_flow_response(resp.json()), request)
        return fail(f"Flow returned {resp.status_code}", resp.status_code, request)
    except Exception as e:
        return fail(f"Flow unreachable: {str(e)}", 502, request)


# ── Computer Use ──


@router.get("/computer-use/status")
async def computer_use_status(request: Request):
    """Get computer-use agent status."""
    data = await proxy_get("/computer-use/status", config.FLOW_URL)
    return ok(unwrap_flow_response(data), request)


@router.post("/computer-use/tasks")
async def create_computer_task(request: Request):
    """Create a new computer-use task."""
    body = await request.json()
    headers = filter_headers(dict(request.headers))
    data = await proxy_post("/computer-use/tasks", config.FLOW_URL, body, headers)
    return ok(unwrap_flow_response(data), request)


@router.get("/computer-use/tasks")
async def list_computer_tasks(request: Request):
    """List all computer-use tasks."""
    data = await proxy_get("/computer-use/tasks", config.FLOW_URL)
    return ok(unwrap_flow_response(data), request)


@router.get("/computer-use/tasks/{task_id}")
async def get_computer_task(task_id: str, request: Request):
    """Get a specific computer-use task by ID."""
    data = await proxy_get(f"/computer-use/tasks/{task_id}", config.FLOW_URL)
    return ok(unwrap_flow_response(data), request)


@router.post("/computer-use/screenshot")
async def take_screenshot(request: Request):
    """Request a screenshot from the computer-use agent."""
    body = (
        await request.json()
        if request.headers.get("content-length", "0") != "0"
        else {}
    )
    headers = filter_headers(dict(request.headers))
    data = await proxy_post("/computer-use/screenshot", config.FLOW_URL, body, headers)
    return ok(unwrap_flow_response(data), request)
