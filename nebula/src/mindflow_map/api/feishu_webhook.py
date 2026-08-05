"""飞书 Webhook 回调端点 — 统一走 Gateway → Alpha-ID TwinBrain + AgentLoop"""

import asyncio
import hmac
import json
import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from mindflow_map.workflows.engine import WorkflowEngine

from fastapi import APIRouter, HTTPException, Request

from mindflow_map.api.feishu_sender import FeishuSender
from mindflow_map.config import settings

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
        # 安全修复：使用 hmac.compare_digest 防止时序攻击
        expected = settings.feishu_verification_token or ""
        if not hmac.compare_digest(token, expected):
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
        # 使用 create_task 而非 ensure_future，保留引用防止被 GC
        asyncio.create_task(_handle_im_message(event_data))

    return {"code": 0, "message": "ok"}


@router.post("/webhook/feishu/route")
async def feishu_route_command(request: Request):
    """运营指令路由 — 供 feishu-bot 等上游调用（复用 feishu_commands.py）

    请求体：{"text": "文案 商品=香薰 价格=59"}
    返回：
      非指令 → {"handled": false}
      指令   → {"handled": true, "reply": "..."}
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "invalid JSON")

    text = (body or {}).get("text", "")
    try:
        from mindflow_map.api.feishu_commands import route_command
        reply = await route_command(text)
    except Exception as e:
        logger.error("指令路由失败: %s", e, exc_info=True)
        return {"handled": False}

    if reply is None:
        return {"handled": False}
    return {"handled": True, "reply": reply}


async def _handle_im_message(event: Dict[str, Any]):
    """处理 im.message.receive_v1 事件

    路由逻辑：
      1. 运营指令（文案/视频/抖音/短剧/帮助）→ feishu_commands.route_command
      2. 其他消息 → 走 WorkflowEngine 自然语言意图识别
         - LLM/规则识别意图（文案/视频/抖音/短剧/地图/闲聊等）
         - 命中工具则执行，否则走 ChatTool 闲聊
    """
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

    logger.info("飞书消息 from=%s: %s", user_id, text)

    # ── 1. 运营指令路由（文案/视频/抖音/短剧/帮助） ──
    # 复用 feishu_commands.py；非指令返回 None 再走 WorkflowEngine 闲聊
    try:
        from mindflow_map.api.feishu_commands import route_command
        cmd_reply = await route_command(text)
    except Exception as e:
        logger.error("指令路由异常，回退 WorkflowEngine: %s", e)
        cmd_reply = None

    if cmd_reply is not None:
        if user_id:
            try:
                await _sender.send_text(user_id, cmd_reply)
            except Exception as e:
                logger.error("回复飞书消息失败: %s", e)
        return

    # ── 2. 走 WorkflowEngine 自然语言 ──
    try:
        engine = _get_workflow_engine()
        result = await engine.execute(text, user_id=user_id or "feishu_user")
        reply = result.get("text", "") or "嗯？"
    except Exception as e:
        logger.error("WorkflowEngine 执行失败: %s", e, exc_info=True)
        reply = "抱歉我暂时无法处理你的消息（系统错误）"

    # 回复消息
    if user_id and reply:
        try:
            await _sender.send_text(user_id, reply)
            logger.info("已回复飞书消息 to=%s", user_id)
        except Exception as e:
            logger.error("回复飞书消息失败: %s", e)


# ── WorkflowEngine 单例（避免每条消息重建引擎） ──
# WorkflowEngine 仅在 TYPE_CHECKING 下导入，注解必须用字符串形式避免运行时 NameError
_workflow_engine: Optional["WorkflowEngine"] = None


def _get_workflow_engine() -> "WorkflowEngine":
    global _workflow_engine
    if _workflow_engine is None:
        from mindflow_map.workflows.engine import WorkflowEngine
        _workflow_engine = WorkflowEngine()
        logger.info("WorkflowEngine 单例已创建")
    return _workflow_engine

