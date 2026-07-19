"""
Alpha-ID Client with retry, concurrency, and caching.

提供对 Alpha-ID 服务的并发访问：
- tenacity 指数退避重试
- asyncio.gather 并发拉取 profile + memory
- 内存缓存（TTL）
- 结构化日志
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from mindflow_map.config import settings

logger = logging.getLogger(__name__)


@dataclass
class _CacheEntry:
    """单条缓存记录。"""

    value: Any
    expire_at: float  # unix timestamp


class AlphaIDClient:
    """Alpha-ID 用户画像 / 记忆服务客户端。"""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        cache_ttl: float = 300.0,
        timeout: float = 10.0,
        max_retries: int = 3,
    ) -> None:
        self._base_url = (base_url or getattr(settings, "alpha_id_api_url", "")).rstrip("/")
        self._api_key = api_key or getattr(settings, "alpha_id_api_key", "")
        self._cache_ttl = cache_ttl
        self._timeout = timeout
        self._max_retries = max_retries

        # 内存缓存：key -> _CacheEntry
        self._cache: dict[str, _CacheEntry] = {}

        if not self._base_url or not self._api_key:
            logger.warning(
                "Alpha-ID client initialized without base_url or api_key; calls will be skipped."
            )

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    async def get_user_context(self, user_id: str) -> dict[str, Any]:
        """并发拉取用户画像和记忆，返回合并后的上下文。"""
        if not self._base_url or not self._api_key:
            return {}

        cache_key = f"user_context:{user_id}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            logger.debug("Alpha-ID cache hit for %s", user_id)
            return cached

        logger.info("Fetching Alpha-ID context for %s", user_id)
        try:
            profile, memory = await asyncio.gather(
                self._fetch("/profile", user_id),
                self._fetch("/memory", user_id),
            )
        except Exception as exc:
            logger.error("Alpha-ID concurrent fetch failed for %s: %s", user_id, exc)
            return {}

        context = {
            "profile": profile or {},
            "memory": memory or {},
            "fetched_at": time.time(),
        }
        self._set_cache(cache_key, context)
        return context

    async def health_check(self) -> bool:
        """检查 Alpha-ID 服务是否可达。"""
        if not self._base_url or not self._api_key:
            return False
        try:
            await self._fetch("/health", "_health")
            return True
        except Exception as exc:
            logger.warning("Alpha-ID health check failed: %s", exc)
            return False

    async def save_memory(
        self,
        user_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """保存用户记忆。"""
        if not self._base_url or not self._api_key:
            return
        payload = {
            "user_id": user_id,
            "content": content,
            "metadata": metadata or {},
        }
        try:
            await self._post("/memory", payload)
        except Exception as exc:
            logger.error("Alpha-ID save_memory failed for %s: %s", user_id, exc)

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """带重试的 HTTP POST。"""
        url = f"{self._base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        async for attempt in AsyncRetrying(
            retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
            stop=stop_after_attempt(self._max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            reraise=True,
        ):
            with attempt:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                    return response.json()
        return {}

    # ------------------------------------------------------------------
    # 底层 HTTP
    # ------------------------------------------------------------------

    async def _fetch(self, path: str, user_id: str) -> dict[str, Any]:
        """带重试的单次 HTTP GET。"""
        url = f"{self._base_url}{path}"
        headers = {"Authorization": f"Bearer {self._api_key}"}
        params: dict[str, Any] = {"user_id": user_id}

        async for attempt in AsyncRetrying(
            retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
            stop=stop_after_attempt(self._max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            reraise=True,
        ):
            with attempt:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.get(url, headers=headers, params=params)
                    response.raise_for_status()
                    return response.json()
        return {}

    # ------------------------------------------------------------------
    # 缓存
    # ------------------------------------------------------------------

    def _get_cache(self, key: str) -> dict[str, Any] | None:
        entry = self._cache.get(key)
        if entry is None:
            return None
        if time.time() > entry.expire_at:
            del self._cache[key]
            return None
        return entry.value

    def _set_cache(self, key: str, value: dict[str, Any]) -> None:
        self._cache[key] = _CacheEntry(
            value=value, expire_at=time.time() + self._cache_ttl
        )

    def invalidate(self, user_id: str | None = None) -> None:
        """清除缓存。传入 user_id 则仅清除该用户；否则全部清除。"""
        if user_id is None:
            self._cache.clear()
            return
        prefix = f"user_context:{user_id}"
        keys_to_delete = [k for k in self._cache if k.startswith(prefix)]
        for k in keys_to_delete:
            del self._cache[k]
