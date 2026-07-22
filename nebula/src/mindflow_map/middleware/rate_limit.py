"""Rate limiting middleware with Redis backend support."""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from typing import Any, Deque, Dict, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from mindflow_map.config import settings

logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    """In-memory sliding window rate limiter (single-process only)."""

    def __init__(self, window_seconds: int = 60, max_requests: int = 100) -> None:
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self._client_windows: Dict[str, Deque[float]] = defaultdict(deque)

    async def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        window = self._client_windows[client_id]
        while window and window[0] <= now - self.window_seconds:
            window.popleft()

        if len(window) >= self.max_requests:
            logger.warning(
                "Rate limit exceeded for %s: %d requests in %ds window",
                client_id,
                len(window),
                self.window_seconds,
            )
            return False

        window.append(now)
        return True


class RedisRateLimiter:
    """Redis-backed sliding window rate limiter (multi-process / distributed)."""

    def __init__(self, url: str, window_seconds: int = 60, max_requests: int = 100) -> None:
        self._url = url
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self._client = None

    async def _get_client(self) -> Any:
        if self._client is None:
            import redis.asyncio as redis
            self._client = redis.from_url(self._url, decode_responses=True)
        return self._client

    async def is_allowed(self, client_id: str) -> bool:
        client = await self._get_client()
        key = f"rate_limit:{client_id}"
        now = time.time()
        window_start = now - self.window_seconds

        pipe = client.pipeline()
        await pipe.zremrangebyscore(key, min=0, max=window_start)
        await pipe.zadd(key, {str(now): now})
        await pipe.zcard(key)
        await pipe.expire(key, self.window_seconds)
        results = await pipe.execute()
        current_count = results[2]

        if current_count >= self.max_requests:
            logger.warning(
                "Rate limit exceeded for %s: %d requests in %ds window",
                client_id,
                current_count,
                self.window_seconds,
            )
            return False

        return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding window rate limiter.

    Uses Redis when available, falls back to in-memory for single-process dev.
    Configure via:
    - RATE_LIMIT_WINDOW_SECONDS: window size in seconds (default 60)
    - RATE_LIMIT_MAX_REQUESTS: max requests per window (default 100)
    - REDIS_ENABLED / REDIS_URL: enable Redis-backed limiter
    """

    def __init__(self, app, window_seconds: int = 60, max_requests: int = 100) -> None:
        super().__init__(app)
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self._limiter = self._create_limiter()

    def _create_limiter(self) -> Any:
        redis_url = getattr(settings, "redis_url", "") or ""
        redis_enabled = getattr(settings, "redis_enabled", False)
        if redis_enabled and redis_url:
            try:
                return RedisRateLimiter(
                    url=redis_url,
                    window_seconds=self.window_seconds,
                    max_requests=self.max_requests,
                )
            except Exception:  # noqa: BLE001
                logger.debug("Redis rate limiter unavailable, falling back to in-memory", exc_info=True)
        return InMemoryRateLimiter(
            window_seconds=self.window_seconds,
            max_requests=self.max_requests,
        )

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        client_id = f"{client_ip}"

        if not await self._limiter.is_allowed(client_id):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Too many requests. Limit: {self.max_requests} per {self.window_seconds}s",
                    "retry_after": self.window_seconds,
                },
                headers={"Retry-After": str(self.window_seconds)},
            )

        return await call_next(request)
