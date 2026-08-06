"""事件处理 — 飞书消息主处理逻辑"""

import json
import logging
import os
import re

from config import (
    _PUBLISH_CONFIRM_WORDS,
    _PUBLISH_CANCEL_WORDS,
    NEBULA_URL,
    RATE_LIMIT_PER_MINUTE,
)
from state.memory import ConversationMemory
from state.rate_limiter import RateLimiter
from state.task_queue import TaskQueue

logger = logging.getLogger("feishu-bot")


def clean_mention(text: str) -> str:
    """去掉 @机器人 前缀（兼容飞书多种 @ 格式）"""
    text = re.sub(r"@_user_\d+\s*", "", text).strip()
    text = re.sub(r"@(ou_\w+|[\w-]{20,})\s*", "", text).strip()
    text = re.sub(r"<at.*?</at>", "", text).strip()
    return text


async def handle_event(handler, event: dict) -> None:
    """处理飞书事件（兼容 v2.0 schema）"""
    logger.info("handle_event called! event keys: %s", list(event.keys())[:5])

    # 兼容 v2.0 schema: event_type 在 header 中
    event_type = event.get("type") or event.get("header", {}).get("event_type", "")

    # 交互卡片按钮回调
    if event_type == "card.action.trigger":
        from handler.card_handler import handle_card_action
        await handle_card_action(handler, event)
        return

    if event_type != "im.message.receive_v1":
        logger.info("handle_event: skip event_type=%s", event_type)
        return

    # 跳过 bot 自己发出的消息
    sender = (
        event.get("event", {}).get("sender", {})
        or event.get("event", {}).get("message", {}).get("sender", {})
    )
    sid = sender.get("sender_id", sender)
    open_id = sid.get("open_id", "")
    if not open_id.startswith("ou_"):
        return

    header = event.get("header", {})
    event_id = header.get("event_id", "")
    if handler._is_duplicate(event_id):
        return

    msg = event.get("event", {}).get("message", {})
    msg_id = msg.get("message_id", "")
    chat_id = msg.get("chat_id", "")
    sender_event = event.get("event", {})
    sender_id = (
        sender_event.get("sender", {}).get("sender_id", {}).get("open_id", "")
        or msg.get("sender", {}).get("sender_id", {}).get("open_id", "")
    )
    msg_type = msg.get("msg_type", "") or msg.get("message_type", "")
    content_str = msg.get("content", "{}")

    # 解析消息内容
    try:
        content = json.loads(content_str)
    except json.JSONDecodeError:
        logger.warning("消息内容解析失败: %s", content_str[:100])
        return

    if msg_type == "text":
        text = content.get("text", "").strip()
    elif msg_type == "audio":
        text = content.get("text", "").strip()
        if not text:
            text = content.get("file_name", "[语音消息]").strip()
    else:
        await handler._reply_text(
            chat_id, msg_id, f"暂不支持 {msg_type} 类型消息，请发送文字或语音"
        )
        return

    if not text:
        return

    # 去掉 @bot 前缀
    text = clean_mention(text)
    logger.info("处理消息 [%s] type=%s: %s", chat_id[:8], msg_type, text[:60])

    # 限流检查
    if not handler.rate_limiter.allow(chat_id):
        await handler._reply_text(chat_id, msg_id, "⚠️ 请求过于频繁，请稍后再试")
        return

    # 处理 chat 命令
    if text.startswith("/"):
        if text.startswith("/video"):
            from handler.video_handler import handle_video_command
            await handle_video_command(handler, text, chat_id, msg_id)
            return
        reply = await _handle_command(handler, text, chat_id)
        if reply:
            await handler._reply_text(chat_id, msg_id, reply)
        return

    # 待确认发布：精确匹配确认/取消词
    if chat_id in handler._pending_publish:
        norm = text.strip().lower()
        if norm in _PUBLISH_CONFIRM_WORDS:
            pending = handler._pending_publish.pop(chat_id)
            await handler._reply_text(chat_id, msg_id, "📤 正在发布到抖音，请稍候（首次可能需要登录验证）...")
            result = await handler._execute_douyin_publish(
                pending.get("title", ""), pending.get("content", "")
            )
            await handler._reply_text(chat_id, msg_id, result)
            return
        if norm in _PUBLISH_CANCEL_WORDS:
            handler._pending_publish.pop(chat_id, None)
            await handler._reply_text(chat_id, msg_id, "已取消发布，内容已丢弃。")
            return

    # 运营指令路由（渠道助手：文案/视频/抖音/短剧）
    try:
        op_reply, op_action = await handler._try_operation_command(text)
    except Exception as e:
        logger.exception("运营指令路由异常: %s", e)
        op_reply, op_action = None, None
    if op_reply:
        if op_action:
            handler._pending_publish[chat_id] = op_action
            try:
                from handler.card_handler import reply_card, build_confirm_card
                await reply_card(
                    handler.token_mgr, handler._http_client, chat_id, msg_id,
                    build_confirm_card(op_reply, op_action["title"], op_action["content"], chat_id),
                )
                logger.info("文案确认卡片已发送 [%s]", chat_id[:8])
            except Exception as e:
                logger.exception("文案确认卡片发送失败: %s", e)
            return
        try:
            await handler._reply_text(chat_id, msg_id, op_reply)
            logger.info("运营指令回复完成 [%s] 长度=%s", chat_id[:8], len(op_reply))
        except Exception as e:
            logger.exception("运营指令回复发送失败: %s", e)
        return
    logger.info("运营指令未命中 [%s]: %s...", chat_id[:8], text[:50])

    # 处理正常消息（AI 闲聊）
    await _handle_chat(handler, text, chat_id, msg_id)


async def _handle_command(handler, text: str, chat_id: str) -> str | None:
    """处理 / 开头的命令"""
    parts = text.strip().split()
    cmd = parts[0].lower()

    if cmd == "/backend":
        if len(parts) == 1 or parts[1] == "list":
            current = handler.runner.get_backend(chat_id)
            lines = ["**可用后端：**"]
            from code_runner import BACKENDS
            for name, cfg in BACKENDS.items():
                mark = " ← 当前" if name == current else ""
                lines.append(f"  /backend {name} — {cfg['desc']}{mark}")
            return "\n".join(lines)

        elif len(parts) >= 2:
            target = parts[1]
            from code_runner import BACKENDS
            if target in BACKENDS:
                handler.runner.set_backend(chat_id, target)
                cfg = BACKENDS[target]
                return f"✅ 已切换到后端: **{target}**（{cfg['desc']}）"
            else:
                return f"❌ 后端 '{target}' 不存在，用 /backend list 查看可用后端"

    elif cmd == "/status":
        current = handler.runner.get_backend(chat_id)
        from code_runner import BACKENDS, MAX_CONCURRENT
        lines = [
            "**当前状态：**",
            f"  • 后端: {current}（{BACKENDS[current]['desc']}）",
            f"  • 并发: {MAX_CONCURRENT}",
        ]
        return "\n".join(lines)

    elif cmd == "/help":
        return (
            "**可用命令：**\n"
            "  /backend list    — 查看可用后端\n"
            "  /backend <名字>  — 切换到指定后端\n"
            "  /status          — 查看当前状态\n"
            "  /clear           — 清空当前会话的上下文记忆\n"
            "  /task list       — 查看待办任务\n"
            "  /video <主题>    — AI 生成视频（DeepSeek + MoneyPrinterTurbo）\n"
            "  /help            — 显示帮助\n\n"
            "直接发文字或语音消息，会自动用当前后端处理\n"
            "支持定时任务：\"明天9点帮我跑个脚本\"\n"
            "Bot 会自动记住最近 10 轮对话作为上下文"
        )

    elif cmd == "/clear":
        handler.conversation_memory.clear(chat_id)
        return "🧹 已清空当前会话的上下文记忆"

    elif cmd == "/task":
        if not handler._app or not handler._app.task_queue:
            return "任务队列未初始化"
        if len(parts) >= 2 and parts[1] == "list":
            pending = handler._app.task_queue.get_pending()
            if not pending:
                return "📭 没有待办任务"
            lines = ["**待办任务：**"]
            for t in pending[:10]:
                from datetime import datetime
                dt = datetime.fromtimestamp(t["execute_at"]).strftime("%m-%d %H:%M")
                lines.append(f"  • [{dt}] {t['prompt'][:40]}...")
            return "\n".join(lines)
        else:
            pending = handler._app.task_queue.get_pending()
            return f"待办任务: {len(pending)} 个"

    return None


async def _handle_chat(handler, text: str, chat_id: str, msg_id: str) -> None:
    """处理正常消息 — AI 闲聊"""
    backend_name = handler.runner.get_backend(chat_id)
    logger.info("收到消息 [%s] 后端=%s: %s...", chat_id[:8], backend_name, text[:50])

    # 记录用户消息到上下文记忆
    handler.conversation_memory.add(chat_id, "user", text)

    # 构建含历史上下文的 prompt
    context_prompt = handler.conversation_memory.build_context_prompt(chat_id, text)
    if context_prompt != text:
        logger.info(
            "为 [%s] 附加了 %d 条历史上下文",
            chat_id[:8],
            len(handler.conversation_memory._histories.get(chat_id, [])),
        )

    # 先回复"处理中"
    await handler._reply_text(chat_id, msg_id, "⏳ 正在处理，请稍候...")

    # 调用后端
    try:
        result = await handler.runner.run(context_prompt, chat_id=chat_id)
    except Exception as e:
        logger.exception("后端调用失败")
        result = f"❌ 处理出错: {str(e)[:200]}"

    # 记录助手回复到上下文记忆
    handler.conversation_memory.add(chat_id, "assistant", result[:3000])

    # 飞书消息有长度限制
    if len(result) > 14000:
        result = result[:13900] + "\n\n...（内容过长已截断）"

    logger.info("准备回复 [%s] 长度=%s", chat_id[:8], len(result))
    try:
        await handler._reply_text(chat_id, msg_id, result)
        logger.info("回复完成 [%s]", chat_id[:8])
    except Exception as e:
        logger.exception("回复发送失败: %s", e)
