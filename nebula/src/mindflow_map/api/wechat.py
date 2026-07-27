"""WeChat 消息解析 — XML → 结构化消息

支持微信公众号/订阅号的消息回调解析。
仅解析文本消息类型，其他类型由调用方处理。
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import logging
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional

import httpx
from fastapi import HTTPException

from mindflow_map.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Access Token 缓存（模块级，进程内单例）
# ---------------------------------------------------------------------------

_ACCESS_TOKEN_CACHE: dict = {"token": "", "expire_at": 0.0}


@contextlib.contextmanager
def fresh_token_cache():
    """测试用：隔离 token 缓存的上下文管理器（原地修改，保持引用有效）"""
    global _ACCESS_TOKEN_CACHE
    old_token = _ACCESS_TOKEN_CACHE["token"]
    old_expire = _ACCESS_TOKEN_CACHE["expire_at"]
    _ACCESS_TOKEN_CACHE["token"] = ""
    _ACCESS_TOKEN_CACHE["expire_at"] = 0.0
    try:
        yield
    finally:
        _ACCESS_TOKEN_CACHE["token"] = old_token
        _ACCESS_TOKEN_CACHE["expire_at"] = old_expire


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------


@dataclass
class WechatMessage:
    """解析后的微信消息"""

    msg_type: str
    from_user: str
    to_user: str
    content: str
    msg_id: Optional[int] = None
    create_time: Optional[int] = None


# ---------------------------------------------------------------------------
# XML 解析
# ---------------------------------------------------------------------------


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
    content_raw = _text("Content")
    content = content_raw if content_raw else None

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


# ---------------------------------------------------------------------------
# 签名校验
# ---------------------------------------------------------------------------


def _check_signature(signature: str, timestamp: str, nonce: str) -> bool:
    """校验微信服务器签名

    将 token、timestamp、nonce 三个参数进行字典序排序后拼接，
    做 SHA1 哈希，与传入的 signature 比较。

    Args:
        signature: 微信传入的签名
        timestamp: 时间戳
        nonce: 随机数

    Returns:
        签名是否匹配

    Raises:
        HTTPException 500: 服务端未配置 wechat_token
    """
    token = settings.wechat_token
    if not token:
        raise HTTPException(status_code=500, detail="WeChat token not configured")

    params = [token, timestamp, nonce]
    params.sort()
    expected = hashlib.sha1("".join(params).encode("utf-8")).hexdigest()
    return expected == signature


# ---------------------------------------------------------------------------
# XML 构造
# ---------------------------------------------------------------------------


def _build_xml(from_user: str, to_user: str, content: str) -> str:
    """构造微信被动回复 XML

    Args:
        from_user: 发送方账号（原接收方）
        to_user: 接收方账号（原发送方）
        content: 回复内容

    Returns:
        XML 字符串
    """
    # CDATA 中的 ]]> 需要转义，避免提前闭合 CDATA section
    safe_content = content.replace("]]>", "]]]]><![CDATA[>")
    create_time = int(time.time())
    return (
        "<xml>"
        f"<ToUserName><![CDATA[{to_user}]]></ToUserName>"
        f"<FromUserName><![CDATA[{from_user}]]></FromUserName>"
        f"<CreateTime>{create_time}</CreateTime>"
        "<MsgType><![CDATA[text]]></MsgType>"
        f"<Content><![CDATA[{safe_content}]]></Content>"
        "</xml>"
    )


# ---------------------------------------------------------------------------
# Access Token 管理
# ---------------------------------------------------------------------------


async def get_wechat_access_token() -> str:
    """获取微信全局 access_token（带缓存）

    先从进程内缓存读取，过期则调用微信 API 刷新。

    Returns:
        access_token 字符串

    Raises:
        HTTPException: 获取失败时抛出
    """
    global _ACCESS_TOKEN_CACHE

    # 缓存未过期直接返回
    if _ACCESS_TOKEN_CACHE["token"] and time.time() < _ACCESS_TOKEN_CACHE["expire_at"]:
        return _ACCESS_TOKEN_CACHE["token"]

    app_id = settings.wechat_app_id
    app_secret = settings.wechat_app_secret
    if not app_id or not app_secret:
        raise HTTPException(status_code=500, detail="WeChat app_id/secret not configured")

    url = "https://api.weixin.qq.com/cgi-bin/token"
    params = {
        "grant_type": "client_credential",
        "appid": app_id,
        "secret": app_secret,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.error("Failed to get WeChat access_token: %s", exc)
        raise HTTPException(status_code=502, detail="WeChat API request failed") from exc

    if "access_token" not in data:
        logger.error("WeChat API error response: %s", data)
        raise HTTPException(status_code=502, detail=f"WeChat API error: {data.get('errmsg', 'unknown')}")

    _ACCESS_TOKEN_CACHE["token"] = data["access_token"]
    # 提前 5 分钟过期，避免边界问题
    _ACCESS_TOKEN_CACHE["expire_at"] = time.time() + data.get("expires_in", 7200) - 300
    return data["access_token"]


def invalidate_wechat_access_token() -> None:
    """清除 access_token 缓存，强制下次调用时重新获取"""
    global _ACCESS_TOKEN_CACHE
    _ACCESS_TOKEN_CACHE["token"] = ""
    _ACCESS_TOKEN_CACHE["expire_at"] = 0.0
