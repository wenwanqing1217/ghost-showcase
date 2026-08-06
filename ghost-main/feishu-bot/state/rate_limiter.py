"""限流器 — 按 chat_id 令牌桶限流"""

import logging
import threading
import time

from config import RATE_LIMIT_PER_MINUTE

logger = logging.getLogger("feishu-bot")


class RateLimiter:
    """简单令牌桶限流器，防止单用户刷爆后端。"""

    def __init__(self, per_minute: int = RATE_LIMIT_PER_MINUTE):
        self._per_minute = per_minute
        self._buckets: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def allow(self, chat_id: str) -> bool:
        """检查是否允许通过，并记录一次请求"""
        now = time.time()
        with self._lock:
            timestamps = self._buckets.setdefault(chat_id, [])
            cutoff = now - 60.0
            self._buckets[chat_id] = [ts for ts in timestamps if ts > cutoff]
            timestamps = self._buckets[chat_id]
            if len(timestamps) >= self._per_minute:
                return False
            timestamps.append(now)
            return True
