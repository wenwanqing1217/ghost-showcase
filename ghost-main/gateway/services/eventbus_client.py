"""Gateway EventBus client — emits events to Redis Streams.

Minimal implementation: only emit() is needed for the Gateway to publish
events (WeChat messages, etc.) to the shared EventBus stream.
Consumption is handled by OrchestratorEngine in alphaid.
"""

import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import config

logger = logging.getLogger("ghost-gateway")

# ── Redis Streams 配置 ──

STREAM_PREFIX = os.getenv("EVENT_STREAM_PREFIX", "alphaid:events")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# ── 常量 ──

_MAX_HISTORY = 1000


@dataclass
class Event:
    """事件数据结构"""
    event_type: str
    data: Dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    timestamp: float = field(default_factory=lambda: __import__("time").time())
    source: str = "gateway"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "data": json.dumps(self.data, ensure_ascii=False),
            "timestamp": str(self.timestamp),
            "source": self.source,
        }


class GatewayEventBus:
    """Minimal EventBus client for Gateway — emit-only.

    Usage:
        bus = get_gateway_eventbus()
        event = bus.emit("social.message", {"platform": "wechat", ...})
    """

    def __init__(self):
        self._redis = None

    def _get_redis(self):
        if self._redis is None:
            try:
                import redis

                self._redis = redis.from_url(REDIS_URL, decode_responses=True)
                self._redis.ping()
                logger.info("[EventBus] Connected to Redis at %s", REDIS_URL)
            except Exception as e:
                logger.warning("[EventBus] Redis connection failed: %s", e)
                self._redis = None
        return self._redis

    def emit(self, event_type: str, data: Dict[str, Any], source: str = "gateway") -> Optional[Event]:
        """Emit an event to the Redis Stream.

        Returns the Event object on success, None on failure.
        """
        event = Event(event_type=event_type, data=data, source=source)
        redis_client = self._get_redis()
        if redis_client is None:
            logger.warning("[EventBus] Cannot emit %s — Redis unavailable", event_type)
            return None

        try:
            stream_key = f"{STREAM_PREFIX}:{event_type}"
            redis_client.xadd(
                stream_key,
                event.to_dict(),
                maxlen=_MAX_HISTORY,
                approximate=True,
            )
            logger.debug("[EventBus] Emitted %s (id=%s)", event_type, event.event_id)
            return event
        except Exception as e:
            logger.error("[EventBus] Emit error [%s]: %s", event_type, e)
            return None


# ── 全局单例 ──


_gateway_bus: Optional[GatewayEventBus] = None


def get_gateway_eventbus() -> GatewayEventBus:
    global _gateway_bus
    if _gateway_bus is None:
        _gateway_bus = GatewayEventBus()
    return _gateway_bus
