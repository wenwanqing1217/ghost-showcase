"""飞书渠道适配器 — 实现 ChannelAdapter 接口

TERM: FeishuChannelAdapter — 飞书 ChannelAdapter 实现

将 FeishuBotHandler 的业务能力包装成统一的 ChannelAdapter 接口，
供 OrchestratorEngine 或其他框架调用。
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from channel_adapter import ChannelAdapter

logger = logging.getLogger("feishu-bot")


class FeishuChannelAdapter(ChannelAdapter):
    """飞书渠道适配器

    封装 FeishuBotHandler，提供统一的 ChannelAdapter 接口。
    入站消息 → handler.handle_event()
    出站消息 → handler._reply_text() / reply_card()
    """

    def __init__(self, handler, event_publisher=None):
        self._handler = handler
        self._event_publisher = event_publisher

    async def receive(self, sender_id: str, text: str, **kwargs: Any) -> None:
        """接收飞书消息，委托给 handler 处理"""
        event = kwargs.get("event", {})
        if not event:
            # 构造最小事件结构供 handler.handle_event 使用
            chat_id = kwargs.get("chat_id", sender_id)
            msg_id = kwargs.get("msg_id", "")
            msg_type = kwargs.get("msg_type", "text")
            event = {
                "type": "im.message.receive_v1",
                "header": {"event_id": msg_id},
                "event": {
                    "message": {
                        "message_id": msg_id,
                        "chat_id": chat_id,
                        "sender": {
                            "sender_id": {"open_id": sender_id}
                        },
                        "msg_type": msg_type,
                        "content": {"text": text},
                    }
                },
            }
        await self._handler.handle_event(event)

    async def send(self, recipient_id: str, content: str, **kwargs: Any) -> None:
        """发送文本消息到飞书"""
        await self._handler._reply_text(
            recipient_id, kwargs.get("reply_msg_id", ""), content
        )
        # 发布出站事件
        if self._event_publisher:
            asyncio.create_task(self._event_publisher.emit(
                "social.message",
                {"chat_id": recipient_id, "direction": "outbound", "content": content[:500]},
            ))

    def channel_name(self) -> str:
        return "feishu"
