"""自动化模块 API 测试"""

import pytest
from unittest.mock import patch, AsyncMock

from mindflow_map.api.automation import router
from mindflow_map.config import settings


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from mindflow_map.main import app
    return TestClient(app)


class TestDouyinAPI:
    def test_publish_without_credentials_returns_demo(self, client):
        response = client.post("/api/v1/automation/douyin/publish", json={
            "title": "测试短剧",
            "content": "测试内容",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["demo"] is True
        assert "note" in data

    def test_stats_without_credentials_returns_demo(self, client):
        response = client.get("/api/v1/automation/douyin/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["demo"] is True
        assert "data" in data


class TestShopifyAPI:
    def test_list_products_without_credentials_returns_demo(self, client):
        response = client.get("/api/v1/automation/shopify/products")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["demo"] is True
        assert data["products"] == []

    def test_create_product_without_credentials_returns_demo(self, client):
        response = client.post("/api/v1/automation/shopify/products", json={
            "title": "测试商品",
            "body_html": "<p>测试</p>",
            "price": 99.9,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["demo"] is True
        assert data["product"]["title"] == "测试商品"


class TestShortDramasAPI:
    def test_submit_without_credentials_returns_demo(self, client):
        """未配置 API 时返回演示模式"""
        response = client.post("/api/v1/shortdramas/submit", json={
            "title": "测试短剧",
            "content": "测试内容",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["demo"] is True
        assert "job_id" in data
        assert data["status"] == "pending"

    def test_query_without_credentials_returns_demo(self, client):
        """未配置 API 时查询返回演示模式"""
        response = client.post("/api/v1/shortdramas/query", json={
            "job_id": "test-job-123",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["demo"] is True
        assert data["status"] == "unknown"

    def test_list_jobs_returns_empty_without_db(self, client):
        """任务列表接口在无数据时返回空列表"""
        response = client.get("/api/v1/shortdramas/jobs")
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
