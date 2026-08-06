"""平台路由器 — 统一管理 nebula/gateway 外部调用

FeishuBotHandler 不再硬编码 NEBULA_URL / GATEWAY_URL，
所有跨服务调用走这里，改端点只需改一处。
"""

import asyncio
import json
import logging
import uuid

import httpx

from config import GATEWAY_URL, NEBULA_URL

logger = logging.getLogger("feishu-bot")


class PlatformRouter:
    """封装对外部平台（nebula / gateway）的所有 HTTP 调用。"""

    def __init__(self, nebula_url: str = NEBULA_URL, gateway_url: str = GATEWAY_URL):
        self._nebula = nebula_url
        self._gateway = gateway_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=10)

    async def close(self):
        await self._client.aclose()

    # ── 运营指令路由 ──

    async def route_operation(self, text: str) -> tuple[str | None, dict | None]:
        """运营指令路由（文案/视频/抖音/短剧）

        调用 nebula /api/v1/webhook/feishu/route
        返回 (reply_text, action_dict | None)，未命中返回 (None, None)
        """
        try:
            resp = await asyncio.wait_for(
                self._client.post(
                    f"{self._nebula}/api/v1/webhook/feishu/route",
                    json={"text": text},
                    timeout=90,
                ),
                timeout=100,
            )
        except Exception as e:
            logger.warning("运营指令路由失败: %s", e)
            return None, None

        if resp.status_code != 200:
            logger.info("运营指令路由 HTTP %s", resp.status_code)
            return None, None

        data = resp.json()
        if not data.get("handled"):
            return None, None

        reply = data.get("reply") or ""
        action = None
        if "【标题】" in reply and "【正文】" in reply:
            action = self._extract_copy_action(reply)
        return reply, action

    # ── 抖音发布 ──

    async def publish_douyin(self, title: str, content: str) -> str:
        """发布图文到抖音创作者中心"""
        text = f"抖音 标题={title} 内容={content}"
        try:
            resp = await self._client.post(
                f"{self._nebula}/api/v1/webhook/feishu/route",
                json={"text": text},
                timeout=180,
            )
            data = resp.json()
            if not data.get("handled"):
                return f"❌ 发布失败：未识别为发布指令\n原始返回：{str(data)[:200]}"
            return data.get("reply") or "发布结果未知"
        except Exception as e:
            logger.warning("抖音发布异常: %s", e)
            return f"❌ 抖音发布出错：{str(e)[:200]}"

    # ── 视频生成 ──

    async def generate_video(
        self,
        topic: str,
        aspect: str = "9:16",
        language: str = "zh",
        concat_mode: str = "random",
        tenant_id: str = "feishu-bot",
    ) -> tuple[str | None, str | None]:
        """触发视频生成，返回 (task_id, error)。成功时 error=None。"""
        try:
            resp = await self._client.post(
                f"{self._gateway}/v1/content/video/generate",
                headers={
                    "Content-Type": "application/json",
                    "X-Tenant-ID": tenant_id,
                    "X-Request-ID": str(uuid.uuid4()),
                },
                json={
                    "video_subject": topic,
                    "video_aspect": aspect,
                    "video_language": language,
                    "video_concat_mode": concat_mode,
                    "paragraph_number": 1,
                    "n_threads": 2,
                    "video_source": "local",
                },
            )
            data = resp.json()
            if not data.get("success"):
                return None, data.get("error", "unknown error")
            task_id = data.get("data", {}).get("task_id")
            return task_id, None
        except Exception as e:
            logger.warning("视频生成请求失败: %s", e)
            return None, str(e)

    async def get_video_status(self, task_id: str, tenant_id: str = "feishu-bot") -> dict:
        """查询视频生成状态，返回 task_data dict"""
        resp = await self._client.get(
            f"{self._gateway}/v1/content/video/status/{task_id}",
            headers={
                "X-Tenant-ID": tenant_id,
                "X-Request-ID": str(uuid.uuid4()),
            },
        )
        data = resp.json()
        if not data.get("success"):
            return {}
        task_data = data.get("data", {})
        if isinstance(task_data, dict) and "data" in task_data:
            task_data = task_data["data"]
        return task_data

    # ── 工具方法 ──

    @staticmethod
    def _extract_copy_action(reply: str) -> dict | None:
        """从文案回复中提取 {title, content}（取最后一段平台文案）"""
        import re
        sections = re.split(r"\n──────────\n", reply)
        for sec in reversed(sections):
            if "【标题】" not in sec:
                continue
            m_title = re.search(r"【标题】(.+?)\n", sec)
            m_body = re.search(r"【正文】\n(.+?)(?:\n【标签】|\Z)", sec, re.S)
            if m_title and m_body:
                return {
                    "title": m_title.group(1).strip(),
                    "content": m_body.group(1).strip(),
                }
        return None
