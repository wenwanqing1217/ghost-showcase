"""事件发布器 — 向 Redis Streams 发送事件

TERM: EventBus — Redis Streams 跨服务事件总线

飞书 bot 作为独立容器运行时，通过此发布器向 Redis Streams 发送事件，
其他服务（Orchestrator / feishu-consumer）可订阅处理。
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger("feishu-bot")

# 事件类型常量（与 Alpha-ID EventBus 对齐）
EVENT_MESSAGE_SENT = "social.message"
EVENT_OPERATION_TRIGGERED = "operation.triggered"
EVENT_VIDEO_GENERATED = "content.video.generated"
EVENT_DOUYIN_PUBLISHED = "publish.douyin"
EVENT_TASK_COMPLETED = "task.completed"
EVENT_TASK_FAILED = "task.failed"


class EventPublisher:
    """Redis Streams 事件发布器（轻量级，不依赖 Alpha-ID EventBus）"""

    def __init__(self, redis_url: str = "", stream_prefix: str = "alphaid:ecom"):
        self._redis_url = redis_url or os.environ.get("REDIS_URL", "redis://localhost:6379")
        self._prefix = stream_prefix
        self._client = None  # lazy init

    def _get_client(self):
        """惰性初始化 redis 连接"""
        if self._client is None:
            try:
                import redis.asyncio as aioredis
                self._client = aioredis.from_url(
                    self._redis_url, decode_responses=True
                )
            except ImportError:
                logger.warning("redis 未安装，事件发布不可用")
                return None
        return self._client

    async def emit(self, event_type: str, data: dict) -> None:
        """发布事件到 Redis Stream

        Args:
            event_type: 事件类型（使用常量，如 EVENT_MESSAGE_SENT）
            data: 事件数据字典
        """
        client = self._get_client()
        if client is None:
            return

        stream = f"{self._prefix}:{event_type}"
        try:
            message = json.dumps(data, ensure_ascii=False, default=str)
            await client.xadd(stream, {"data": message}, maxlen=10000, approximate=True)
        except Exception as e:
            logger.warning("事件发布失败 [%s]: %s", event_type, e)

    async def close(self):
        """关闭 redis 连接"""
        if self._client:
            await self._client.aclose()
            self._client = None
