"""WeChat 消息解析 — XML → 结构化消息

支持微信公众号/订阅号的消息回调解析。
仅解析文本消息类型，其他类型由调用方处理。
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class WechatMessage:
    """解析后的微信消息"""

    msg_type: str
    from_user: str
    to_user: str
    content: str
    msg_id: Optional[int] = None
    create_time: Optional[int] = None


def _parse_xml(raw: bytes) -> WechatMessage:
    """解析微信 XML 消息体

    Args:
        raw: 原始 XML 字节

    Returns:
        WechatMessage 结构化消息

    Raises:
        ValueError: XML 解析失败或缺少必要字段
    """
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ValueError(f"Invalid XML: {exc}") from exc

    def _text(tag: str) -> str:
        elem = root.find(tag)
        if elem is None or elem.text is None:
            return ""
        return elem.text.strip()

    msg_type = _text("MsgType")
    from_user = _text("FromUserName")
    to_user = _text("ToUserName")
    content = _text("Content")

    if not msg_type:
        raise ValueError("Missing MsgType in WeChat XML")
    if not from_user or not to_user:
        raise ValueError("Missing FromUserName/ToUserName in WeChat XML")

    # 可选字段
    msg_id_str = _text("MsgId")
    msg_id = int(msg_id_str) if msg_id_str.isdigit() else None

    create_time_str = _text("CreateTime")
    create_time = int(create_time_str) if create_time_str.isdigit() else None

    return WechatMessage(
        msg_type=msg_type,
        from_user=from_user,
        to_user=to_user,
        content=content,
        msg_id=msg_id,
        create_time=create_time,
    )
