"""Platform event subscription handlers for Feishu and WeChat."""

from __future__ import annotations

import datetime
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel

from mindflow_map.schemas.events import (
    BaseEvent,
    FeishuMessageEvent,
    WechatMessageEvent,
)
from mindflow_map.workflows.engine import WorkflowEngine

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class FeishuCallbackRequest(BaseModel):
    """Feishu event subscription callback body."""

    challenge: Optional[str] = None
    token: Optional[str] = None
    type: str
    event: Dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Event builders
# ---------------------------------------------------------------------------


def _build_feishu_message_event(event_id: str, payload: Dict[str, Any]) -> FeishuMessageEvent:
    # The handler passes body.event directly; Feishu message/sender live at the top level.
    message = payload.get("message", {})
    sender = payload.get("sender", {})
    sender_id = sender.get("sender_id", {}).get("user_id", "")
    content = message.get("content", "")
    if isinstance(content, str):
        try:
            import json
            parsed = json.loads(content)
            content = parsed.get("text", content)
        except (json.JSONDecodeError, AttributeError):
            pass
    return FeishuMessageEvent(
        event_id=event_id,
        payload=payload,
        source="feishu_ws",
        message_id=message.get("message_id", ""),
        chat_id=message.get("chat_id", ""),
        sender_id=sender_id,
        text=content,
    )


def _build_wechat_message_event(
    from_user: str,
    to_user: str,
    content: str,
    msg_id: Optional[int] = None,
    create_time: Optional[int] = None,
) -> WechatMessageEvent:
    event_id = f"wx_{msg_id or int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)}"
    return WechatMessageEvent(
        event_id=event_id,
        payload={"FromUserName": from_user, "ToUserName": to_user, "Content": content},
        source="wechat_http",
        from_user=from_user,
        to_user=to_user,
        content=content,
        msg_id=msg_id,
        create_time=create_time or int(datetime.datetime.now(datetime.timezone.utc).timestamp()),
    )


# ---------------------------------------------------------------------------
# Workflow dispatch helper
# ---------------------------------------------------------------------------


async def _dispatch_to_workflow_engine(event: BaseEvent, engine: WorkflowEngine) -> Dict[str, Any]:
    if isinstance(event, FeishuMessageEvent):
        text = event.text
        user_id = event.sender_id or event.chat_id
    elif isinstance(event, WechatMessageEvent):
        text = event.content
        user_id = event.from_user
    else:
        raise ValueError(f"Unsupported event type for workflow execution: {event.event_type}")

    if not text:
        return {"skipped": True, "reason": "empty_text"}

    return await engine.execute(text=text, user_id=user_id)


# ---------------------------------------------------------------------------
# Feishu callback
# ---------------------------------------------------------------------------


@router.post("/feishu")
async def feishu_event_subscription(
    request: Request,
    body: FeishuCallbackRequest,
):
    """
    Feishu event subscription callback.

    - `challenge` 响应用于 URL 验证；
    - 其余事件经处理后投递到内部 event bus（当前同步执行）。
    """
    if body.type == "url_verification":
        return {"challenge": body.challenge}

    if body.type != "event_callback":
        raise HTTPException(status_code=400, detail="unsupported callback type")

    event_type = body.event.get("type", "")
    event_id = body.event.get("uuid", "unknown")
    engine: WorkflowEngine | None = getattr(request.app.state, "workflow_engine", None)

    event: BaseEvent | None = None
    if event_type == "im.message.receive_v1":
        event = _build_feishu_message_event(event_id=event_id, payload=body.event)
    else:
        logger.info("Feishu event ignored: %s", event_type)
        return {"ignored": True}

    if engine is None:
        logger.error("WorkflowEngine not mounted; dropping event %s", event_id)
        raise HTTPException(status_code=500, detail="workflow_engine_not_initialized")

    try:
        result = await _dispatch_to_workflow_engine(event, engine)
        logger.info("Feishu event %s handled: %s", event_id, result)
        return {"handled": True, "result": result}
    except Exception as exc:  # noqa: BLE001
        logger.error("Feishu event %s failed: %s", event_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# WeChat callback
# ---------------------------------------------------------------------------


def _build_wechat_reply(from_user: str, to_user: str, content: str) -> str:
    safe = content.replace("]]>", "]]]]><![CDATA[>")
    return (
        "<xml>"
        f"<ToUserName><![CDATA[{to_user}]]></ToUserName>"
        f"<FromUserName><![CDATA[{from_user}]]></FromUserName>"
        f"<CreateTime>{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}</CreateTime>"
        "<MsgType><![CDATA[text]]></MsgType>"
        f"<Content><![CDATA[{safe}]]></Content>"
        "</xml>"
    )


@router.post("/wechat")
async def wechat_event_subscription(
    request: Request,
    signature: str = Query(...),
    timestamp: str = Query(...),
    nonce: str = Query(...),
    echostr: Optional[str] = Query(None),
):
    """
    WeChat event subscription callback.

    支持：
    - 服务器验证（`echostr` 存在时直接返回）；
    - 文本消息事件：解析 XML 后转交 WorkflowEngine。
    """
    if echostr is not None:
        return Response(content=echostr, media_type="text/plain")

    raw = await request.body()
    try:
        from mindflow_map.api.wechat import _parse_xml
        msg = _parse_xml(raw)
    except Exception as exc:
        logger.warning("WeChat XML parse failed: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid XML") from exc

    if msg.msg_type != "text" or not msg.content:
        reply = _build_wechat_reply(msg.from_user, msg.to_user, "目前只支持文字消息。")
        return Response(content=reply, media_type="application/xml")

    event = _build_wechat_message_event(
        from_user=msg.from_user,
        to_user=msg.to_user,
        content=msg.content,
        msg_id=msg.msg_id,
        create_time=msg.create_time,
    )

    engine: WorkflowEngine | None = getattr(request.app.state, "workflow_engine", None)
    if engine is None:
        logger.error("WorkflowEngine not mounted; dropping wechat event")
        raise HTTPException(status_code=500, detail="workflow_engine_not_initialized")

    try:
        result = await _dispatch_to_workflow_engine(event, engine)
        text = result.get("text") if isinstance(result, dict) else str(result)
    except Exception as exc:  # noqa: BLE001
        logger.error("WeChat event failed: %s", exc)
        text = "处理你的消息时出错了，请稍后再试。"

    reply = _build_wechat_reply(msg.from_user, msg.to_user, text)
    return Response(content=reply, media_type="application/xml")
