"""
E2E test fixtures — real HTTP calls to running services.

These tests require all services to be running:
  - Alpha-ID on :8000
  - Gateway on :18080
  - Flow on :3036
  - Net-Agent on :18180

Skip automatically if a service is unreachable.
"""

import os

import httpx
import pytest

import config


def _service_reachable(url: str, timeout: float = 2.0) -> bool:
    """Check if a service responds to /health."""
    try:
        r = httpx.get(f"{url}/health", timeout=timeout)
        return r.status_code < 500
    except Exception:
        return False


@pytest.fixture(scope="module")
def gateway_url():
    """Gateway base URL — allow override via GATEWAY_PORT env var."""
    port = int(os.environ.get("GATEWAY_PORT", config.GATEWAY_PORT))
    return f"http://127.0.0.1:{port}"


@pytest.fixture(scope="module")
def flow_url():
    """Flow service base URL."""
    return config.FLOW_URL


@pytest.fixture(scope="module")
def real_gateway(gateway_url):
    """Verify Gateway is reachable, skip if not."""
    if not _service_reachable(gateway_url):
        pytest.skip(f"Gateway not reachable at {gateway_url}")
    return gateway_url


@pytest.fixture(scope="module")
def real_flow(flow_url):
    """Verify Flow is reachable, skip if not."""
    if not _service_reachable(flow_url):
        pytest.skip(f"Flow not reachable at {flow_url}")
    return flow_url


@pytest.fixture
def http_client():
    """Shared httpx client for E2E requests with default tenant header."""
    with httpx.Client(timeout=10.0, headers={"X-Tenant-ID": "e2e-test-tenant"}) as client:
        yield client
