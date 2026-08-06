"""飞书 WebSocket 长连接 + HTTP 轮询兜底"""

import asyncio
import json
import logging
import time

import httpx
import websockets

from auth.token_manager import TokenManager
from transport.protobuf import parse_ws_message, send_ack

logger = logging.getLogger("feishu-bot")


def _extract_text(event_data: dict) -> str:
    """从飞书事件中提取文本内容"""
    msg = event_data.get("event", {}).get("message", {})
    content_str = msg.get("content", "{}")
    msg_type = msg.get("msg_type", "") or msg.get("message_type", "")
    try:
        content = json.loads(content_str)
    except json.JSONDecodeError:
        return ""
    if msg_type == "text":
        return content.get("text", "").strip()
    elif msg_type == "audio":
        text = content.get("text", "").strip()
        return text or content.get("file_name", "[语音消息]").strip()
    return ""


class FeishuEventWatcher:
    """主：WebSocket 长连接（实时、免公网）；断开时 HTTP 轮询兜底 + 指数退避重连。"""

    def __init__(self, token_mgr: TokenManager, channel_adapter):
        self.token_mgr = token_mgr
        self.channel_adapter = channel_adapter
        self._running = True
        self._poller = MessagePoller(token_mgr, channel_adapter)
        self._tasks: list[asyncio.Task] = []
        self._heartbeat_task: asyncio.Task | None = None
        self._processed_events: dict[str, bool] = {}

    async def run(self):
        """主循环：WS 长连接 + 轮询兜底 + 指数退避"""
        backoff = 1
        while self._running:
            try:
                await self._connect_and_listen()
                backoff = 1
            except Exception as e:
                logger.error("WS 连接异常: %s，%s 秒后重连（HTTP 轮询兜底中）", e, min(backoff, 30))
                try:
                    await self._poller.poll_once()
                except Exception as pe:
                    logger.debug("轮询兜底异常: %s", pe)
                await asyncio.sleep(min(backoff, 30))
                backoff *= 2
        logger.info("消息接收已停止")

    async def _connect_and_listen(self):
        """连接飞书 WS 并持续接收事件"""
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                "https://open.feishu.cn/callback/ws/endpoint",
                headers={"locale": "zh"},
                json={"AppID": __import__("config").FEISHU_APP_ID,
                      "AppSecret": __import__("config").FEISHU_APP_SECRET},
            )
            data = r.json()
            if data.get("code") != 0:
                raise RuntimeError(f"获取 WS 端点失败: {data}")
            ws_url = data["data"]["URL"]

        logger.info("正在连接飞书 WebSocket...")
        async with websockets.connect(ws_url, max_size=2**20) as ws:
            logger.info("飞书 WebSocket 已连接")

            # 心跳任务
            async def _heartbeat():
                while self._running:
                    await asyncio.sleep(30)
                    logger.info("WS 连接存活中...")

            if self._heartbeat_task and not self._heartbeat_task.done():
                self._heartbeat_task.cancel()
            self._heartbeat_task = asyncio.create_task(_heartbeat())
            self._tasks.append(self._heartbeat_task)

            async for raw_msg in ws:
                if not self._running:
                    break
                try:
                    event_data = await parse_ws_message(raw_msg)
                    if event_data:
                        # 发送 ACK
                        await send_ack(raw_msg, ws)
                        # 去重
                        event_id = event_data.get("header", {}).get("event_id", "")
                        if event_id and event_id in self._processed_events:
                            continue
                        if event_id:
                            self._processed_events[event_id] = True
                            if len(self._processed_events) > 5000:
                                self._processed_events.popitem(last=False)
                        # 通知轮询器学习 chat_id
                        chat_id = event_data.get("event", {}).get("message", {}).get("chat_id", "")
                        if chat_id:
                            self._poller.add_chat(chat_id)
                        # 异步处理事件 — 通过 ChannelAdapter 统一入口
                        task = asyncio.create_task(
                            self.channel_adapter.receive(
                                sender_id=event_data.get("event", {}).get("sender", {}).get("sender_id", {}).get("open_id", ""),
                                text=_extract_text(event_data),
                                chat_id=chat_id,
                                msg_id=event_id,
                                msg_type=event_data.get("event", {}).get("message", {}).get("msg_type", ""),
                                event=event_data,
                            )
                        )
                        self._tasks.append(task)
                        task.add_done_callback(
                            lambda t: self._tasks.remove(t) if t in self._tasks else None
                        )
                except Exception as e:
                    logger.error("处理 WS 消息异常: %s", e, exc_info=True)

    def stop(self):
        self._running = False
        if self._poller:
            self._poller._known_chats.clear()
        for t in self._tasks:
            if not t.done():
                t.cancel()
        self._tasks.clear()
