"""异步事件队列，用于解耦耗时任务与 HTTP 响应。"""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Deque

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """事件消息。"""

    name: str
    payload: dict[str, Any] = field(default_factory=dict)


EventHandler = Callable[[Event], Awaitable[None]]


class EventQueue:
    """线程安全的异步事件队列。"""

    def __init__(self, maxsize: int = 1000) -> None:
        self._queue: Deque[Event] = deque(maxlen=maxsize)
        self._condition = asyncio.Condition()
        self._handlers: dict[str, list[EventHandler]] = {}
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """启动消费者。"""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._consume())
        logger.info("EventQueue started")

    async def stop(self) -> None:
        """停止消费者。"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("EventQueue stopped")

    def on(self, name: str) -> Callable[[EventHandler], EventHandler]:
        """事件注册装饰器。"""

        def decorator(func: EventHandler) -> EventHandler:
            self._handlers.setdefault(name, []).append(func)
            return func

        return decorator

    async def emit(self, event: Event) -> None:
        """发布事件。"""
        async with self._condition:
            self._queue.append(event)
            self._condition.notify()
        logger.debug("Event emitted: %s", event.name)

    async def _consume(self) -> None:
        """消费事件循环。"""
        while self._running:
            async with self._condition:
                await self._condition.wait_for(lambda: len(self._queue) > 0 or not self._running)
                if not self._running:
                    break
                event = self._queue.popleft()

            handlers = self._handlers.get(event.name, [])
            for handler in handlers:
                try:
                    await handler(event)
                except Exception:  # noqa: BLE001
                    logger.exception("Event handler failed for %s", event.name)


# 全局事件队列
_event_queue: EventQueue | None = None


def get_event_queue() -> EventQueue:
    """获取全局事件队列单例。"""
    global _event_queue
    if _event_queue is None:
        _event_queue = EventQueue()
    return _event_queue
