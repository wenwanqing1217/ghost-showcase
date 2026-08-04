#!/usr/bin/env python3
"""
Feishu Notification Consumer — Event Bus → Feishu
====================================================
Listens to Redis Streams events and sends Feishu notifications.

Architecture:
  Redis Stream (event bus) → This Consumer → FeishuService → Feishu API

Event Flow:
  Webhook → Redis Stream → Consumer → Feishu Notification

Supported events:
  order:created      → 📦 新订单通知
  order:paid         → 💰 订单付款通知
  order:fulfilled    → 🚚 订单发货通知
  order:refunded     → 💸 订单退款通知
  order:cancelled    → ❌ 订单取消通知
  supply:error       → ❌ 货源异常通知
  system:alert       → 🔔 系统告警通知
  fulfillment:task:completed → ✅ 履约完成通知
  fulfillment:task:failed    → ❌ 履约失败通知

Usage:
  python feishu_consumer.py
  # or
  from feishu_consumer import start_consumer
  start_consumer(redis_client)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
import sys
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# ── Configuration ──

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
STREAM_PREFIX = os.getenv("EVENT_STREAM_PREFIX", "alphaid:ecom")
CONSUMER_GROUP = os.getenv("FEISHU_CONSUMER_GROUP", "feishu-notifiers")
CONSUMER_NAME = os.getenv("FEISHU_CONSUMER_NAME", f"feishu-{os.getpid()}")
BLOCK_TIMEOUT_MS = int(os.getenv("FEISHU_BLOCK_TIMEOUT", "5000"))
BATCH_SIZE = int(os.getenv("FEISHU_BATCH_SIZE", "10"))

# Event types to consume
SUBSCRIBED_EVENTS = [
    "order:created",
    "order:paid",
    "order:fulfilled",
    "order:refunded",
    "order:cancelled",
    "supply:error",
    "system:alert",
    "fulfillment:task:completed",
    "fulfillment:task:failed",
]

# Event type → Feishu notification type mapping
EVENT_TO_NOTIFICATION = {
    "order:created": "order:created",
    "order:paid": "order:paid",
    "order:fulfilled": "order:fulfilled",
    "order:refunded": "order:refunded",
    "order:cancelled": "order:cancelled",
    "supply:error": "supply:error",
    "system:alert": "system:alert",
    "fulfillment:task:completed": "task:completed",
    "fulfillment:task:failed": "task:failed",
}


# ── Consumer ──


class FeishuNotificationConsumer:
    """Consumes events from Redis Streams and sends Feishu notifications."""

    def __init__(self, redis_client, feishu_service=None):
        self.redis = redis_client
        self.feishu = feishu_service
        self.running = False
        self._processed_count = 0
        self._error_count = 0

    async def start(self):
        """Start consuming events."""
        if self.running:
            return

        self.running = True
        logger.info(
            "Feishu consumer starting: group=%s, consumer=%s, events=%s",
            CONSUMER_GROUP,
            CONSUMER_NAME,
            SUBSCRIBED_EVENTS,
        )

        # Create consumer groups for each event type
        for event_type in SUBSCRIBED_EVENTS:
            stream_key = f"{STREAM_PREFIX}:{event_type}"
            try:
                await self.redis.xgroup_create(stream_key, CONSUMER_GROUP, id="0", mkstream=True)
                logger.debug("Created consumer group for %s", stream_key)
            except Exception as e:
                if "BUSYGROUP" not in str(e):
                    logger.warning("Failed to create group for %s: %s", stream_key, e)

        # Start consumption loop
        await self._consume_loop()

    async def stop(self):
        """Stop consuming events."""
        self.running = False
        logger.info(
            "Feishu consumer stopped: processed=%d, errors=%d",
            self._processed_count,
            self._error_count,
        )

    async def _consume_loop(self):
        """Main consumption loop."""
        stream_keys = [f"{STREAM_PREFIX}:{et}" for et in SUBSCRIBED_EVENTS]
        _backoff = 1.0

        while self.running:
            try:
                stream_dict = {k: ">" for k in stream_keys}
                result = await self.redis.xreadgroup(
                    groupname=CONSUMER_GROUP,
                    consumername=CONSUMER_NAME,
                    streams=stream_dict,
                    count=BATCH_SIZE,
                    block=BLOCK_TIMEOUT_MS,
                )

                if not result:
                    _backoff = 1.0  # 正常空轮询，重置退避
                    continue

                _backoff = 1.0
                for stream_key, messages in result:
                    event_type = stream_key.replace(f"{STREAM_PREFIX}:", "")
                    for message_id, fields in messages:
                        await self._process_event(event_type, message_id, fields)

            except asyncio.CancelledError:
                break
            except Exception as e:
                err_str = str(e)
                # Redis XREADGROUP 超时（无消息时 block 到期）是正常行为，不告警
                if "Timeout" in err_str or "timeout" in err_str:
                    logger.debug("XREADGROUP block timeout (no messages), retrying")
                    _backoff = 1.0
                else:
                    logger.error("Consume loop error: %s", e)
                    _backoff = min(_backoff * 2, 30.0)
                await asyncio.sleep(_backoff)

    async def _process_event(self, event_type: str, message_id: str, fields: list):
        """Process a single event."""
        try:
            # Extract event data
            event_data = None
            for field, value in fields:
                if field == "data":
                    event_data = json.loads(value)
                    break

            if not event_data:
                await self.redis.xack(f"{STREAM_PREFIX}:{event_type}", CONSUMER_GROUP, message_id)
                return

            # Get notification type
            notification_type = EVENT_TO_NOTIFICATION.get(event_type)
            if not notification_type:
                logger.debug("No notification mapping for event: %s", event_type)
                await self.redis.xack(f"{STREAM_PREFIX}:{event_type}", CONSUMER_GROUP, message_id)
                return

            # Get tenant and user to notify
            tenant_id = event_data.get("tenantId", "default")
            user_id = event_data.get("notifyUserId") or self._resolve_notify_user(event_data)

            if not user_id:
                logger.debug("No user to notify for event: %s", event_type)
                await self.redis.xack(f"{STREAM_PREFIX}:{event_type}", CONSUMER_GROUP, message_id)
                return

            # Send notification via Feishu
            if self.feishu:
                await self.feishu.notify(
                    receive_id=user_id,
                    notification_type=notification_type,
                    data=event_data,
                )
            else:
                logger.info("[Mock] Would send %s notification to %s: %s", notification_type, user_id, event_data)

            self._processed_count += 1
            await self.redis.xack(f"{STREAM_PREFIX}:{event_type}", CONSUMER_GROUP, message_id)

        except Exception as e:
            logger.error("Failed to process event %s (%s): %s", event_type, message_id, e)
            self._error_count += 1
            # ACK anyway to prevent infinite retry
            try:
                await self.redis.xack(f"{STREAM_PREFIX}:{event_type}", CONSUMER_GROUP, message_id)
            except Exception:
                pass

    def _resolve_notify_user(self, event_data: Dict[str, Any]) -> Optional[str]:
        """Resolve which user to notify based on event data.

        Priority:
          1. notifyUserId (explicit)
          2. Merchant/shop owner from shop data
          3. alphaId from tenant mapping
        """
        # Check for explicit notify target
        if "notifyUserId" in event_data:
            return event_data["notifyUserId"]

        # Check for shop owner
        if "shopId" in event_data:
            # TODO: Look up shop owner from database
            pass

        # Check for alpha_id
        if "alphaId" in event_data or "alpha_id" in event_data:
            # TODO: Look up Feishu user_id from alpha_id
            pass

        return None


# ── Entry Point ──


async def _main():
    """Main entry point for standalone execution."""
    import signal

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Connect to Redis
    import redis.asyncio as aioredis
    redis = aioredis.from_url(REDIS_URL, decode_responses=True)

    # Try to load Feishu service
    feishu = None
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/feishu-bot")
        from feishu_service import get_feishu_service
        feishu = get_feishu_service()
        logger.info("FeishuService loaded: enabled=%s", feishu.enabled)
    except Exception as e:
        logger.warning("FeishuService not loaded: %s", e)

    consumer = FeishuNotificationConsumer(redis, feishu)

    # Graceful shutdown
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _signal_handler():
        logger.info("Received shutdown signal")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            signal.signal(sig, lambda s, f: _signal_handler())

    # Start consumer in background
    consumer_task = asyncio.create_task(consumer.start())

    # Wait for shutdown signal
    await stop_event.wait()

    # Cleanup
    await consumer.stop()
    consumer_task.cancel()
    await redis.close()
    logger.info("Feishu consumer shutdown complete")


if __name__ == "__main__":
    asyncio.run(_main())
