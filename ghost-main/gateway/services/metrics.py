"""
Gateway Metrics — Prometheus Observability
============================================
Exposes /metrics endpoint for Prometheus scraping.
Tracks request counts, durations, and backend health.
"""

import time
import logging
from typing import Optional

from fastapi import Request
from fastapi.responses import Response

logger = logging.getLogger("ghost-gateway")

# ── Prometheus client (optional dependency) ──
try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        generate_latest,
        CONTENT_TYPE_LATEST,
        CollectorRegistry,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.info("prometheus_client not installed — /metrics disabled")

# ── Metrics Registry ──
if PROMETHEUS_AVAILABLE:
    _registry = CollectorRegistry()

    # Request counters
    http_requests_total = Counter(
        "gateway_http_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status"],
        registry=_registry,
    )

    # Request duration histogram
    http_request_duration_seconds = Histogram(
        "gateway_http_request_duration_seconds",
        "HTTP request duration in seconds",
        ["method", "endpoint"],
        buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
        registry=_registry,
    )

    # Active requests gauge
    http_requests_in_flight = Gauge(
        "gateway_http_requests_in_flight",
        "Current in-flight HTTP requests",
        registry=_registry,
    )

    # Backend health gauges (1 = healthy, 0 = unhealthy)
    backend_health = Gauge(
        "gateway_backend_health",
        "Backend service health status (1=ok, 0=error)",
        ["backend"],
        registry=_registry,
    )

    # Backend request latencies
    backend_request_duration_seconds = Histogram(
        "gateway_backend_request_duration_seconds",
        "Backend request duration in seconds",
        ["backend", "endpoint"],
        buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
        registry=_registry,
    )


def record_request(method: str, endpoint: str, status: int, duration: float) -> None:
    """Record an HTTP request metric."""
    if not PROMETHEUS_AVAILABLE:
        return
    http_requests_total.labels(method=method, endpoint=endpoint, status=str(status)).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)


def set_backend_health(backend: str, healthy: bool) -> None:
    """Update backend health gauge."""
    if not PROMETHEUS_AVAILABLE:
        return
    backend_health.labels(backend=backend).set(1 if healthy else 0)


def record_backend_latency(backend: str, endpoint: str, duration: float) -> None:
    """Record backend request latency."""
    if not PROMETHEUS_AVAILABLE:
        return
    backend_request_duration_seconds.labels(backend=backend, endpoint=endpoint).observe(duration)


def get_metrics_response() -> Optional[Response]:
    """Generate Prometheus metrics response."""
    if not PROMETHEUS_AVAILABLE:
        return None
    return Response(
        content=generate_latest(_registry),
        media_type=CONTENT_TYPE_LATEST,
    )
