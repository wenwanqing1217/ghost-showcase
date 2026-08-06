"""ChannelAdapter 接口定义

TERM: ChannelAdapter — 渠道适配器基类（飞书/Web/微信/Telegram）

每个渠道实现此接口，OrchestratorEngine 通过统一接口收发消息。
飞书实现见 FeishuChannelAdapter。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ChannelAdapter(ABC):
    """渠道适配器基类

    子类实现 receive() 处理入站消息，
    通过 send() 发送出站消息。
    """

    @abstractmethod
    async def receive(self, sender_id: str, text: str, **kwargs: Any) -> None:
        """接收来自渠道的消息，路由到后端处理

        Args:
            sender_id: 发送者标识（open_id / user_id 等）
            text: 消息文本内容
            **kwargs: 渠道特有字段（chat_id, msg_id, msg_type 等）
        """
        ...

    @abstractmethod
    async def send(self, recipient_id: str, content: str, **kwargs: Any) -> None:
        """向渠道用户发送消息

        Args:
            recipient_id: 接收者标识
            content: 消息内容
            **kwargs: 渠道特有参数（msg_type, card 等）
        """
        ...

    @abstractmethod
    def channel_name(self) -> str:
        """返回渠道名称（如 "feishu", "web", "wechat"）"""
        ...
