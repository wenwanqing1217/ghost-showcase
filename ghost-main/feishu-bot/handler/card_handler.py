"""卡片消息处理 — 交互卡片构建、发送、按钮回调"""

import json
import logging

import httpx

from auth.token_manager import TokenManager

logger = logging.getLogger("feishu-bot")


async def reply_card(token_mgr: TokenManager, http_client: httpx.AsyncClient,
                     chat_id: str, reply_msg_id: str, card: dict) -> None:
    """发送交互卡片消息（msg_type=interactive）"""
    token = await token_mgr.get_token()
    r = await http_client.post(
        "https://open.feishu.cn/open-apis/im/v1/messages",
        params={"receive_id_type": "chat_id"},
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "receive_id": chat_id,
            "msg_type": "interactive",
            "content": json.dumps(card, ensure_ascii=False),
        },
    )
    data = r.json()
    if data.get("code") != 0:
        logger.warning("卡片回复失败: %s", data)


def build_confirm_card(reply: str, title: str, content: str, chat_id: str) -> dict:
    """构建文案确认卡片：✅发布到抖音 / 🔄重写 / ❌取消"""
    import re
    sections = re.split(r"\n──────────\n", reply)
    douyin_section = next(
        (s for s in reversed(sections) if "🎬" in s or "抖音" in s), sections[-1]
    )
    body = douyin_section.strip()
    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "📝 文案已生成，确认发布？"},
            "template": "blue",
        },
        "elements": [
            {"tag": "div", "text": {"tag": "lark_md", "content": body}},
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "✅ 发布到抖音"},
                        "type": "primary",
                        "value": json.dumps(
                            {
                                "action": "publish",
                                "chat_id": chat_id,
                                "title": title,
                                "content": content,
                            },
                            ensure_ascii=False,
                        ),
                    },
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "🔄 重写"},
                        "type": "default",
                        "value": json.dumps(
                            {"action": "rewrite", "chat_id": chat_id},
                            ensure_ascii=False,
                        ),
                    },
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "❌ 取消"},
                        "type": "danger",
                        "value": json.dumps(
                            {"action": "cancel", "chat_id": chat_id},
                            ensure_ascii=False,
                        ),
                    },
                ],
            },
        ],
    }


async def handle_card_action(handler, event: dict) -> None:
    """处理交互卡片按钮回调（card.action.trigger）"""
    try:
        ev = event.get("event", {})
        action = ev.get("action", {})
        value = action.get("value", {})
        operator = ev.get("operator", {})
        open_id = operator.get("open_id", "")
        act = value.get("action", "")
        chat_id = value.get("chat_id", "") or open_id
        title = value.get("title", "")
        content = value.get("content", "")
        logger.info("卡片回调 [%s] action=%s", chat_id[:8], act)

        if act == "publish":
            if not title:
                await handler._reply_text(chat_id, "", "❌ 缺少发布内容，请重新生成文案")
                return
            handler._pending_publish.pop(chat_id, None)
            await handler._reply_text(
                chat_id, "", "📤 正在发布到抖音，请稍候（首次可能需要登录验证）..."
            )
            result = await handler._execute_douyin_publish(title, content)
            await handler._reply_text(chat_id, "", result)
        elif act == "rewrite":
            handler._pending_publish.pop(chat_id, None)
            await handler._reply_text(
                chat_id, "", "🔄 好的，请重新描述你的需求，例如：帮我写北欧风香薰的抖音文案"
            )
        elif act == "cancel":
            handler._pending_publish.pop(chat_id, None)
            await handler._reply_text(chat_id, "", "已取消发布，内容已丢弃。")
        else:
            logger.warning("未知卡片动作: %s", act)
    except Exception as e:
        logger.exception("卡片回调处理异常: %s", e)
