"""飞书消息发送器 — 复用类级别共享 httpx 客户端，避免每请求创建连接池"""

import json
import logging
from typing import Optional, Dict, Any

import httpx

from mindflow_map.config import settings

logger = logging.getLogger(__name__)


class FeishuSender:
    """飞书消息发送器 — 所有实例共享一个 httpx.AsyncClient（连接池复用）"""

    # 类级别共享客户端，所有实例复用
    _shared_client: Optional[httpx.AsyncClient] = None

    @classmethod
    def _get_shared_client(cls) -> httpx.AsyncClient:
        if cls._shared_client is None:
            cls._shared_client = httpx.AsyncClient(
                timeout=30.0,
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            )
        return cls._shared_client

    @classmethod
    async def close_shared_client(cls) -> None:
        """应用关闭时释放共享客户端"""
        if cls._shared_client:
            await cls._shared_client.aclose()
            cls._shared_client = None

    def __init__(self):
        self.app_id = settings.feishu_app_id
        self.app_secret = settings.feishu_app_secret
        self._tenant_access_token: Optional[str] = None

    async def _get_tenant_access_token(self) -> str:
        """获取飞书 tenant_access_token（带缓存）"""
        if self._tenant_access_token:
            return self._tenant_access_token

        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret,
        }

        client = self._get_shared_client()
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        if data.get("code") != 0:
            raise Exception(f"获取飞书 token 失败: {data}")

        self._tenant_access_token = data["tenant_access_token"]
        return self._tenant_access_token

    async def send_text(self, user_id: str, text: str) -> Dict[str, Any]:
        """发送文本消息（text 为纯文本，自动包装为飞书格式）"""
        token = await self._get_tenant_access_token()
        url = "https://open.feishu.cn/open-apis/im/v1/messages"
        params = {"receive_id_type": "user_id"}
        payload = {
            "receive_id": user_id,
            "msg_type": "text",
            "content": json.dumps({"text": text}, ensure_ascii=False),
        }
        headers = {"Authorization": f"Bearer {token}"}

        client = self._get_shared_client()
        response = await client.post(url, params=params, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    async def send_card(self, user_id: str, card: Dict[str, Any]) -> Dict[str, Any]:
        """发送卡片消息"""
        token = await self._get_tenant_access_token()
        url = "https://open.feishu.cn/open-apis/im/v1/messages"
        params = {"receive_id_type": "user_id"}
        payload = {
            "receive_id": user_id,
            "msg_type": "interactive",
            "content": json.dumps(card, ensure_ascii=False),
        }
        headers = {"Authorization": f"Bearer {token}"}

        client = self._get_shared_client()
        response = await client.post(url, params=params, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
