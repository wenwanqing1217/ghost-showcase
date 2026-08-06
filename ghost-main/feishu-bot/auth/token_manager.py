"""Token 管理 — 自动刷新飞书 tenant_access_token"""

import asyncio
import logging
import time

import httpx

from config import FEISHU_APP_ID, FEISHU_APP_SECRET

logger = logging.getLogger("feishu-bot")


class TokenManager:
    """自动刷新飞书 tenant_access_token，复用共享 HTTP 客户端。"""

    def __init__(self):
        self._token: str | None = None
        self._expires_at: float = 0
        self._lock = asyncio.Lock()
        self._client = httpx.AsyncClient(timeout=10)

    async def get_token(self) -> str:
        """获取有效 token，必要时自动刷新"""
        async with self._lock:
            if time.time() < self._expires_at - 60:
                return self._token
            await self._refresh()
            return self._token

    async def _refresh(self):
        r = await self._client.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET},
        )
        data = r.json()
        if data.get("code") != 0:
            raise RuntimeError(f"获取 token 失败: {data}")
        self._token = data["tenant_access_token"]
        self._expires_at = time.time() + data["expire"]
        logger.info("Token 已刷新，有效期 %s 秒", data["expire"])

    async def close(self):
        await self._client.aclose()
