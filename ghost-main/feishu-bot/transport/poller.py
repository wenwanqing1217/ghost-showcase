"""HTTP 轮询后备 — 当 WS 事件未到达时使用"""

import asyncio
import logging
import time

import httpx

from auth.token_manager import TokenManager

logger = logging.getLogger("feishu-bot")


class MessagePoller:
    """定时轮询飞书消息 API，用于 WS 事件未到达时的后备"""

    def __init__(self, token_mgr: TokenManager, handler):
        self.token_mgr = token_mgr
        self.handler = handler
        self._known_chats: set[str] = set()
        self._last_msg_times: dict[str, int] = {}
        # 从环境变量读取已知 chat_id（逗号分隔）
        from config import KNOWN_CHAT_IDS  # noqa: F401 — placeholder for env var
        extra = __import__("os").environ.get("KNOWN_CHAT_IDS", "").strip()
        if extra:
            for cid in extra.split(","):
                cid = cid.strip()
                if cid:
                    self._known_chats.add(cid)
                    self._last_msg_times[cid] = int(time.time() * 1000) - 30000
        logger.info("消息轮询: 已知 %s 个会话", len(self._known_chats))

    def add_chat(self, chat_id: str):
        if chat_id not in self._known_chats:
            self._known_chats.add(chat_id)
            self._last_msg_times[chat_id] = int(time.time() * 1000) - 30000
            logger.info("新增轮询会话: %s", chat_id[:12])

    async def poll_once(self):
        if not self._known_chats:
            return
        token = await self.token_mgr.get_token()
        async with httpx.AsyncClient(timeout=10) as client:
            for chat_id in list(self._known_chats):
                try:
                    check_time = int(time.time() * 1000)
                    last_time = self._last_msg_times.get(chat_id, 0)
                    r = await client.get(
                        "https://open.feishu.cn/open-apis/im/v1/messages",
                        params={
                            "container_id_type": "chat",
                            "container_id": chat_id,
                            "page_size": "50",
                            "sort_type": "ByCreateTimeDesc",
                        },
                        headers={"Authorization": f"Bearer {token}"},
                    )
                    data = r.json()
                    if data.get("code") != 0:
                        if "permission" in str(data) or "99991672" in str(data):
                            logger.warning(
                                "轮询 %s 失败(权限): %s",
                                chat_id[:12],
                                data.get("msg", ""),
                            )
                        continue
                    items = data.get("data", {}).get("items", [])
                    logger.info(
                        "轮询 %s: items=%d last_time=%d now=%d",
                        chat_id[:12], len(items), last_time, int(time.time() * 1000),
                    )
                    for msg in reversed(items):
                        msg_time = int(msg.get("create_time", "0"))
                        sender = msg.get("sender", {})
                        sender_id = sender.get("id", "")
                        body_preview = msg.get("body", {}).get("content", "")[:30]
                        logger.info(
                            "  消息: time=%d diff=%d sender=%s body=%s",
                            msg_time, msg_time - last_time, sender_id[:16], body_preview,
                        )
                        if msg_time > last_time:
                            # 有新消息，构造事件处理
                            msg_type = msg.get("msg_type", "")
                            if msg_type == "text":
                                # 跳过 bot 自己发的消息（以 cli_ 开头）
                                if not sender_id or sender_id.startswith("cli_"):
                                    logger.info("  跳过 bot 消息: sender=%s", sender_id)
                                    continue
                                event = {
                                    "type": "im.message.receive_v1",
                                    "header": {"event_id": msg.get("message_id", "")},
                                    "event": {
                                        "message": {
                                            "message_id": msg.get("message_id", ""),
                                            "chat_id": chat_id,
                                            "sender": {
                                                "sender_id": {
                                                    "open_id": sender.get("id", "")
                                                }
                                            },
                                            "msg_type": msg_type,
                                            "content": msg.get("body", {}).get(
                                                "content", "{}"
                                            ),
                                        }
                                    },
                                }
                                try:
                                    logger.info(
                                        "轮询消息处理: chat=%s sender=%s body=%s",
                                        chat_id[:12],
                                        sender_id[:12],
                                        msg.get("body", {}).get("content", "")[:50],
                                    )
                                    await self.handler.handle_event(event)
                                except Exception as e:
                                    logger.error("轮询消息处理异常: %s", e)
                    # 更新最后检查时间为本次轮询开始前的时间戳
                    self._last_msg_times[chat_id] = int(time.time() * 1000)
                except Exception as e:
                    logger.debug("轮询 %s 异常: %s", chat_id[:12], e)
