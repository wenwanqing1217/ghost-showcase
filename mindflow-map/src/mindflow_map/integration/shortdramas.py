"""短剧平台内容预审集成客户端"""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import logging
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import httpx
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from mindflow_map.config import settings

logger = logging.getLogger(__name__)


class ShortDramasClient:
    """短剧平台内容预审 API 客户端"""

    def __init__(self):
        self.api_url = settings.shortdramas_api_url.rstrip("/") if settings.shortdramas_api_url else ""
        self.api_key = settings.shortdramas_api_key or ""
        self.webhook_secret = settings.shortdramas_webhook_secret or ""
        # 复用 httpx 连接池
        self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        """释放 httpx 连接池"""
        await self._client.aclose()

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _sign_payload(self, payload: bytes) -> str:
        """使用 webhook_secret 对 payload 进行 HMAC-SHA256 签名（供回调验证使用）"""
        if not self.webhook_secret:
            return ""
        return hmac.new(
            self.webhook_secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def _validate_url(url: str) -> None:
        """
        校验目标 URL 安全性，防止 SSRF：
        - 强制 HTTPS
        - 禁止 localhost / 链路本地 / 私有网段
        """
        parsed = urlparse(url)
        if parsed.scheme != "https":
            raise ValueError(f"仅允许 HTTPS 目标，当前: {parsed.scheme}")

        hostname = (parsed.hostname or "").lower()
        if not hostname:
            raise ValueError("URL 缺少 hostname")

        # 解析 IP，覆盖 IPv4/IPv6 的私有/本地地址
        try:
            addr = ipaddress.ip_address(hostname)
        except ValueError:
            # 域名无法直接解析为 IP，放行（依赖 DNS 结果）
            return

        if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
            raise ValueError(f"禁止请求内网地址: {hostname}")

    async def _request(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """发送 HTTP 请求，带重试机制"""
        if not self.api_url:
            return {
                "success": False,
                "error": "SHORTDRAMAS_API_URL 未配置",
                "demo": True,
            }

        url = f"{self.api_url}{path}"
        self._validate_url(url)
        async for attempt in AsyncRetrying(
            retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            reraise=True,
        ):
            with attempt:
                response = await self._client.request(
                    method,
                    url,
                    json=payload,
                    headers=self._headers(),
                )
                response.raise_for_status()
                return response.json()

        return {"success": False, "error": "unknown"}

    async def submit_precheck(
        self,
        title: str,
        content: str,
        content_type: str = "video",
        callback_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        提交内容预审
        
        返回结构：
        {
            "success": true/false,
            "job_id": "唯一任务ID",
            "status": "pending|scanning|approved|rejected|manual_review",
            "ai_scan_result": {...},
            "platform_status": "queued|processing|done",
            "message": "..."
        }
        """
        payload = {
            "title": title,
            "content": content,
            "content_type": content_type,
        }
        if callback_url:
            payload["callback_url"] = callback_url

        result = await self._request("POST", "/api/v1/precheck/submit", payload)
        
        # 标准化返回
        if "demo" in result:
            return result
            
        return {
            "success": result.get("success", False),
            "job_id": result.get("job_id", ""),
            "status": result.get("status", "pending"),
            "ai_scan_result": result.get("ai_scan_result"),
            "platform_status": result.get("platform_status"),
            "message": result.get("message", ""),
        }

    async def query_precheck(self, job_id: str) -> Dict[str, Any]:
        """查询预审任务状态"""
        result = await self._request("GET", f"/api/v1/precheck/query/{job_id}")
        
        if "demo" in result:
            return result
            
        return {
            "success": result.get("success", False),
            "job_id": job_id,
            "status": result.get("status", "unknown"),
            "ai_scan_result": result.get("ai_scan_result"),
            "platform_status": result.get("platform_status"),
            "platform_result": result.get("platform_result"),
            "message": result.get("message", ""),
        }

    async def verify_callback(self, payload: bytes, signature: str) -> bool:
        """验证回调请求签名"""
        expected = self._sign_payload(payload)
        if not expected:
            return False
        return hmac.compare_digest(expected, signature)


class AIContentScanner:
    """本地 AI 内容预扫描器（在提交到平台前先做一轮快速检查）"""

    def __init__(self):
        try:
            from mindflow_map.ai.llm import LLMClient
            self.llm = LLMClient()
            self._available = True
        except Exception:
            self._available = False

    async def scan(self, title: str, content: str) -> Dict[str, Any]:
        """
        对内容进行 AI 快速扫描
        
        返回：
        {
            "risk_level": "safe|warning|blocked",
            "violations": ["violation_type", ...],
            "suggestions": ["suggestion", ...],
            "summary": "扫描摘要"
        }
        """
        if not self._available:
            return {
                "risk_level": "unknown",
                "violations": [],
                "suggestions": ["AI 扫描器未配置（OPENAI_API_KEY 未设置）"],
                "summary": "跳过本地 AI 扫描",
            }

        prompt = f"""你是一个短剧内容合规预审助手。请对以下短剧内容进行快速合规扫描：

标题：{title}
内容：{content[:2000]}

请检查是否存在以下违规类型：
1. 色情低俗内容
2. 暴力血腥内容
3. 政治敏感内容
4. 侵犯版权/抄袭
5. 虚假宣传/欺诈
6. 其他违规内容

请以 JSON 格式返回：
{{
    "risk_level": "safe|warning|blocked",
    "violations": ["violation_type", ...],
    "suggestions": ["suggestion", ...],
    "summary": "扫描摘要（50字以内）"
}}"""

        try:
            result_text = await self.llm.chat(
                messages=[
                    {"role": "system", "content": "你是短剧内容合规预审助手，只返回 JSON，不要其他内容。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=256,
            )
            
            # 解析 JSON
            result_text = result_text.strip()
            if result_text.startswith("```"):
                result_text = result_text.split("```", 2)[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            return json.loads(result_text)
        except Exception as e:
            logger.error("AI content scan failed: %s", e)
            return {
                "risk_level": "unknown",
                "violations": [],
                "suggestions": [f"AI 扫描失败: {e}"],
                "summary": "扫描失败，建议人工复核",
            }
