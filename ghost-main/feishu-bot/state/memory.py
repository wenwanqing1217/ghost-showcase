"""会话上下文记忆 — 让 Bot 记住多轮对话"""

import json
import logging
import os
import threading
import time

from config import TASK_QUEUE_PATH

logger = logging.getLogger("feishu-bot")


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
        for msg in hist[:-1]:
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


# ── 原子文件写入工具（被 task_queue 和 memory 共用） ──

import tempfile as _tempfile


def _atomic_write_json(filepath: str, data) -> None:
    """原子写入 JSON 文件（tempfile + os.replace）"""
    dir_path = os.path.dirname(filepath)
    fd, tmp_path = _tempfile.mkstemp(dir=dir_path, suffix=".tmp", prefix=".bot_")
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
