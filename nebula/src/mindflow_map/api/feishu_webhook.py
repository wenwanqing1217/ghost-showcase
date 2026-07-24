"""飞书 Webhook 回调端点（替代 WS 长连接方案）"""

import hashlib
import json
import logging
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException

from mindflow_map.config import settings
from mindflow_map.core.engine_registry import get_workflow_engine
from mindflow_map.api.feishu_sender import FeishuSender


logger = logging.getLogger(__name__)

router = APIRouter()
_sender = FeishuSender()


@router.post("/webhook/feishu")
async def feishu_webhook(request: Request):
    """飞书事件回调入口"""
    body = await request.body()
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(400, "invalid JSON")

    # 飞书 URL 验证挑战
    challenge = data.get("challenge")
    if challenge is not None:
        token = data.get("token", "")
        if token != settings.feishu_verification_token:
            raise HTTPException(403, "token mismatch")
        return {"challenge": challenge}

    # 加密事件解密
    encrypt = data.get("encrypt")
    if encrypt:
        if not settings.feishu_encrypt_key:
            logger.warning("收到加密事件但未配置 encrypt_key")
            return {"code": 0}
        try:
            from lark_oapi.core.utils import AESCipher
            plaintext = AESCipher(settings.feishu_encrypt_key).decrypt_str(encrypt)
            data = json.loads(plaintext)
        except Exception as e:
            logger.error("飞书事件解密失败: %s", e)
            raise HTTPException(400, "decrypt failed")

    # 解析事件
    header = data.get("header", {})
    event_type = header.get("event_type", "")
    event_data = data.get("event", {})

    logger.info("收到飞书事件: %s", event_type)

    if event_type == "im.message.receive_v1":
        # 异步处理消息，不阻塞回调响应
        import asyncio
        asyncio.ensure_future(_handle_im_message(event_data))

    return {"code": 0, "message": "ok"}


async def _handle_im_message(event: Dict[str, Any]):
    """处理 im.message.receive_v1 事件"""
    message = event.get("message", {})
    msg_type = message.get("message_type", "")

    if msg_type != "text":
        return

    # 提取文本内容
    raw_content = message.get("content", "")
    try:
        content_data = json.loads(raw_content) if isinstance(raw_content, str) else raw_content
        text = content_data.get("text", "")
    except (json.JSONDecodeError, TypeError):
        text = str(raw_content)

    if not text:
        return

    # 提取发送者
    sender = event.get("sender", {})
    sender_id_info = sender.get("sender_id", {})
    user_id = sender_id_info.get("user_id", "") or sender_id_info.get("open_id", "")
    chat_id = message.get("chat_id", "")

    logger.info("飞书消息 from=%s: %s", user_id, text)

    try:
        engine = get_workflow_engine()
        result = await engine.execute(text, user_id=user_id or "feishu_user")
        reply = result.get("text", str(result))
    except Exception as e:
        logger.error("工作流引擎执行失败: %s", e)
        reply = "抱歉，处理消息时出错了"

    # 回复消息
    if user_id:
        try:
            await _sender.send_text(user_id, reply)
            logger.info("已回复飞书消息 to=%s", user_id)
        except Exception as e:
            logger.error("回复飞书消息失败: %s", e)
