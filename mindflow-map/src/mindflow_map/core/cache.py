"""缓存层抽象，支持内存缓存与可选 Redis 后端。"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class CacheBackend(ABC):
    """缓存后端抽象。"""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        ...

    @abstractmethod
    async def clear(self) -> None:
        ...


class InMemoryCache(CacheBackend):
    """线程不安全的内存缓存，适用于单进程开发环境。"""

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    async def get(self, key: str) -> Any | None:
        return self._store.get(key)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        self._store[key] = value

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def clear(self) -> None:
        self._store.clear()


class RedisCache(CacheBackend):
    """Redis 缓存后端，适用于生产环境。"""

    def __init__(self, url: str = "redis://localhost:6379/0") -> None:
        self._url = url
        self._client = None

    async def _get_client(self) -> Any:
        if self._client is None:
            try:
                import redis.asyncio as redis

                self._client = redis.from_url(self._url, decode_responses=True)
            except ImportError as exc:
                raise RuntimeError("redis package required for RedisCache") from exc
        return self._client

    async def get(self, key: str) -> Any | None:
        client = await self._get_client()
        value = await client.get(key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        client = await self._get_client()
        raw = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
        if ttl:
            await client.setex(key, ttl, raw)
        else:
            await client.set(key, raw)

    async def delete(self, key: str) -> None:
        client = await self._get_client()
        await client.delete(key)

    async def clear(self) -> None:
        client = await self._get_client()
        await client.flushdb()


def get_cache() -> CacheBackend:
    """根据环境选择缓存后端。"""
    try:
        from mindflow_map.config import settings

        if getattr(settings, "redis_enabled", False) and getattr(settings, "redis_url", None):
            return RedisCache(settings.redis_url)
    except Exception:  # noqa: BLE001
        logger.debug("Falling back to in-memory cache", exc_info=True)
    return InMemoryCache()
