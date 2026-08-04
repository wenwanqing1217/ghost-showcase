"""HTTP proxy utilities and response helpers.

Design:
  - Preserves backend error details (status code, error body) for debugging
  - Retries on transient failures (connection reset, 502/503/504)
  - Per-route timeout support
  - Single _proxy_request method to eliminate duplication
"""

import time
import logging
from typing import Optional

import httpx
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("ghost-gateway")

# Module-level async client (initialized in lifespan)
client: httpx.AsyncClient = None

# Headers that are safe to forward to backend services.
# Excludes Host (must match backend), Cookie (gateway-scoped session),
# Content-Length/Transfer-Encoding (httpx manages these).
SAFE_PROXY_HEADERS = {
    "authorization",
    "content-type",
    "x-request-id",
    "x-correlation-id",
    "accept",
    "user-agent",
    "x-requested-with",
    "origin",
}

# Headers required by Alpha-ID CSRF middleware.
_CSRF_HEADERS = ("x-requested-with", "origin", "referer")

# Status codes worth retrying (transient failures)
_RETRYABLE_STATUS = {502, 503, 504}
_MAX_RETRIES = 2
_RETRY_DELAY = 0.5  # seconds


def filter_headers(headers: dict) -> dict:
    """Filter request headers to only include safe-to-forward ones."""
    return {k: v for k, v in headers.items() if k.lower() in SAFE_PROXY_HEADERS}


def forward_csrf_headers(request: Request, extra: dict = None) -> dict:
    """Extract CSRF-relevant headers from the incoming request.

    Always includes X-Requested-With: XMLHttpRequest since Gateway acts as
    a trusted internal client when proxying to Alpha-ID.
    Returns a dict with X-Requested-With, Origin, Referer if present.
    Merges with optional extra dict (extra keys take precedence).
    """
    fwd = {}
    for h in _CSRF_HEADERS:
        v = request.headers.get(h)
        if v:
            fwd[h] = v
    # Gateway is the trusted internal client — always set X-Requested-With
    # so Alpha-ID CSRF middleware accepts the proxied request.
    if not fwd.get("x-requested-with"):
        fwd["x-requested-with"] = "XMLHttpRequest"
    if extra:
        fwd.update(extra)
    return fwd


def get_client() -> httpx.AsyncClient:
    """Get the shared HTTP client."""
    return client


async def _proxy_request(
    method: str,
    path: str,
    base_url: str,
    body: dict = None,
    headers: dict = None,
    timeout: float = None,
    is_json: bool = True,
) -> dict:
    """Core proxy request with retry logic and error preservation.

    Returns the JSON response on success. On failure, returns a dict with:
      - _error: Human-readable error summary
      - _status: Original HTTP status code (if available)
      - _raw: Truncated raw response body for debugging
      - _backend: The backend URL that failed
    """
    url = f"{base_url}{path}"
    last_error = None

    for attempt in range(_MAX_RETRIES + 1):
        try:
            kwargs = {"headers": headers or {}}
            if timeout:
                kwargs["timeout"] = timeout
            if body is not None:
                if is_json:
                    kwargs["json"] = body
                else:
                    kwargs["content"] = body
                    kwargs["headers"] = {**kwargs["headers"], "Content-Type": "application/xml"}

            resp = await client.request(method, url, **kwargs)

            if resp.status_code in (200, 201):
                return resp.json()

            # Retry on transient errors
            if resp.status_code in _RETRYABLE_STATUS and attempt < _MAX_RETRIES:
                logger.warning(
                    "Proxy retry %d/%d: %s %s → %d",
                    attempt + 1, _MAX_RETRIES, method, url, resp.status_code,
                )
                await __import__("asyncio").sleep(_RETRY_DELAY * (attempt + 1))
                continue

            # Non-retryable error — preserve details
            error_body = resp.text[:500] if resp.text else ""
            logger.warning(
                "Proxy error: %s %s → %d (%s)",
                method, url, resp.status_code, error_body[:100],
            )
            return {
                "_error": f"backend returned {resp.status_code}",
                "_status": resp.status_code,
                "_raw": error_body,
                "_backend": base_url,
            }
        except httpx.TimeoutException as e:
            last_error = f"timeout: {str(e)}"
            if attempt < _MAX_RETRIES:
                logger.warning("Proxy timeout, retrying %s %s", method, url)
                await __import__("asyncio").sleep(_RETRY_DELAY)
                continue
            return {
                "_error": f"backend timeout after {_MAX_RETRIES + 1} attempts",
                "_backend": base_url,
            }
        except Exception as e:
            return {
                "_error": f"backend unreachable: {str(e)}",
                "_backend": base_url,
            }

    return {"_error": last_error or "unknown error", "_backend": base_url}


async def proxy_delete(
    path: str,
    base_url: str,
    headers: dict = None,
    body: dict = None,
    timeout: float = None,
) -> dict:
    """Proxy DELETE request to backend."""
    return await _proxy_request("DELETE", path, base_url, body=body, headers=headers, timeout=timeout)


async def proxy_get(
    path: str,
    base_url: str,
    headers: dict = None,
    timeout: float = None,
) -> dict:
    """Proxy GET request to backend."""
    return await _proxy_request("GET", path, base_url, headers=headers, timeout=timeout)


async def proxy_post(
    path: str,
    base_url: str,
    body: dict = None,
    headers: dict = None,
    timeout: float = None,
    is_json: bool = True,
) -> dict:
    """Proxy POST request to backend.

    Args:
        path: Backend path (e.g. /api/v1/chat)
        base_url: Backend base URL
        body: JSON dict or raw bytes
        headers: Extra headers to forward
        timeout: Request timeout (seconds)
        is_json: If True, serialize body as JSON; if False, send body as raw content
    """
    return await _proxy_request("POST", path, base_url, body=body, headers=headers, timeout=timeout, is_json=is_json)


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
