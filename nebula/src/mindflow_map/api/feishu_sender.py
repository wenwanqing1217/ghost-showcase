"""飞书消息发送器"""

import json
import httpx
from typing import Optional, Dict, Any
from mindflow_map.config import settings


class FeishuSender:
    """飞书消息发送器"""
    
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
        
        async with httpx.AsyncClient(timeout=30.0) as client:
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
        
        async with httpx.AsyncClient(timeout=30.0) as client:
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
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, params=params, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
