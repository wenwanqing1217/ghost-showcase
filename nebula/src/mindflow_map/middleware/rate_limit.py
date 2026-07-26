"""Rate limiting middleware — 基于 limits 库

替换了原有的手写 InMemoryRateLimiter + RedisRateLimiter（135 行 → 62 行）。
支持内存和 Redis 两种后端，自动降级，固定窗口策略。
slowapi 已引入作为附加依赖，未来可用于路由级 @limiter.limit() 装饰器。
"""

from __future__ import annotations

import logging

from limits import RateLimitItemPerSecond, storage
from limits.strategies import FixedWindowRateLimiter
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from mindflow_map.config import settings

logger = logging.getLogger(__name__)


def _create_limiter() -> FixedWindowRateLimiter:
    if settings.redis_url:
        try:
            redis_storage = storage.RedisStorage(settings.redis_url)
            logger.info("Rate limiter: Redis backend")
            return FixedWindowRateLimiter(redis_storage)
        except Exception:
            logger.warning("Redis rate limiter unavailable, falling back to in-memory")

    logger.info("Rate limiter: In-memory backend")
    return FixedWindowRateLimiter(storage.MemoryStorage())


_limiter = _create_limiter()
_rps = max(1, settings.rate_limit_max_per_window // max(1, settings.rate_limit_window_seconds))
_rate_limit = RateLimitItemPerSecond(_rps)


def _extract_client_ip(request: Request) -> str:
    """提取客户端真实 IP（支持反向代理场景）

    优先级：
    1. X-Forwarded-For（取第一个，即客户端原始 IP）
    2. X-Real-IP（Nginx 等常用）
    3. 直连 IP（request.client.host）
    """
    xff = request.headers.get("x-forwarded-for")
    if xff:
        # X-Forwarded-For: client, proxy1, proxy2
        return xff.split(",")[0].strip()

    x_real_ip = request.headers.get("x-real-ip")
    if x_real_ip:
        return x_real_ip.strip()

    return request.client.host or "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """全局限流中间件（基于 limits 库 FixedWindow 策略）"""

    async def dispatch(self, request: Request, call_next) -> Response:
        client_id = _extract_client_ip(request)

        try:
            if not _limiter.hit(_rate_limit, client_id):
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "rate_limit_exceeded",
                        "message": f"Too many requests. Limit: {settings.rate_limit_max_per_window} per {settings.rate_limit_window_seconds}s",
                        "retry_after": settings.rate_limit_window_seconds,
                    },
                    headers={"Retry-After": str(settings.rate_limit_window_seconds)},
                )
        except Exception as e:
            logger.error("Rate limiter error: %s", e)

        return await call_next(request)