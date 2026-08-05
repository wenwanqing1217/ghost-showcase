"""性能稳定性测试：事件队列、缓存、指标。"""

from __future__ import annotations

import asyncio

import pytest

from mindflow_map.core.cache import InMemoryCache, get_cache
from mindflow_map.core.events import Event, EventQueue
from mindflow_map.core.metrics import MetricsRegistry


@pytest.fixture()
def metrics() -> MetricsRegistry:
    registry = MetricsRegistry()
    registry.reset()
    return registry


@pytest.fixture()
async def event_queue() -> EventQueue:
    # 异步 fixture：EventQueue 在测试的同一个事件循环内创建与销毁，
    # 避免跨循环 await 已关闭循环上的任务触发 "Event loop is closed"（Linux 严格模式）。
    queue = EventQueue()
    yield queue
    await queue.stop()


class TestEventQueue:
    """事件队列测试。"""

    @pytest.mark.asyncio
    async def test_emit_and_receive(self, event_queue: EventQueue) -> None:
        received: list[Event] = []

        @event_queue.on("test")
        async def handler(event: Event) -> None:
            received.append(event)

        await event_queue.start()
        await event_queue.emit(Event(name="test", payload={"key": "value"}))
        await asyncio.sleep(0.1)
        await event_queue.stop()

        assert len(received) == 1
        assert received[0].name == "test"
        assert received[0].payload["key"] == "value"

    @pytest.mark.asyncio
    async def test_multiple_handlers(self, event_queue: EventQueue) -> None:
        calls: list[str] = []

        @event_queue.on("multi")
        async def handler_a(event: Event) -> None:
            calls.append("a")

        @event_queue.on("multi")
        async def handler_b(event: Event) -> None:
            calls.append("b")

        await event_queue.start()
        await event_queue.emit(Event(name="multi"))
        await asyncio.sleep(0.1)
        await event_queue.stop()

        assert set(calls) == {"a", "b"}

    @pytest.mark.asyncio
    async def test_queue_drops_old_when_full(self, event_queue: EventQueue) -> None:
        event_queue._queue = type(event_queue._queue)(maxlen=2)
        await event_queue.start()
        await event_queue.emit(Event(name="x"))
        await event_queue.emit(Event(name="x"))
        await event_queue.emit(Event(name="x"))
        await asyncio.sleep(0.1)
        await event_queue.stop()

        assert len(event_queue._queue) <= 2


class TestCacheBackends:
    """缓存后端测试。"""

    @pytest.mark.asyncio
    async def test_in_memory_cache_roundtrip(self) -> None:
        cache = InMemoryCache()
        await cache.set("k", "v")
        assert await cache.get("k") == "v"
        await cache.delete("k")
        assert await cache.get("k") is None

    @pytest.mark.asyncio
    async def test_in_memory_cache_clear(self) -> None:
        cache = InMemoryCache()
        await cache.set("a", 1)
        await cache.set("b", 2)
        await cache.clear()
        assert await cache.get("a") is None
        assert await cache.get("b") is None

    @pytest.mark.asyncio
    async def test_fallback_to_in_memory_when_redis_unavailable(self) -> None:
        cache = get_cache()
        assert isinstance(cache, InMemoryCache)


class TestMetrics:
    """指标注册表测试。"""

    @pytest.fixture(autouse=True)
    def _require_prometheus(self):
        from mindflow_map.core.metrics import _PROMETHEUS_AVAILABLE
        if not _PROMETHEUS_AVAILABLE:
            pytest.skip("prometheus_client 未安装，跳过指标测试")

    def test_increment(self, metrics: MetricsRegistry) -> None:
        metrics.increment("requests_total", labels={"method": "GET"})
        rendered = metrics.render()
        assert "mindflow_requests_total" in rendered
        assert 'method="GET"' in rendered

    def test_gauge(self, metrics: MetricsRegistry) -> None:
        metrics.gauge("active_requests", 5)
        rendered = metrics.render()
        # prometheus_client omits {} when no labels are defined and formats values as floats
        assert "mindflow_active_requests 5.0" in rendered

    def test_histogram(self, metrics: MetricsRegistry) -> None:
        metrics.observe("request_duration_seconds", 0.1)
        metrics.observe("request_duration_seconds", 0.2)
        rendered = metrics.render()
        # prometheus_client omits {} when no labels are defined and formats values as floats
        assert "mindflow_request_duration_seconds_count 2.0" in rendered

    def test_reset(self, metrics: MetricsRegistry) -> None:
        metrics.increment("x")
        metrics.reset()
        rendered = metrics.render()
        assert "mindflow_requests_total" not in rendered.split("\n")[2:]
