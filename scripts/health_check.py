""" Unified health check for all Ghost services.

Usage:
    python scripts/health_check.py

Checks each service's health endpoint and reports overall status.
Useful for quick verification after `docker compose up` or `start-demo.bat`.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from dataclasses import dataclass


# ── Service registry ──

SERVICES: dict[str, dict[str, str]] = {
    "gateway": {
        "url": "http://localhost:18080/health",
        "label": "Gateway (Unified API)",
    },
    "nebula": {
        "url": "http://localhost:2002/health",
        "label": "Nebula (Workflow Engine)",
    },
    "ds": {
        "url": "http://localhost:3004/api/health",
        "label": "DS (Shopify Dashboard)",
    },
    "aid": {
        "url": "http://localhost:8000/health",
        "label": "Alpha-ID (Identity Service)",
    },
}


# ── Health checker ──

@dataclass
class HealthResult:
    name: str
    label: str
    url: str
    ok: bool
    status_code: int | None = None
    body: dict | None = None
    error: str | None = None


def check_service(name: str, url: str, label: str, timeout: float = 3.0) -> HealthResult:
    """Check a single service's health endpoint."""
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                body = json.loads(raw)
            except json.JSONDecodeError:
                body = {"raw": raw[:200]}
            return HealthResult(
                name=name,
                label=label,
                url=url,
                ok=status == 200,
                status_code=status,
                body=body,
            )
    except urllib.error.URLError as exc:
        return HealthResult(
            name=name, label=label, url=url, ok=False, error=str(exc.reason)
        )
    except Exception as exc:  # noqa: BLE001
        return HealthResult(
            name=name, label=label, url=url, ok=False, error=str(exc)
        )


def main() -> int:
    """Run health checks and print results. Returns exit code 0 if all pass."""
    print("=" * 60)
    print("Ghost Workspace Health Check")
    print("=" * 60)

    results: list[HealthResult] = []
    for name, info in SERVICES.items():
        result = check_service(name, info["url"], info["label"])
        results.append(result)

        status = "✓ OK" if result.ok else "✗ FAIL"
        print(f"\n  [{status}] {result.label}")
        print(f"         URL: {result.url}")
        if result.status_code is not None:
            print(f"         HTTP {result.status_code}")
        if result.body:
            status_val = result.body.get("status", result.body.get("state", "?"))
            print(f"         Status: {status_val}")
        if result.error:
            print(f"         Error: {result.error}")

    # Summary
    total = len(results)
    passed = sum(1 for r in results if r.ok)
    failed = total - passed

    print("\n" + "=" * 60)
    print(f"Result: {passed}/{total} services healthy")
    if failed:
        print(f"        {failed} service(s) unreachable")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
