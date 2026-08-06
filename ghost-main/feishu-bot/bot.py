"""BotApp — 封装 Bot 的所有组件和全局状态"""

import asyncio
import logging

from auth.token_manager import TokenManager
from code_runner import BackendRunner, MAX_CONCURRENT
from config import TASK_QUEUE_PATH
from feishu_service import get_feishu_service
from handler import handle_event
from event_publisher import EventPublisher
from platform_router import PlatformRouter
from state.memory import ConversationMemory
from state.rate_limiter import RateLimiter
from state.task_queue import TaskQueue
from transport.ws_client import FeishuEventWatcher

logger = logging.getLogger("feishu-bot")


class BotApp:
    """封装 Bot 的所有组件和全局状态，消除模块级 globals。"""

    def __init__(self):
        self.event_loop: asyncio.AbstractEventLoop | None = None
        self.runner: BackendRunner | None = None
        self.handler: FeishuBotHandler | None = None
        self.task_queue: TaskQueue | None = None
        self.token_mgr: TokenManager | None = None
        self.watcher: FeishuEventWatcher | None = None
        self.rate_limiter = RateLimiter()
        self.feishu_service = get_feishu_service()
        self.platform_router: PlatformRouter | None = None
        self.event_publisher: EventPublisher | None = None

    async def start(self):
        """启动 Bot 所有组件"""
        self.event_loop = asyncio.get_event_loop()

        self.token_mgr = TokenManager()
        self.runner = BackendRunner()

        # 会话上下文记忆（持久化到文件，关机不丢）
        conv_mem = ConversationMemory(
            max_messages=10,
            persist_path=TASK_QUEUE_PATH.replace("tasks.json", "conversations.json"),
        )

        self.handler = FeishuBotHandler(
            self.token_mgr,
            self.runner,
            conversation_memory=conv_mem,
            rate_limiter=self.rate_limiter,
            platform_router=self.platform_router,
            event_publisher=self.event_publisher,
        )
        # 构建 ChannelAdapter（统一接口，供 OrchestratorEngine 等外部框架调用）
        from feishu_channel import FeishuChannelAdapter
        self.channel_adapter = FeishuChannelAdapter(self.handler, self.event_publisher)
        # 将 adapter 注入 handler（handler 内部可通过 self._channel_adapter 发送事件）
        self.handler._channel_adapter = self.channel_adapter

        self.task_queue = TaskQueue(TASK_QUEUE_PATH, self)
        self.watcher = FeishuEventWatcher(self.token_mgr, self.channel_adapter)
        self.platform_router = PlatformRouter()
        self.event_publisher = EventPublisher()

        logger.info("BotApp 已启动")

    async def stop(self):
        """优雅关闭"""
        if self.watcher:
            self.watcher.stop()
        if self.handler:
            await self.handler.close()
        if self.platform_router:
            await self.platform_router.close()
        if self.event_publisher:
            await self.event_publisher.close()
        if self.token_mgr:
            await self.token_mgr.close()
        logger.info("BotApp 已停止")


class FeishuBotHandler:
    """飞书消息处理器 — 持有业务状态，处理逻辑委托给 handler 包"""

    def __init__(self, token_mgr, runner, conversation_memory=None, rate_limiter=None, platform_router=None, event_publisher=None):
        self.token_mgr = token_mgr
        self.runner = runner
        self.conversation_memory = conversation_memory
        self.rate_limiter = rate_limiter
        self.platform_router = platform_router
        self.event_publisher = event_publisher
        # 已处理的消息去重（LRU OrderedDict）
        from collections import OrderedDict
        self._processed: OrderedDict = OrderedDict()
        # 待确认发布：chat_id → {title, content}（文案生成后等待用户确认）
        self._pending_publish: dict[str, dict] = {}
        # 共享 HTTP 客户端
        import httpx
        self._http_client = httpx.AsyncClient(timeout=10)
        # 反向引用 BotApp（由 BotApp.start() 设置）
        self._app: BotApp | None = None

    async def close(self):
        await self._http_client.aclose()

    def _is_duplicate(self, msg_id: str) -> bool:
        """LRU 去重：重复返回 True，新消息记录并返回 False"""
        if msg_id in self._processed:
            self._processed.move_to_end(msg_id)
            return True
        self._processed[msg_id] = True
        if len(self._processed) > 10000:
            evict_count = 2000
            for _ in range(evict_count):
                try:
                    self._processed.popitem(last=False)
                except KeyError:
                    break
            logger.info(
                "去重缓存: 淘汰 %d 条旧记录, 剩余 %d",
                evict_count,
                len(self._processed),
            )
        return False

    async def handle_event(self, event: dict):
        """委托给 handler 包处理"""
        await handle_event(self, event)

    async def _reply_text(self, chat_id: str, reply_msg_id: str, text: str):
        """回复消息"""
        token = await self.token_mgr.get_token()
        r = await self._http_client.post(
            "https://open.feishu.cn/open-apis/im/v1/messages",
            params={"receive_id_type": "chat_id"},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={
                "receive_id": chat_id,
                "msg_type": "text",
                "content": __import__("json").dumps({"text": text}, ensure_ascii=False),
            },
        )
        data = r.json()
        if data.get("code") != 0:
            logger.warning("回复失败: %s", data)
        # 发布事件（不阻塞主流程）
        if self.event_publisher:
            import asyncio
            asyncio.create_task(self.event_publisher.emit(
                "social.message",
                {"chat_id": chat_id, "msg_type": "text", "content": text[:500]},
            ))

    async def _reply_card(self, chat_id: str, reply_msg_id: str, card: dict):
        """发送交互卡片消息（msg_type=interactive）"""
        await reply_card(self.token_mgr, self._http_client, chat_id, reply_msg_id, card)

    async def _try_operation_command(self, text: str) -> tuple:
        """尝试运营指令路由（渠道助手：文案/视频/抖音/短剧）"""
        if not self.platform_router:
            return None, None
        return await self.platform_router.route_operation(text)

    def _extract_copy_action(self, reply: str) -> dict | None:
        """从文案回复中提取 {title, content}"""
        import re
        sections = re.split(r"\n──────────\n", reply)
        for sec in reversed(sections):
            if "【标题】" not in sec:
                continue
            m_title = re.search(r"【标题】(.+?)\n", sec)
            m_body = re.search(r"【正文】\n(.+?)(?:\n【标签】|\Z)", sec, re.S)
            if m_title and m_body:
                return {
                    "title": m_title.group(1).strip(),
                    "content": m_body.group(1).strip(),
                }
        return None

    async def _execute_douyin_publish(self, title: str, content: str) -> str:
        """执行抖音发布：复用 nebula 抖音指令"""
        if not self.platform_router:
            return "❌ 平台路由器未初始化"
        return await self.platform_router.publish_douyin(title, content)


# ============================================================
# 入口
# ============================================================

async def main():
    """Bot 主入口"""
    import sys
    from config import FEISHU_APP_ID, FEISHU_APP_SECRET, CODEX_PATH

    if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
        print(
            """
❌ 请设置环境变量:
   set FEISHU_APP_ID=cli_xxxxx
   set FEISHU_APP_SECRET=xxxxx

   或者创建 .env 文件:
   FEISHU_APP_ID=cli_xxxxx
   FEISHU_APP_SECRET=xxxxx
"""
        )
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            pass
        return

    app = BotApp()
    await app.start()

    print(
        f"""
╔══════════════════════════════════════╗
║   飞书 Bot → AtomCode CLI 桥接服务      ║
╠══════════════════════════════════════╣
║  App ID: {FEISHU_APP_ID[:20]}...  ║
║  并发: {MAX_CONCURRENT}               ║
║  AtomCode: {CODEX_PATH}  ║
║                                      ║
║  在飞书里给机器人发消息即可开始       ║
║  支持文字 / 语音输入                  ║
║  Ctrl+C 优雅退出                      ║
╚══════════════════════════════════════╝
"""
    )

    try:
        await app.watcher.run()
    except (asyncio.CancelledError, KeyboardInterrupt):
        logger.info("⏹️ 收到关闭信号，正在优雅退出...")
    finally:
        await app.stop()
        logger.info("✅ Bot 已安全退出")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
