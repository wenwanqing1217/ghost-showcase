"""微信公众号消息入口 - 支持签名验证、文本消息、AccessToken 管理"""

import hashlib
import logging
import time
from typing import Optional
from xml.etree import ElementTree as ET

import httpx
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel
from starlette.responses import Response

from mindflow_map.config import settings
from mindflow_map.workflows.engine import WorkflowEngine

logger = logging.getLogger(__name__)

router = APIRouter()
workflow_engine = WorkflowEngine()

# ---------------------------------------------------------------------------
# WeChat Access Token 缓存
# ---------------------------------------------------------------------------

_ACCESS_TOKEN_CACHE: dict[str, str | float] = {"token": "", "expire_at": 0.0}


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------

class WechatMessage(BaseModel):
    """微信消息模型"""
    to_user: str
    from_user: str
    create_time: int
    msg_type: str
    content: Optional[str] = None
    msg_id: Optional[int] = None


# ---------------------------------------------------------------------------
# XML 解析 / 构造
# ---------------------------------------------------------------------------

def _parse_xml(body: bytes) -> WechatMessage:
    """解析微信 XML"""
    root = ET.fromstring(body)
    return WechatMessage(
        to_user=root.find("ToUserName").text or "",
        from_user=root.find("FromUserName").text or "",
        create_time=int(root.find("CreateTime").text or 0),
        msg_type=root.find("MsgType").text or "",
        content=root.find("Content").text if root.find("Content") is not None else None,
        msg_id=int(root.find("MsgId").text) if root.find("MsgId") is not None else None,
    )


def _build_xml(from_user: str, to_user: str, content: str) -> str:
    """构造微信回复 XML"""
    return (
        "<xml>"
        f"<ToUserName><![CDATA[{to_user}]]></ToUserName>"
        f"<FromUserName><![CDATA[{from_user}]]></FromUserName>"
        f"<CreateTime>{int(time.time())}</CreateTime>"
        f"<MsgType><![CDATA[text]]></MsgType>"
        f"<Content><![CDATA[{content}]]></Content>"
        "</xml>"
    )


# ---------------------------------------------------------------------------
# 签名校验
# ---------------------------------------------------------------------------

def _check_signature(signature: str, timestamp: str, nonce: str) -> bool:
    """校验微信签名（sha1(token, timestamp, nonce)，按字典序排序后拼接）"""
    token = settings.wechat_token
    if not token:
        # 未配置 token 时拒绝请求，而不是静默跳过验证
        logger.error("WECHAT_TOKEN 未配置，拒绝所有微信请求")
        raise HTTPException(status_code=500, detail="微信服务未配置：WECHAT_TOKEN 缺失")

    params = [token, timestamp, nonce]
    params.sort()
    sha1 = hashlib.sha1("".join(params).encode("utf-8")).hexdigest()
    return sha1 == signature


# ---------------------------------------------------------------------------
# Access Token 管理
# ---------------------------------------------------------------------------

async def get_wechat_access_token() -> str:
    """
    获取微信 Access Token，带缓存和自动刷新。
    缓存有效期 1.5 小时（微信官方 2 小时，提前刷新避免边界失效）。
    """
    now = time.time()
    cached_token = _ACCESS_TOKEN_CACHE.get("token", "")
    expire_at = _ACCESS_TOKEN_CACHE.get("expire_at", 0.0)

    if cached_token and now < expire_at:
        return cached_token

    app_id = settings.wechat_app_id
    app_secret = settings.wechat_app_secret
    if not app_id or not app_secret:
        raise HTTPException(status_code=500, detail="微信公众号未配置 AppID/AppSecret")

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
        logger.error("获取微信 Access Token 失败: %s", exc)
        raise HTTPException(status_code=502, detail="获取微信 Access Token 失败") from exc

    if "errcode" in data:
        logger.error("微信返回错误: %s", data)
        raise HTTPException(status_code=502, detail=f"微信 API 错误: {data.get('errmsg', '未知错误')}")

    token = data.get("access_token", "")
    expires_in = int(data.get("expires_in", 7200))

    _ACCESS_TOKEN_CACHE["token"] = token
    _ACCESS_TOKEN_CACHE["expire_at"] = now + expires_in - 300  # 提前 5 分钟过期

    logger.info("微信 Access Token 已刷新，有效期 %d 秒", expires_in)
    return token


def invalidate_wechat_access_token() -> None:
    """强制清除 Access Token 缓存（用于测试或手动刷新）。"""
    _ACCESS_TOKEN_CACHE["token"] = ""
    _ACCESS_TOKEN_CACHE["expire_at"] = 0.0


# ---------------------------------------------------------------------------
# 路由
# ---------------------------------------------------------------------------

@router.get("/")
async def wechat_verify(
    signature: str = Query(...),
    timestamp: str = Query(...),
    nonce: str = Query(...),
    echostr: str = Query(...),
):
    """微信服务器验证"""
    if not _check_signature(signature, timestamp, nonce):
        raise HTTPException(status_code=403, detail="Invalid signature")

    return Response(content=echostr, media_type="text/plain")


@router.post("/")
async def wechat_message(request: Request):
    """接收微信用户消息"""
    signature = request.query_params.get("signature", "")
    timestamp = request.query_params.get("timestamp", "")
    nonce = request.query_params.get("nonce", "")

    if not _check_signature(signature, timestamp, nonce):
        raise HTTPException(status_code=403, detail="Invalid signature")

    body = await request.body()
    try:
        msg = _parse_xml(body)
    except Exception as exc:
        logger.warning("微信 XML 解析失败: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid XML") from exc

    logger.info(
        "收到微信消息: from=%s type=%s content=%s",
        msg.from_user,
        msg.msg_type,
        (msg.content or "")[:50],
    )

    if msg.msg_type != "text" or not msg.content:
        reply = _build_xml(msg.to_user, msg.from_user, "目前只支持文字消息，请发文字给我。")
        return Response(content=reply, media_type="application/xml")

    try:
        result = await workflow_engine.execute(msg.content, user_id=msg.from_user)
        response_text = result.get("text", str(result))
    except Exception as exc:
        logger.exception("处理微信消息失败")
        response_text = "处理你的消息时出错了，请稍后再试。"

    reply_xml = _build_xml(msg.to_user, msg.from_user, response_text)
    return Response(content=reply_xml, media_type="application/xml")
