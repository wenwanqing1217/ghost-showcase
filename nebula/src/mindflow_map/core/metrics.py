"""Prometheus metrics 集成 — 基于 prometheus_client 标准库

替换了原有的手写 MetricsRegistry（自定义 Prometheus 文本格式导出）。
使用官方 prometheus_client 库，支持：
- 标准 Prometheus 文本格式（无需手写 render）
- 正确的 label 支持
- Histogram buckets
- 多进程支持（可选）
- 与 Grafana / Prometheus 生态无缝集成
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager

logger = logging.getLogger(__name__)

try:
    from prometheus_client import (
        Counter,
        Gauge,
        Histogram,
        generate_latest,
        CONTENT_TYPE_LATEST,
        CollectorRegistry,
    )
    _PROMETHEUS_AVAILABLE = True
except ImportError:
    _PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus_client 未安装，指标将不生效。pip install prometheus_client")


# ── 指标定义 ──

if _PROMETHEUS_AVAILABLE:
    # 使用独立注册表，避免与默认注册表冲突
    _registry = CollectorRegistry()

    HTTP_REQUESTS = Counter(
        "mindflow_http_requests_total",
        "Total HTTP requests",
        ["method", "route", "status"],
        registry=_registry,
    )
    HTTP_LATENCY = Histogram(
        "mindflow_http_request_duration_seconds",
        "HTTP request latency",
        ["method", "route"],
        buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
        registry=_registry,
    )
    ACTIVE_REQUESTS = Gauge(
        "mindflow_http_active_requests",
        "Active HTTP requests",
        ["method", "route"],
        registry=_registry,
    )
    LLM_CALLS = Counter(
        "mindflow_llm_calls_total",
        "Total LLM API calls",
        ["model", "status"],
        registry=_registry,
    )
    LLM_LATENCY = Histogram(
        "mindflow_llm_call_duration_seconds",
        "LLM call latency",
        ["model"],
        buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
        registry=_registry,
    )
    BUSINESS_EVENTS = Counter(
        "mindflow_business_events_total",
        "Total business events",
        ["event_type"],
        registry=_registry,
    )
else:
    # 桩对象，无 prometheus_client 时也能运行
    class _Stub:
        def labels(self, *a, **k):
            return self
        def inc(self, *a, **k):
            pass
        def dec(self, *a, **k):
            pass
        def observe(self, *a, **k):
            pass
        def set(self, *a, **k):
            pass
        def time(self):
            return self
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
    HTTP_REQUESTS = HTTP_LATENCY = ACTIVE_REQUESTS = _Stub()
    LLM_CALLS = LLM_LATENCY = BUSINESS_EVENTS = _Stub()


# ── 公共 API ──

def record_http_request(method: str, route: str, status: int, duration: float) -> None:
    """记录一次 HTTP 请求"""
    HTTP_REQUESTS.labels(method=method, route=route, status=str(status)).inc()
    HTTP_LATENCY.labels(method=method, route=route).observe(duration)


def increment_active_requests(method: str, route: str) -> None:
    """活跃请求数 +1"""
    ACTIVE_REQUESTS.labels(method=method, route=route).inc()


def decrement_active_requests(method: str, route: str) -> None:
    """活跃请求数 -1"""
    ACTIVE_REQUESTS.labels(method=method, route=route).dec()


def record_llm_call(model: str, success: bool, duration: float) -> None:
    """记录一次 LLM 调用"""
    status = "success" if success else "failure"
    LLM_CALLS.labels(model=model, status=status).inc()
    LLM_LATENCY.labels(model=model).observe(duration)


def record_business_event(event_type: str) -> None:
    """记录业务事件"""
    BUSINESS_EVENTS.labels(event_type=event_type).inc()


@contextmanager
def observe_llm_call(model: str):
    """LLM 调用计时上下文管理器"""
    start = time.perf_counter()
    success = True
    try:
        yield
    except Exception:
        success = False
        raise
    finally:
        duration = time.perf_counter() - start
        record_llm_call(model, success, duration)


def get_metrics_bytes() -> bytes:
    """获取 Prometheus 指标数据（用于 /metrics 端点）"""
    if not _PROMETHEUS_AVAILABLE:
        return b"# prometheus_client not installed\n"
    return generate_latest(_registry)


def get_content_type() -> str:
    """获取 metrics 响应的 Content-Type"""
    return CONTENT_TYPE_LATEST if _PROMETHEUS_AVAILABLE else "text/plain"


# ── 向后兼容（旧接口） ──

class MetricsRegistry:
    """向后兼容的包装器（新代码应直接使用上面的函数）。

    保留了旧接口 increment/gauge/observe/render，便于渐进迁移。
    每个实例使用独立的 CollectorRegistry，避免测试间相互污染。
    """

    def __init__(self) -> None:
        if not _PROMETHEUS_AVAILABLE:
            self._registry_obj = None
            return
        # 每个实例独立注册表，避免全局状态污染
        self._registry_obj = CollectorRegistry()
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}
        self._histograms: dict[str, Histogram] = {}

    def _counter(self, name: str) -> Counter:
        if name not in self._counters:
            self._counters[name] = Counter(
                f"mindflow_{name}", f"Metric {name}", [],
                registry=self._registry_obj,
            )
        return self._counters[name]

    def _gauge(self, name: str) -> Gauge:
        if name not in self._gauges:
            self._gauges[name] = Gauge(
                f"mindflow_{name}", f"Metric {name}", [],
                registry=self._registry_obj,
            )
        return self._gauges[name]

    def _histogram(self, name: str) -> Histogram:
        if name not in self._histograms:
            self._histograms[name] = Histogram(
                f"mindflow_{name}", f"Metric {name}", [],
                registry=self._registry_obj,
            )
        return self._histograms[name]

    def increment(self, name: str, amount: float = 1.0, labels: dict | None = None) -> None:
        """兼容旧接口：计数器 +1"""
        self._counter(name).inc(amount)

    def gauge(self, name: str, value: float, labels: dict | None = None) -> None:
        """兼容旧接口：设置 Gauge 值"""
        self._gauge(name).set(value)

    def observe(self, name: str, value: float, labels: dict | None = None) -> None:
        """兼容旧接口：记录到直方图"""
        self._histogram(name).observe(value)

    def render(self) -> str:
        """兼容旧接口：返回 Prometheus 文本格式"""
        if not _PROMETHEUS_AVAILABLE or not self._registry_obj:
            return ""
        return generate_latest(self._registry_obj).decode("utf-8")

    def reset(self) -> None:
        """兼容旧接口：清空注册表（仅测试用）"""
        if self._registry_obj:
            for collector in list(self._registry_obj._names_to_collectors.values()):
                try:
                    self._registry_obj.unregister(collector)
                except KeyError:
                    pass  # 已被其他实例注销
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()


# 全局指标注册表（向后兼容）
_metrics = MetricsRegistry()


def get_metrics() -> MetricsRegistry:
    """获取全局指标注册表（向后兼容）。"""
    return _metrics
