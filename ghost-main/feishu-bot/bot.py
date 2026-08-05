#!/usr/bin/env python3
"""
飞书 Bot → AtomCode CLI 桥接服务 + 离线任务队列
=================================
用户通过飞书发消息（文字/语音自动转文字），
Bot 接收后传给 AtomCode CLI 处理，结果返回给用户。

运行: python bot.py

安全/质量改进：
  - 全局状态封装进 BotApp 类（消除模块级 globals）
  - 文件写入原子化（tempfile + os.replace）
  - 共享 httpx.AsyncClient（避免每次请求创建连接）
  - 简单令牌桶限流（每 chat_id 每分钟 20 条）
  - LRU 去重集合（渐进淘汰而非整体清空）
  - 类型提示完善
"""

import asyncio
import json
import os
import sys
import time
import uuid
import logging
import re
import tempfile
import threading
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Optional, Dict, List

import httpx
import websockets
from dotenv import load_dotenv

# 飞书 WebSocket 协议（protobuf 帧解码）
from lark_oapi.ws.pb.pbbp2_pb2 import Frame

# Feishu 卡片构建服务
from feishu_service import get_feishu_service

load_dotenv()

# 从 code_runner 导入统一后端配置（单一起源，消除重复）
from code_runner import BackendRunner, BACKENDS, DEFAULT_BACKEND, MAX_CONCURRENT

# ============================================================
# 飞书配置
# ============================================================
FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")
CODEX_PATH = os.environ.get("CODEX_PATH", "atomcode")  # 仅用于启动横幅展示

TASK_QUEUE_PATH = os.path.join(os.path.dirname(__file__), "tasks.json")

# 限流配置
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))

# ============================================================
# 原子文件写入工具
# ============================================================


def _atomic_write_json(filepath: str, data) -> None:
    """原子写入 JSON 文件（tempfile + os.replace）"""
    dir_path = os.path.dirname(filepath)
    fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix=".tmp", prefix=".bot_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, filepath)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ============================================================
# Protobuf 帧工具函数
# ============================================================

def _extract_payload(data: bytes) -> bytes:
    """从 pbbp2.Frame protobuf 原始字节中提取 payload 字段（field 8）。
    兼容服务端省略 SeqID/LogID 等必填字段导致 Frame.ParseFromString 失败的情况。
    """
    i = 0
    while i < len(data):
        tag = data[i]
        i += 1
        if i > len(data):
            break
        field_number = tag >> 3
        wire_type = tag & 0x07

        if wire_type == 0:  # VARINT
            while i < len(data) and data[i] & 0x80:
                i += 1
            i += 1
        elif wire_type == 1:  # 64-bit
            i += 8
        elif wire_type == 2:  # Length-delimited
            length = 0
            shift = 0
            while i < len(data):
                b = data[i]
                i += 1
                length |= (b & 0x7F) << shift
                shift += 7
                if not (b & 0x80):
                    break
            if field_number == 8:  # payload
                return data[i : i + length]
            i += length
        elif wire_type == 5:  # 32-bit
            i += 4
        else:
            break
    return b""


# ============================================================
# 离线任务队列（关机不丢，到点自动执行）
# ============================================================
class TaskQueue:
    """持久化任务队列，支持定时执行。文件写入原子化，线程安全。"""

    def __init__(self, path: str, app: "BotApp"):
        self.path = path
        self._app = app
        self._tasks: List[dict] = []
        self._lock = threading.Lock()
        self._load()
        # 后台调度线程
        self._scheduler = threading.Thread(
            target=self._scheduler_loop, daemon=True, name="task-scheduler"
        )
        self._scheduler.start()

    def _load(self):
        try:
            if os.path.exists(self.path):
                with open(self.path, "r", encoding="utf-8") as f:
                    self._tasks = json.load(f)
                logger.info("任务队列已加载: %s 个待办", len(self._tasks))
        except Exception as e:
            logger.warning("加载任务队列失败: %s", e)
            self._tasks = []

    def _save(self):
        """原子写入任务队列"""
        with self._lock:
            tasks_copy = list(self._tasks)
        try:
            _atomic_write_json(self.path, tasks_copy)
        except Exception as e:
            logger.warning("保存任务队列失败: %s", e)

    def add(self, chat_id: str, prompt: str, execute_at: float, msg_id: str = ""):
        """添加定时任务"""
        task = {
            "id": uuid.uuid4().hex[:12],
            "chat_id": chat_id,
            "prompt": prompt,
            "execute_at": execute_at,
            "msg_id": msg_id,
            "created_at": time.time(),
            "done": False,
        }
        with self._lock:
            self._tasks.append(task)
        self._save()
        return task

    def get_pending(self) -> list:
        with self._lock:
            return [t for t in self._tasks if not t.get("done")]

    def mark_done(self, task_id: str):
        with self._lock:
            for t in self._tasks:
                if t["id"] == task_id:
                    t["done"] = True
                    t["completed_at"] = time.time()
                    break
        self._save()

    def _scheduler_loop(self):
        """后台线程：每分钟检查一次到期的任务"""
        while True:
            try:
                now = time.time()
                for t in self.get_pending():
                    if t["execute_at"] <= now:
                        logger.info("执行定时任务: %s <- %s", t["prompt"][:30], t["id"])
                        # 丢给事件循环执行
                        asyncio.run_coroutine_threadsafe(
                            self._execute_task(t),
                            self._app.event_loop,
                        )
                        self.mark_done(t["id"])
            except Exception as e:
                logger.warning("调度循环异常: %s", e)
            time.sleep(60)

    async def _execute_task(self, task: dict):
        """执行单个定时任务"""
        try:
            result = await self._app.runner.run(task["prompt"], chat_id=task["chat_id"])
            if self._app.handler:
                await self._app.handler._reply_text(
                    task["chat_id"], "", f"⏰ 定时任务完成:\n\n{result[:2000]}"
                )
        except Exception as e:
            if self._app.handler:
                await self._app.handler._reply_text(
                    task["chat_id"], "", f"⏰ 定时任务失败: {str(e)[:200]}"
                )

    def parse_time(self, text: str) -> Optional[float]:
        """解析中文时间表达，返回时间戳"""
        now = datetime.now()
        t = text.lower()

        # 明天X点
        m = re.search(r"明天(?:早上|上午|下午|晚上)?\s*(\d{1,2})(?:[：:]?(\d{2}))?", t)
        if m:
            h, mi = int(m.group(1)), int(m.group(2) or 0)
            dt = now + timedelta(days=1)
            return dt.replace(hour=h, minute=mi, second=0).timestamp()

        # 后天X点
        m = re.search(r"后天(?:早上|上午|下午|晚上)?\s*(\d{1,2})(?:[：:]?(\d{2}))?", t)
        if m:
            h, mi = int(m.group(1)), int(m.group(2) or 0)
            dt = now + timedelta(days=2)
            return dt.replace(hour=h, minute=mi, second=0).timestamp()

        # X小时后 / X分钟
        m = re.search(r"(\d+)\s*(?:小时|分钟|分)", t)
        if m:
            n = int(m.group(1))
            if "小时" in t:
                return (now + timedelta(hours=n)).timestamp()
            else:
                return (now + timedelta(minutes=n)).timestamp()

        # 今天X点
        m = re.search(
            r"(?:今天|今晚)?(?:早上|上午|下午|晚上)?\s*(\d{1,2})(?:[：:]?(\d{2}))?", t
        )
        if m:
            h, mi = int(m.group(1)), int(m.group(2) or 0)
            dt = now.replace(hour=h, minute=mi, second=0)
            if dt < now:
                dt += timedelta(days=1)
            return dt.timestamp()

        return None  # 没识别到时间


# ============================================================
# 限流器（令牌桶，按 chat_id）
# ============================================================
class RateLimiter:
    """简单令牌桶限流器，防止单用户刷爆后端。"""

    def __init__(self, per_minute: int = RATE_LIMIT_PER_MINUTE):
        self._per_minute = per_minute
        self._buckets: Dict[str, List[float]] = {}
        self._lock = threading.Lock()

    def allow(self, chat_id: str) -> bool:
        """检查是否允许通过，并记录一次请求"""
        now = time.time()
        with self._lock:
            timestamps = self._buckets.setdefault(chat_id, [])
            # 清理 60 秒前的记录
            cutoff = now - 60.0
            self._buckets[chat_id] = [ts for ts in timestamps if ts > cutoff]
            timestamps = self._buckets[chat_id]
            if len(timestamps) >= self._per_minute:
                return False
            timestamps.append(now)
            return True


# ============================================================
# 日志（UTF-8 编码）
# ============================================================
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("feishu-bot")

# 添加文件日志
_log_dir = os.path.dirname(os.path.abspath(__file__))
_fh = logging.FileHandler(
    os.path.join(_log_dir, "bot_current.log"), encoding="utf-8", mode="a"
)
_fh.setLevel(logging.INFO)
_fh.setFormatter(
    logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S"
    )
)
logger.addHandler(_fh)


# ============================================================
# 会话上下文记忆（让 Bot 记住多轮对话）
# ============================================================
class ConversationMemory:
    """每个会话维护最近的消息历史，作为上下文传给后端

    - 按 chat_id 独立存储
    - 保留最近 N 条消息（默认 10）
    - 可选的持久化（JSON 文件，原子写入）
    """

    def __init__(self, max_messages: int = 10, persist_path: str = ""):
        self._histories: dict[str, list[dict]] = {}
        self._max_messages = max_messages
        self._persist_path = persist_path
        self._lock = threading.Lock()
        if persist_path:
            self._load()

    def _load(self):
        """从文件加载历史"""
        if not os.path.exists(self._persist_path):
            return
        try:
            with open(self._persist_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._histories = {k: v[-self._max_messages :] for k, v in data.items()}
        except Exception as e:
            logger.warning("加载会话上下文失败: %s", e)

    def _save(self):
        """原子持久化到文件"""
        if not self._persist_path:
            return
        with self._lock:
            data_copy = dict(self._histories)
        try:
            _atomic_write_json(self._persist_path, data_copy)
        except Exception as e:
            logger.warning("保存会话上下文失败: %s", e)

    def add(self, chat_id: str, role: str, content: str):
        """添加一条消息到会话历史"""
        with self._lock:
            if chat_id not in self._histories:
                self._histories[chat_id] = []
            self._histories[chat_id].append(
                {"role": role, "content": content, "time": time.time()}
            )
            # 超出上限则裁剪旧消息
            if len(self._histories[chat_id]) > self._max_messages:
                self._histories[chat_id] = self._histories[chat_id][
                    -self._max_messages :
                ]
        self._save()

    def build_context_prompt(self, chat_id: str, current_text: str) -> str:
        """将历史会话拼接到当前消息前，作为后端上下文"""
        with self._lock:
            hist = list(self._histories.get(chat_id, []))
        if not hist:
            return current_text

        parts = []
        for msg in hist[:-1]:  # 除最后一条（刚添加的当前消息）之外的历史
            label = "用户" if msg["role"] == "user" else "助手"
            content_preview = msg["content"][:3000]
            parts.append(f"{label}: {content_preview}")
        if parts:
            context = "\n\n".join(parts)
            return f"【以下是对话历史】\n{context}\n\n【现在请回答】\n{current_text}"
        return current_text

    def clear(self, chat_id: str = ""):
        """清除会话历史（指定 chat_id 或全部）"""
        with self._lock:
            if chat_id:
                self._histories.pop(chat_id, None)
            else:
                self._histories.clear()
        self._save()


# ============================================================
# Token 管理（自动刷新，复用 HTTP 客户端）
# ============================================================
class TokenManager:
    def __init__(self):
        self._token = None
        self._expires_at = 0
        self._lock = asyncio.Lock()
        self._client = httpx.AsyncClient(timeout=10)

    async def get_token(self) -> str:
        async with self._lock:
            if time.time() < self._expires_at - 60:
                return self._token
            await self._refresh()
            return self._token

    async def _refresh(self):
        r = await self._client.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET},
        )
        data = r.json()
        if data.get("code") != 0:
            raise RuntimeError(f"获取 token 失败: {data}")
        self._token = data["tenant_access_token"]
        self._expires_at = time.time() + data["expire"]
        logger.info("Token 已刷新，有效期 %s 秒", data["expire"])

    async def close(self):
        await self._client.aclose()


# BackendRunner 已从 code_runner 导入


# ============================================================
# 飞书消息处理
# ============================================================
class FeishuBotHandler:
    def __init__(
        self,
        token_mgr: TokenManager,
        runner: BackendRunner,
        conversation_memory: Optional[ConversationMemory] = None,
        rate_limiter: Optional[RateLimiter] = None,
    ):
        self.token_mgr = token_mgr
        self.runner = runner
        self.conversation_memory = conversation_memory or ConversationMemory()
        self.rate_limiter = rate_limiter or RateLimiter()
        # 已处理的消息去重（LRU OrderedDict）
        self._processed: OrderedDict = OrderedDict()
        # 共享 HTTP 客户端（避免每次请求创建新连接）
        self._http_client = httpx.AsyncClient(timeout=10)
        # 反向引用 BotApp（由 BotApp.start() 设置）
        self._app: Optional["BotApp"] = None

    async def close(self):
        await self._http_client.aclose()

    def _is_duplicate(self, msg_id: str) -> bool:
        """LRU 去重：重复返回 True，新消息记录并返回 False"""
        if msg_id in self._processed:
            # 移到末尾（最近使用）
            self._processed.move_to_end(msg_id)
            return True
        self._processed[msg_id] = True
        # LRU 渐进淘汰：超出上限时移除最旧的 20%
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
        """处理飞书事件（兼容 v2.0 schema）"""
        logger.info("handle_event called! event keys: %s", list(event.keys())[:5])
        # 兼容 v2.0 schema: event_type 在 header 中
        event_type = event.get("type") or event.get("header", {}).get("event_type", "")
        if event_type != "im.message.receive_v1":
            logger.info("handle_event: skip event_type=%s", event_type)
            return

        # 跳过 bot 自己发出的消息（防止循环）
        # 兼容 v1/v2 事件结构：sender 可能在 event.sender 或 event.message.sender
        sender = (
            event.get("event", {}).get("sender", {})
            or event.get("event", {}).get("message", {}).get("sender", {})
        )
        sid = sender.get("sender_id", sender)
        open_id = sid.get("open_id", "")
        # 只有 ou_ 开头的才是真实用户消息，bot 的消息跳过
        if not open_id.startswith("ou_"):
            return

        header = event.get("header", {})
        event_id = header.get("event_id", "")
        if self._is_duplicate(event_id):
            return

        msg = event.get("event", {}).get("message", {})
        msg_id = msg.get("message_id", "")
        chat_id = msg.get("chat_id", "")
        # sender_id: 兼容 v1 (event.message.sender) 和 v2 (event.sender)
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
            # 飞书语音消息自动转文字，转文字结果在 content 的 text 字段
            text = content.get("text", "").strip()
            if not text:
                text = content.get("file_name", "[语音消息]").strip()
        else:
            # 其他类型暂不支持
            await self._reply_text(
                chat_id, msg_id, f"暂不支持 {msg_type} 类型消息，请发送文字或语音"
            )
            return

        if not text:
            return

        # 如果是 @bot 的消息，去掉 @bot 前缀
        text = self._clean_mention(text)

        # ---- 限流检查 ----
        if not self.rate_limiter.allow(chat_id):
            await self._reply_text(chat_id, msg_id, "⚠️ 请求过于频繁，请稍后再试")
            return

        # ---- 处理 chat 命令 ----
        if text.startswith("/"):
            # /video 命令需要异步处理（API 调用 + 轮询）
            if text.startswith("/video"):
                await self._handle_video_command(text, chat_id, msg_id)
                return
            reply = await self._handle_command(text, chat_id)
            if reply:
                await self._reply_text(chat_id, msg_id, reply)
            return

        # ---- 处理正常消息 ----
        backend_name = self.runner.get_backend(chat_id)
        logger.info(
            "收到消息 [%s] 后端=%s: %s...", chat_id[:8], backend_name, text[:50]
        )

        # 记录用户消息到上下文记忆
        self.conversation_memory.add(chat_id, "user", text)

        # 构建含历史上下文的 prompt
        context_prompt = self.conversation_memory.build_context_prompt(chat_id, text)
        if context_prompt != text:
            logger.info(
                "为 [%s] 附加了 %d 条历史上下文",
                chat_id[:8],
                len(self.conversation_memory._histories.get(chat_id, [])),
            )

        # 先回复一个"处理中"的提示
        await self._reply_text(chat_id, msg_id, "⏳ 正在处理，请稍候...")

        # 调用后端
        try:
            result = await self.runner.run(context_prompt, chat_id=chat_id)
        except Exception as e:
            logger.exception("后端调用失败")
            result = f"❌ 处理出错: {str(e)[:200]}"

        # 记录助手回复到上下文记忆
        self.conversation_memory.add(chat_id, "assistant", result[:3000])

        # 飞书消息有长度限制（约 15000 字），超长则截断
        if len(result) > 14000:
            result = result[:13900] + "\n\n...（内容过长已截断）"

        logger.info("准备回复 [%s] 长度=%s", chat_id[:8], len(result))
        try:
            await self._reply_text(chat_id, msg_id, result)
            logger.info("回复完成 [%s]", chat_id[:8])
        except Exception as e:
            logger.exception("回复发送失败: %s", e)

    def _clean_mention(self, text: str) -> str:
        """去掉 @机器人 前缀（兼容飞书多种 @ 格式）"""
        text = re.sub(r"@_user_\d+\s*", "", text).strip()
        # 也去掉纯数字 open_id 格式（飞书新版 @ 格式）
        text = re.sub(r"@(ou_\w+|[\w-]{20,})\s*", "", text).strip()
        # 去掉富文本 xml 标签中的 @mention
        text = re.sub(r"<at.*?</at>", "", text).strip()
        return text

    async def _reply_text(self, chat_id: str, reply_msg_id: str, text: str):
        """回复消息（复用共享 HTTP 客户端）"""
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
                "content": json.dumps({"text": text}, ensure_ascii=False),
            },
        )
        data = r.json()
        if data.get("code") != 0:
            logger.warning("回复失败: %s", data)

    async def _handle_command(self, text: str, chat_id: str) -> str:
        """处理 / 开头的命令"""
        parts = text.strip().split()
        cmd = parts[0].lower()

        if cmd == "/backend":
            if len(parts) == 1 or parts[1] == "list":
                current = self.runner.get_backend(chat_id)
                lines = ["**可用后端：**"]
                for name, cfg in BACKENDS.items():
                    mark = " ← 当前" if name == current else ""
                    lines.append(f"  /backend {name} — {cfg['desc']}{mark}")
                return "\n".join(lines)

            elif len(parts) >= 2:
                target = parts[1]
                if target in BACKENDS:
                    self.runner.set_backend(chat_id, target)
                    return f"✅ 已切换到后端: **{target}**（{BACKENDS[target]['desc']}）"
                else:
                    return f"❌ 后端 '{target}' 不存在，用 /backend list 查看可用后端"

        elif cmd == "/status":
            current = self.runner.get_backend(chat_id)
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
            self.conversation_memory.clear(chat_id)
            return "🧹 已清空当前会话的上下文记忆"

        elif cmd == "/task":
            if not self._app or not self._app.task_queue:
                return "任务队列未初始化"
            if len(parts) >= 2 and parts[1] == "list":
                pending = self._app.task_queue.get_pending()
                if not pending:
                    return "📭 没有待办任务"
                lines = ["**待办任务：**"]
                for t in pending[:10]:
                    dt = datetime.fromtimestamp(t["execute_at"]).strftime("%m-%d %H:%M")
                    lines.append(f"  • [{dt}] {t['prompt'][:40]}...")
                return "\n".join(lines)
            else:
                pending = self._app.task_queue.get_pending()
                return f"待办任务: {len(pending)} 个"

        return None

    async def _handle_video_command(self, text: str, chat_id: str, msg_id: str):
        """Handle /video command — trigger AI video generation via Gateway.

        Usage:
          /video <topic>           — generate video about a topic
          /video <topic> 9:16      — portrait mode (default)
          /video <topic> 16:9      — landscape mode
          /video <topic> 1:1       — square mode

        Flow:
          1. Parse topic and options from command
          2. Call Gateway /v1/content/video/generate
          3. Send "generating..." message
          4. Poll status every 10s
          5. When complete, send video card with inline player
        """
        parts = text.strip().split(maxsplit=2)
        if len(parts) < 2:
            await self._reply_text(chat_id, msg_id,
                "用法: /video <主题> [比例]\n"
                "示例: /video 深海探索\n"
                "  /video 赛博朋克城市 16:9\n"
                "  /video 日本樱花 9:16\n"
                "支持的参数:\n"
                "  比例: 9:16（竖屏，默认）, 16:9（横屏）, 1:1（方形）\n"
                "  语言: zh（中文，默认）, en（英文）\n"
                "  拼接: random（随机，默认）, sequential（顺序）"
            )
            return

        topic = parts[1].strip()
        # Parse optional parameters
        aspect = "9:16"
        language = "zh"
        concat_mode = "random"

        if len(parts) >= 3:
            extra = parts[2].strip()
            # Check for aspect ratio
            if ":" in extra:
                aspect = extra
            elif extra in ("zh", "en"):
                language = extra
            elif extra in ("random", "sequential"):
                concat_mode = extra

        # Validate topic length
        if len(topic) > 200:
            await self._reply_text(chat_id, msg_id, "❌ 主题过长，请控制在 200 字以内")
            return

        # Get Gateway URL from config
        gateway_url = os.environ.get("GATEWAY_URL", "http://localhost:18080")
        tenant_id = getattr(self._app, "tenant_id", "feishu-bot") if self._app else "feishu-bot"

        # Step 1: Trigger video generation
        await self._reply_text(chat_id, msg_id, f"🎬 正在生成视频「{topic[:50]}」...\n⏳ 预计需要 2-5 分钟，请稍候")

        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{gateway_url}/v1/content/video/generate",
                    headers={
                        "Content-Type": "application/json",
                        "X-Tenant-ID": tenant_id,
                        "X-Request-ID": str(uuid.uuid4()),
                    },
                    json={
                        "video_subject": topic,
                        "video_language": language,
                        "video_aspect": aspect,
                        "video_concat_mode": concat_mode,
                        "paragraph_number": 1,
                        "n_threads": 2,
                        "video_source": "local",
                    },
                )
                data = resp.json()

            if not data.get("success"):
                error_msg = data.get("error", "unknown error")
                await self._reply_text(chat_id, msg_id, f"❌ 视频生成请求失败: {error_msg}")
                return

            task_id = data.get("data", {}).get("task_id")
            if not task_id:
                await self._reply_text(chat_id, msg_id, "❌ 未获取到任务 ID，请稍后重试")
                return

            # Step 2: Poll for completion
            await self._poll_video_task(task_id, chat_id, msg_id, gateway_url, tenant_id)

        except Exception as e:
            logger.exception("Video generation error")
            await self._reply_text(chat_id, msg_id, f"❌ 视频生成出错: {str(e)[:200]}")

    async def _poll_video_task(self, task_id: str, chat_id: str, msg_id: str,
                                gateway_url: str, tenant_id: str):
        """Poll video generation task and send video card when ready."""
        import httpx
        max_polls = 60  # 60 polls * 10s = 10 minutes max
        poll_interval = 10

        for i in range(max_polls):
            try:
                await asyncio.sleep(poll_interval)
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(
                        f"{gateway_url}/v1/content/video/status/{task_id}",
                        headers={
                            "X-Tenant-ID": tenant_id,
                            "X-Request-ID": str(uuid.uuid4()),
                        },
                    )
                    data = resp.json()

                if not data.get("success"):
                    await self._reply_text(chat_id, msg_id, f"❌ 查询任务状态失败: {data.get('error', 'unknown')}")
                    return

                task_data = data.get("data", {})
                # Handle nested response from proxy
                if isinstance(task_data, dict) and "data" in task_data:
                    task_data = task_data["data"]

                state = task_data.get("state", -1)
                progress = task_data.get("progress", 0)
                error = task_data.get("error")
                failed_stage = task_data.get("failed_stage")

                logger.info(f"Video task {task_id}: state={state}, progress={progress}")

                # State: 0=pending, 1=success, 2=failed, 4=processing
                if state == 1:
                    # Success! Send video card
                    videos = task_data.get("videos", [])
                    if videos:
                        video_url = videos[0]
                        # If it's a relative path, prepend the gateway URL
                        if video_url.startswith("/"):
                            # Extract host:port from gateway_url
                            gw_host = gateway_url.replace("http://", "").replace("https://", "")
                            video_url = f"{gw_host}{video_url}"
                            # If gateway is on a different host than moneyprinter, use moneyprinter directly
                        # Build preview from script
                        script = task_data.get("script", "")
                        description = script[:200] + "..." if len(script) > 200 else script

                        card = self._app.feishu_service._build_video_card(
                            title=task_data.get("video_subject") or (task_data.get("script", "")[:50] + ("..." if len(task_data.get("script", "")) > 50 else "")) or "生成的视频",
                            video_url=video_url,
                            description=f"📝 {description}\n\n✅ 生成完成",
                        )
                        await self._reply_card(chat_id, msg_id, card)
                    else:
                        await self._reply_text(chat_id, msg_id,
                            f"✅ 视频生成完成，但未获取到视频链接\n"
                            f"任务 ID: {task_id}\n"
                            f"请稍后在平台查看")
                    return

                elif state == 2 or error:
                    # Failed
                    error_detail = error or failed_stage or "unknown error"
                    await self._reply_text(chat_id, msg_id,
                        f"❌ 视频生成失败\n"
                        f"错误: {error_detail}\n"
                        f"任务 ID: {task_id}")
                    return

                # Still processing — send progress update every 6 polls
                if i > 0 and i % 6 == 0 and progress > 0:
                    await self._reply_text(chat_id, msg_id,
                        f"⏳ 视频生成中... {progress}%")

            except Exception as e:
                logger.warning(f"Poll error for task {task_id}: {e}")

        # Timeout
        await self._reply_text(chat_id, msg_id,
            f"⏰ 视频生成超时（10分钟）\n"
            f"任务 ID: {task_id}\n"
            f"请稍后在平台查看或重新生成")

    async def _reply_card(self, chat_id: str, reply_msg_id: str, card: dict):
        """Reply with an interactive card message."""
        token = await self.token_mgr.get_token()
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
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
            data = resp.json()
            if data.get("code") != 0:
                logger.warning("Send card failed: %s", data)


# ============================================================
# 消息接收（HTTP 轮询，不用 WebSocket）
# ============================================================
class FeishuEventWatcher:
    def __init__(self, token_mgr: TokenManager, handler: FeishuBotHandler):
        self.token_mgr = token_mgr
        self.handler = handler
        self._running = True
        self._poller = MessagePoller(token_mgr, handler)
        self._tasks: List[asyncio.Task] = []
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._processed_events: OrderedDict = OrderedDict()

    async def run(self):
        """主：WebSocket 长连接（实时、免公网）；断开时 HTTP 轮询兜底 + 指数退避重连。"""
        backoff = 1
        while self._running:
            try:
                await self._connect_and_listen()
                backoff = 1  # 连接成功并正常退出（异常退出走 except）后重置退避
            except Exception as e:
                logger.error("WS 连接异常: %s，%s 秒后重连（HTTP 轮询兜底中）", e, min(backoff, 30))
                # WS 断开期间用 HTTP 轮询兜底，不丢消息
                try:
                    await self._poller.poll_once()
                except Exception as pe:
                    logger.debug("轮询兜底异常: %s", pe)
                await asyncio.sleep(min(backoff, 30))
                backoff *= 2
        logger.info("消息接收已停止")

    async def _connect_and_listen(self):
        """连接飞书 WS 并持续接收事件"""
        # 获取 WebSocket 端点（用 AppID + AppSecret）
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                "https://open.feishu.cn/callback/ws/endpoint",
                headers={"locale": "zh"},
                json={"AppID": FEISHU_APP_ID, "AppSecret": FEISHU_APP_SECRET},
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
                logger.info(
                    "WS recv: type=%s len=%s",
                    type(raw_msg).__name__,
                    len(raw_msg) if hasattr(raw_msg, "__len__") else "?",
                )
                try:
                    # 先解析帧，发送 ACK，再处理事件
                    event_data = await self._parse_ws_message(raw_msg)
                    if event_data:
                        # 发送 ACK（在事件处理前，防止超时）
                        await self._send_ack(raw_msg, ws)
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
                        # 异步处理事件
                        task = asyncio.create_task(self.handler.handle_event(event_data))
                        self._tasks.append(task)
                        task.add_done_callback(
                            lambda t: self._tasks.remove(t) if t in self._tasks else None
                        )
                except Exception as e:
                    logger.error("处理 WS 消息异常: %s", e, exc_info=True)

    async def _parse_ws_message(self, raw_msg) -> Optional[dict]:
        """解析 WS 消息，返回事件 dict 或 None"""
        event_data = None

        if isinstance(raw_msg, bytes):
            # 第一尝试：标准 protobuf 解析
            try:
                frame = Frame()
                frame.ParseFromString(raw_msg)
                event_text = frame.payload.decode("utf-8", errors="replace")
                if event_text:
                    event_data = json.loads(event_text)
            except Exception:
                pass

            # Fallback：手动提取 protobuf payload（field 8）
            if event_data is None:
                payload_bytes = _extract_payload(raw_msg)
                if payload_bytes:
                    try:
                        event_data = json.loads(
                            payload_bytes.decode("utf-8", errors="replace")
                        )
                    except json.JSONDecodeError:
                        pass

            # 最后尝试：原始字节中搜索 JSON
            if event_data is None:
                try:
                    text = raw_msg.decode("utf-8", errors="replace")
                    for marker in ['"type":"im.message.receive_v1"', '"event"']:
                        idx = text.find(marker)
                        if idx >= 0:
                            start = text.rfind("{", 0, idx)
                            if start >= 0:
                                candidate = text[start : start + 2000]
                                depth = 0
                                for i, c in enumerate(candidate):
                                    if c == "{":
                                        depth += 1
                                    elif c == "}":
                                        depth -= 1
                                        if depth == 0:
                                            event_data = json.loads(candidate[: i + 1])
                                            break
                                break
                except Exception:
                    pass

            if event_data is None:
                try:
                    text_preview = raw_msg[:200].decode("utf-8", errors="replace")
                    if text_preview:
                        logger.warning("WS 消息无法解析: raw_preview=%s", text_preview[:200])
                    else:
                        logger.warning("WS 消息无法解析: raw_hex=%s", raw_msg[:120].hex())
                except Exception:
                    logger.warning("WS 消息无法解析: raw_hex=%s", raw_msg[:120].hex())

        elif isinstance(raw_msg, str):
            try:
                data = json.loads(raw_msg)
                if "event" in data or "type" in data:
                    event_data = data
            except json.JSONDecodeError:
                pass

        return event_data

    async def _send_ack(self, raw_msg, ws):
        """发送 ACK 响应给飞书服务器"""
        try:
            frame = Frame()
            frame.ParseFromString(raw_msg if isinstance(raw_msg, bytes) else raw_msg.encode())
            from lark_oapi.ws.const import HEADER_BIZ_RT
            ack = Frame()
            for h in frame.headers:
                nh = ack.headers.add()
                nh.key = h.key
                nh.value = h.value
            rt = ack.headers.add()
            rt.key = HEADER_BIZ_RT
            rt.value = "0"
            ack.method = frame.method
            ack.service = frame.service
            ack.payload = b'{"msg":"success"}'
            await ws.send(ack.SerializeToString())
        except Exception as e:
            logger.debug("ACK 发送失败: %s", e)

    def stop(self):
        self._running = False
        if self._poller:
            self._poller._known_chats.clear()
        for t in self._tasks:
            if not t.done():
                t.cancel()
        self._tasks.clear()


# ============================================================
# HTTP 轮询后备（当 WS 事件未到达时使用）
# ============================================================
class MessagePoller:
    """定时轮询飞书消息 API，用于 WS 事件未到达时的后备"""

    def __init__(self, token_mgr: TokenManager, handler: FeishuBotHandler):
        self.token_mgr = token_mgr
        self.handler = handler
        self._known_chats: set = set()
        self._last_msg_times: dict = {}
        # 从环境变量读取已知 chat_id（逗号分隔）
        extra = os.environ.get("KNOWN_CHAT_IDS", "").strip()
        if extra:
            for cid in extra.split(","):
                cid = cid.strip()
                if cid:
                    self._known_chats.add(cid)
                    self._last_msg_times[cid] = (
                        int(time.time() * 1000) - 30000
                    )  # 当前时间-30秒，只处理新消息
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
                    last_time = self._last_msg_times.get(chat_id, 0)
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
                    # 更新最后检查时间为本次轮询开始前的时间戳（防止漏掉轮询期间的新消息）
                    self._last_msg_times[chat_id] = int(time.time() * 1000)
                except Exception as e:
                    logger.debug("轮询 %s 异常: %s", chat_id[:12], e)


# ============================================================
# BotApp — 封装所有全局状态
# ============================================================
class BotApp:
    """封装 Bot 的所有组件和全局状态，消除模块级 globals。"""

    def __init__(self):
        self.event_loop: Optional[asyncio.AbstractEventLoop] = None
        self.runner: Optional[BackendRunner] = None
        self.handler: Optional[FeishuBotHandler] = None
        self.task_queue: Optional[TaskQueue] = None
        self.token_mgr: Optional[TokenManager] = None
        self.watcher: Optional[FeishuEventWatcher] = None
        self.rate_limiter = RateLimiter()
        self.feishu_service = get_feishu_service()

    async def start(self):
        """启动 Bot 所有组件"""
        self.event_loop = asyncio.get_event_loop()

        # 初始化组件
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
        )
        # 给 handler 反向引用 app（供 task_queue 等使用）
        self.handler._app = self  # type: ignore

        self.task_queue = TaskQueue(TASK_QUEUE_PATH, self)
        self.watcher = FeishuEventWatcher(self.token_mgr, self.handler)

        logger.info("BotApp 已启动")

    async def stop(self):
        """优雅关闭"""
        if self.watcher:
            self.watcher.stop()
        if self.handler:
            await self.handler.close()
        if self.token_mgr:
            await self.token_mgr.close()
        logger.info("BotApp 已停止")


# ============================================================
# 入口
# ============================================================
async def main():
    # 检查配置
    if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
        print(
            """
❌ 请设置环境变量:
   set FEISHU_APP_ID=cli_xxxxx
   set FEISHU_APP_SECRET=xxxxx

   或者创建 .env 文件:
   FEISHU_APP_ID=cli_xxxxx
   FEISHU_APP_SECRET=xxxxx

   容器内无凭证时进入休眠等待配置（避免 restart: unless-stopped 无限重启）。
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
