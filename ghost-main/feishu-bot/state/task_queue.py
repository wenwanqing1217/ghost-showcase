"""离线任务队列（关机不丢，到点自动执行）"""

import asyncio
import json
import logging
import os
import re
import threading
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional

from config import TASK_QUEUE_PATH
from state.memory import _atomic_write_json

logger = logging.getLogger("feishu-bot")


class TaskQueue:
    """持久化任务队列，支持定时执行。文件写入原子化，线程安全。"""

    def __init__(self, path: str, app: "BotApp"):
        self.path = path
        self._app = app
        self._tasks: list[dict] = []
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
                        logger.info(
                            "执行定时任务: %s <- %s", t["prompt"][:30], t["id"]
                        )
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
            result = await self._app.runner.run(
                task["prompt"], chat_id=task["chat_id"]
            )
            if self._app.handler:
                await self._app.handler._reply_text(
                    task["chat_id"],
                    "",
                    f"⏰ 定时任务完成:\n\n{result[:2000]}",
                )
        except Exception as e:
            if self._app.handler:
                await self._app.handler._reply_text(
                    task["chat_id"],
                    "",
                    f"⏰ 定时任务失败: {str(e)[:200]}",
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
