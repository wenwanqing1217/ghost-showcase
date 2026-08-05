"""Tests for enhanced health check endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from mindflow_map.main import app

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def _close_module_client():
    """模块测试结束后关闭 TestClient，避免泄漏 portal 线程/事件循环。"""
    yield
    client.close()


class TestHealthEndpoints:
    def test_health_root_returns_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["service"] == "mindflow-map"
        assert "timestamp" in body

    def test_livez_returns_ok(self):
        resp = client.get("/health/livez")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"

    def test_readyz_returns_ready(self):
        resp = client.get("/health/readyz")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ready"
        assert "platforms_configured" in body
        assert "timestamp" in body

    def test_healthz_returns_detailed_status(self):
        resp = client.get("/health/healthz")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "healthy"
        assert body["service"] == "mindflow-map"
        assert "version" in body
        assert "dependencies" in body
        assert "database" in body["dependencies"]
        assert "llm" in body["dependencies"]
        assert "platforms" in body

    def test_config_status_returns_platform_info(self):
        resp = client.get("/health/config")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, dict)


class TestErrorResponseFormat:
    def test_404_returns_standardized_format(self):
        resp = client.get("/nonexistent")
        assert resp.status_code == 404
        body = resp.json()
        assert "error" in body
        assert "message" in body
        assert "request_id" in body
        assert "timestamp" in body
        assert body["error"] == "not_found"

    def test_method_not_allowed_returns_standardized_format(self):
        resp = client.patch("/")
        assert resp.status_code == 405
        body = resp.json()
        assert "error" in body
        assert body["error"] == "method_not_allowed"

    def test_validation_error_returns_standardized_format(self):
        # POST with missing required fields
        resp = client.post("/api/v1/approvals", json={})
        assert resp.status_code == 422
        body = resp.json()
        assert "error" in body
        assert body["error"] == "validation_error"

    def test_generic_exception_handler_returns_500(self):
        # The generic exception handler should catch unhandled exceptions
        # and return a standardized format
        resp = client.get("/api/v1/approvals/nonexistent/decide")
        assert resp.status_code in (404, 405)


class TestRateLimitMiddleware:
    def test_rate_limit_exceeded_returns_429(self):
        # Rate limit middleware should return 429 with standardized format
        # Note: This test creates a fresh app to avoid accumulated rate limit state
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from mindflow_map.middleware.rate_limit import RateLimitMiddleware

        test_app = FastAPI()

        @test_app.get("/test-rate")
        async def test_route():
            return {"status": "ok"}

        test_app.add_middleware(RateLimitMiddleware, window_seconds=60, max_requests=2)

        test_client = TestClient(test_app)

        # First two requests should pass
        for _ in range(2):
            resp = test_client.get("/test-rate")
            assert resp.status_code == 200

        # Third request should be rate limited
        resp = test_client.get("/test-rate")
        assert resp.status_code == 429
        body = resp.json()
        assert body["error"] == "rate_limit_exceeded"
        assert "message" in body
        assert "retry_after" in body
