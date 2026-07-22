"""Async load / stress test for MindFlow Map API.

Usage:
    python scripts/load_test.py --base-url http://localhost:2002 --users 50 --spawn-rate 5 --duration 60

Metrics:
    - Requests/sec
    - p50 / p95 / p99 latency
    - Error rate
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import random
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Sequence

import httpx

logger = logging.getLogger(__name__)


@dataclass
class LatencyStats:
    count: int = 0
    total_ms: float = 0.0
    min_ms: float = float("inf")
    max_ms: float = 0.0
    _samples: list[float] | None = None

    def __post_init__(self) -> None:
        self._samples = []

    def record(self, ms: float) -> None:
        self.count += 1
        self.total_ms += ms
        self.min_ms = min(self.min_ms, ms)
        self.max_ms = max(self.max_ms, ms)
        if self._samples is not None:
            self._samples.append(ms)

    def percentile(self, p: float) -> float:
        if not self._samples:
            return 0.0
        s = sorted(self._samples)
        idx = int(len(s) * p)
        idx = min(idx, len(s) - 1)
        return s[idx]

    @property
    def avg_ms(self) -> float:
        return self.total_ms / self.count if self.count else 0.0


ENDPOINTS = [
    ("GET", "/health/livez"),
    ("GET", "/health/readyz"),
    ("GET", "/health"),
    ("GET", "/"),
    ("GET", "/metrics"),
]


async def run_scenario(client: httpx.AsyncClient, base_url: str, stats: dict[str, LatencyStats], errors: dict[str, int]) -> None:
    """Run a single request scenario and record metrics."""
    method, path = random.choice(ENDPOINTS)
    url = base_url + path
    start = time.perf_counter()
    try:
        resp = await client.request(method, url, timeout=10.0)
        latency_ms = (time.perf_counter() - start) * 1000
        key = f"{method} {path}"
        stats[key].record(latency_ms)
        if resp.status_code >= 400:
            errors[f"{method} {path} {resp.status_code}"] += 1
    except Exception as exc:  # noqa: BLE001
        latency_ms = (time.perf_counter() - start) * 1000
        key = f"{method} {path}"
        stats[key].record(latency_ms)
        errors[f"{method} {path} ERROR"] += 1


async def worker(worker_id: int, base_url: str, duration: float, stats: dict[str, LatencyStats], errors: dict[str, int]) -> None:
    """Single worker making requests for a fixed duration."""
    async with httpx.AsyncClient() as client:
        deadline = time.perf_counter() + duration
        while time.perf_counter() < deadline:
            await run_scenario(client, base_url, stats, errors)
            # Random think time 10-200ms
            await asyncio.sleep(random.uniform(0.01, 0.2))


async def run_load_test(base_url: str, users: int, duration: float) -> dict[str, object]:
    stats: dict[str, LatencyStats] = defaultdict(LatencyStats)
    errors: dict[str, int] = defaultdict(int)

    logger.info("Starting load test: %d users, %.1fs duration", users, duration)
    tasks = [worker(i, base_url, duration, stats, errors) for i in range(users)]
    await asyncio.gather(*tasks)

    total_requests = sum(s.count for s in stats.values())
    total_errors = sum(errors.values())
    error_rate = (total_errors / total_requests * 100) if total_requests else 0.0

    all_latencies: list[float] = []
    for s in stats.values():
        all_latencies.extend(s._samples or [])

    all_latencies.sort()
    p50 = all_latencies[int(len(all_latencies) * 0.5)] if all_latencies else 0.0
    p95 = all_latencies[int(len(all_latencies) * 0.95)] if all_latencies else 0.0
    p99 = all_latencies[int(len(all_latencies) * 0.99)] if all_latencies else 0.0

    return {
        "base_url": base_url,
        "users": users,
        "duration_seconds": duration,
        "total_requests": total_requests,
        "requests_per_second": total_requests / duration if duration else 0,
        "error_rate_pct": round(error_rate, 2),
        "latency_p50_ms": round(p50, 2),
        "latency_p95_ms": round(p95, 2),
        "latency_p99_ms": round(p99, 2),
        "endpoints": {k: {
            "count": v.count,
            "avg_ms": round(v.avg_ms, 2),
            "p95_ms": round(v.percentile(0.95), 2),
            "min_ms": round(v.min_ms, 2),
            "max_ms": round(v.max_ms, 2),
        } for k, v in stats.items()},
        "errors": dict(errors),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="MindFlow Map API load test")
    parser.add_argument("--base-url", default="http://localhost:2002", help="Base URL for API")
    parser.add_argument("--users", type=int, default=10, help="Concurrent users")
    parser.add_argument("--duration", type=float, default=30.0, help="Duration in seconds")
    parser.add_argument("--output", default="", help="Optional JSON report path")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    start = time.perf_counter()
    report = asyncio.run(run_load_test(args.base_url, args.users, args.duration))
    wall = time.perf_counter() - start
    report["wall_clock_seconds"] = round(wall, 2)

    print("\n" + json.dumps(report, ensure_ascii=False, indent=2))

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info("Report written to %s", args.output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
