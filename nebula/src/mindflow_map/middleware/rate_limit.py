"""Rate limiting middleware — 基于 limits 库

替换了原有的手写 InMemoryRateLimiter + RedisRateLimiter（135 行 → 62 行）。
支持内存和 Redis 两种后端，自动降级，固定窗口策略。
slowapi 已引入作为附加依赖，未来可用于路由级 @limiter.limit() 装饰器。
"""

from __future__ import annotations

import ipaddress
import logging

from limits import RateLimitItemPerSecond, storage
from limits.strategies import FixedWindowRateLimiter
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from mindflow_map.config import settings

logger = logging.getLogger(__name__)

# 受信任的反向代理 CIDR（与 auth.py 保持一致）
_TRUSTED_PROXY_CIDRS = [
    "127.0.0.1/32",
    "::1/128",
    "10.0.0.0/8",
    "172.16.0.0/12",
    "192.168.0.0/16",
]


def _is_trusted_proxy(host: str) -> bool:
    """检查 IP 是否为受信任的反向代理"""
    try:
        addr = ipaddress.ip_address(host)
        return any(addr in ipaddress.ip_network(cidr, strict=False) for cidr in _TRUSTED_PROXY_CIDRS)
    except ValueError:
        return False


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


def reset_rate_limiter():
    """重置限流器（测试用）"""
    global _limiter
    _limiter = _create_limiter()


def _extract_client_ip(request: Request) -> str:
    """提取客户端真实 IP（支持反向代理场景）

    安全: 仅当请求来自受信任的反向代理（私有 IP）时才信任 X-Forwarded-For/X-Real-IP，
    防止外部攻击者通过伪造这些头部绕过限流。

    优先级：
    1. 受信任代理 + X-Forwarded-For（取第一个，即客户端原始 IP）
    2. 受信任代理 + X-Real-IP
    3. 直连 IP（request.client.host）
    """
    direct_host = request.client.host if request.client else "unknown"

    # 仅当直连 IP 是受信任代理时才使用头部中的 IP
    if _is_trusted_proxy(direct_host):
        xff = request.headers.get("x-forwarded-for")
        if xff:
            # X-Forwarded-For: client, proxy1, proxy2
            return xff.split(",")[0].strip()

        x_real_ip = request.headers.get("x-real-ip")
        if x_real_ip:
            return x_real_ip.strip()

    return direct_host


class RateLimitMiddleware(BaseHTTPMiddleware):
    """全局限流中间件（基于 limits 库 FixedWindow 策略）"""

    def __init__(
        self,
        app,
        exempt_paths: set[str] | None = None,
        window_seconds: int | None = None,
        max_requests: int | None = None,
    ):
        super().__init__(app)
        self._exempt_paths = exempt_paths or set()
        # 允许测试覆盖限流参数（创建独立限流器，避免全局状态污染）
        if window_seconds is not None and max_requests is not None:
            from limits import parse
            # 使用 parse 支持 "X per Y seconds" 格式
            self._override_rate = parse(f"{max_requests} per {window_seconds} seconds")
            self._override_limiter = _create_limiter()
        else:
            self._override_rate = None
            self._override_limiter = None

    def _get_rate(self):
        """获取当前限流速率（测试覆盖优先）"""
        return self._override_rate if self._override_rate is not None else _rate_limit

    def _get_limiter(self):
        """获取限流器（测试覆盖优先）"""
        return self._override_limiter if self._override_limiter is not None else _limiter

    async def dispatch(self, request: Request, call_next) -> Response:
        # 有测试覆盖参数时，强制执行限流（用于测试限流行为）
        if self._override_limiter is not None:
            client_id = _extract_client_ip(request)
            rate = self._get_rate()
            limiter = self._get_limiter()
            try:
                if not limiter.hit(rate, client_id):
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": "rate_limit_exceeded",
                            "message": "Too many requests. Limit exceeded",
                            "retry_after": 60,
                        },
                        headers={"Retry-After": "60"},
                    )
            except Exception as e:
                logger.error("Rate limiter error: %s", e)
            return await call_next(request)

        # 测试模式或豁免路径跳过限流
        if settings.rate_limit_disabled or request.url.path in self._exempt_paths:
            return await call_next(request)

        client_id = _extract_client_ip(request)
        rate = self._get_rate()
        limiter = self._get_limiter()

        try:
            if not limiter.hit(rate, client_id):
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
