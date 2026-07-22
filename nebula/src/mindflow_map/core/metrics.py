"""Prometheus metrics 集成。"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class MetricsRegistry:
    """轻量级指标注册表，支持 Prometheus 文本格式导出。"""

    def __init__(self) -> None:
        self._counters: dict[str, float] = {}
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = {}

    def increment(self, name: str, amount: float = 1.0, labels: dict[str, str] | None = None) -> None:
        key = self._label_key(name, labels)
        self._counters[key] = self._counters.get(key, 0.0) + amount

    def gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        key = self._label_key(name, labels)
        self._gauges[key] = value

    def observe(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        key = self._label_key(name, labels)
        self._histograms.setdefault(key, []).append(value)

    @staticmethod
    def _label_key(name: str, labels: dict[str, str] | None) -> str:
        if not labels:
            return name
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def render(self) -> str:
        """导出 Prometheus 文本格式。"""
        lines: list[str] = []

        lines.append("# HELP mindflow_requests_total Total requests")
        lines.append("# TYPE mindflow_requests_total counter")
        for key, value in sorted(self._counters.items()):
            lines.append(f"mindflow_requests_total{{{self._labels_part(key)}}} {value}")

        lines.append("# HELP mindflow_active_requests Active requests")
        lines.append("# TYPE mindflow_active_requests gauge")
        for key, value in sorted(self._gauges.items()):
            lines.append(f"mindflow_active_requests{{{self._labels_part(key)}}} {value}")

        lines.append("# HELP mindflow_request_duration_seconds Request duration")
        lines.append("# TYPE mindflow_request_duration_seconds histogram")
        for key, values in sorted(self._histograms.items()):
            total = sum(values)
            count = len(values)
            lines.append(f"mindflow_request_duration_seconds_sum{{{self._labels_part(key)}}} {total}")
            lines.append(f"mindflow_request_duration_seconds_count{{{self._labels_part(key)}}} {count}")

        return "\n".join(lines) + "\n"

    @staticmethod
    def _labels_part(key: str) -> str:
        if "{" in key:
            base, _, labels = key.partition("{")
            return f"{base}_total{{{labels}"
        return ""

    def reset(self) -> None:
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()


# 全局指标注册表
_metrics = MetricsRegistry()


def get_metrics() -> MetricsRegistry:
    """获取全局指标注册表。"""
    return _metrics
