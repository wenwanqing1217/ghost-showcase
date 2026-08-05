"""地图 API 测试"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from mindflow_map.main import app
from mindflow_map.tools.baidu_map import BaiduMapTool


@pytest.fixture
def client():
    return TestClient(app)


def _post_json(client: TestClient, path: str, payload: dict):
    return client.post(
        path,
        content=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )


def test_search_location_returns_demo_when_demo_mode(monkeypatch, client):
    monkeypatch.setattr("mindflow_map.api.map.settings.demo_mode", True)
    monkeypatch.setattr("mindflow_map.api.map.settings.baidu_map_auth_token", "real-token")

    response = client.post(
        "/api/v1/map/search",
        content=json.dumps({"query": "故宫", "city": "北京"}),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["message"] == "ok"
    assert payload["data"]["results"][0]["name"] == "故宫（演示结果）"


def test_route_plan_supports_travel_mode_and_coordinates(monkeypatch, client):
    monkeypatch.setattr("mindflow_map.api.map.settings.demo_mode", True)
    monkeypatch.setattr("mindflow_map.api.map.settings.baidu_map_auth_token", "real-token")

    response = client.post(
        "/api/v1/map/route",
        content=json.dumps({
            "origin": "天安门",
            "destination": "故宫",
            "mode": "walking",
            "origin_latitude": 39.9087,
            "origin_longitude": 116.3975,
            "destination_latitude": 39.9163,
            "destination_longitude": 116.3972,
        }),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["message"] == "ok"
    assert payload["data"]["result"]["routes"][0]["steps"][0]["instruction"] == "沿演示路线行驶"


def test_geocode_supports_region(monkeypatch, client):
    monkeypatch.setattr("mindflow_map.api.map.settings.demo_mode", True)
    monkeypatch.setattr("mindflow_map.api.map.settings.baidu_map_auth_token", "real-token")

    response = client.get("/api/v1/map/geocode", params={"address": "中关村", "region": "北京市"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["result"]["location"]["lat"] == 39.9042


def test_weather_query_proxies_tool_success(monkeypatch, client):
    monkeypatch.setattr("mindflow_map.api.map.settings.demo_mode", False)
    monkeypatch.setattr("mindflow_map.api.map.settings.baidu_map_auth_token", "real-token")

    tool_response = {
        "status": 0,
        "message": "ok",
        "result": {
            "region": "北京",
            "location": {"lat": 39.9042, "lng": 116.4074},
            "weather": "晴 28°C",
        },
    }

    with patch.object(BaiduMapTool, "weather", new_callable=AsyncMock, return_value=tool_response):
        response = client.post(
            "/api/v1/map/weather",
            content=json.dumps({"region": "北京", "latitude": 39.9042, "longitude": 116.4074}),
            headers={"Content-Type": "application/json"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "success": True,
        "data": tool_response,
    }


def test_weather_query_returns_business_error_when_tool_reports_failure(monkeypatch, client):
    monkeypatch.setattr("mindflow_map.api.map.settings.demo_mode", False)
    monkeypatch.setattr("mindflow_map.api.map.settings.baidu_map_auth_token", "real-token")

    tool_response = {
        "status": "202",
        "message": "地区不支持",
        "raw": {"status": "202"},
    }

    with patch.object(BaiduMapTool, "weather", new_callable=AsyncMock, return_value=tool_response):
        response = client.post(
            "/api/v1/map/weather",
            content=json.dumps({"region": "未知区域"}),
            headers={"Content-Type": "application/json"},
        )

    assert response.status_code == 502
    assert response.json()["message"] == "天气查询暂时不可用：工具调用失败：地区不支持"


def test_geocode_returns_demo_when_demo_mode(monkeypatch, client):
    monkeypatch.setattr("mindflow_map.api.map.settings.demo_mode", True)
    monkeypatch.setattr("mindflow_map.api.map.settings.baidu_map_auth_token", "real-token")

    response = client.get("/api/v1/map/geocode", params={"address": "故宫博物院"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["result"]["location"]["lat"] == 39.9042


def test_weather_returns_demo_when_demo_mode(monkeypatch, client):
    monkeypatch.setattr("mindflow_map.api.map.settings.demo_mode", True)
    monkeypatch.setattr("mindflow_map.api.map.settings.baidu_map_auth_token", "real-token")

    response = _post_json(client, "/api/v1/map/weather", {"region": "北京"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["result"]["weather"] == "演示天气：晴 26°C"


def test_search_location_returns_502_on_http_status_error(monkeypatch, client):
    """HTTPStatusError 应返回 502 而非 500。"""
    monkeypatch.setattr("mindflow_map.api.map.settings.demo_mode", False)
    monkeypatch.setattr("mindflow_map.api.map.settings.baidu_map_auth_token", "real-token")

    http_error = httpx.HTTPStatusError(
        "server error",
        request=httpx.Request("GET", "https://test"),
        response=httpx.Response(500),
    )
    with patch.object(BaiduMapTool, "search_location", new_callable=AsyncMock, side_effect=http_error):
        response = _post_json(client, "/api/v1/map/search", {"query": "故宫"})

    assert response.status_code == 502
    assert "HTTP 错误" in response.json()["message"]


def test_route_plan_returns_502_on_request_error(monkeypatch, client):
    """网络层错误（超时、连接失败）应返回 502。"""
    monkeypatch.setattr("mindflow_map.api.map.settings.demo_mode", False)
    monkeypatch.setattr("mindflow_map.api.map.settings.baidu_map_auth_token", "real-token")

    network_error = httpx.ConnectError("connection refused")
    with patch.object(BaiduMapTool, "plan_route", new_callable=AsyncMock, side_effect=network_error):
        response = _post_json(client, "/api/v1/map/route", {"origin": "天安门", "destination": "故宫"})

    assert response.status_code == 502
    assert "网络错误" in response.json()["message"]


def test_search_location_returns_500_on_value_error(monkeypatch, client):
    """响应解析失败应返回 500。"""
    monkeypatch.setattr("mindflow_map.api.map.settings.demo_mode", False)
    monkeypatch.setattr("mindflow_map.api.map.settings.baidu_map_auth_token", "real-token")

    with patch.object(BaiduMapTool, "search_location", new_callable=AsyncMock, side_effect=ValueError("invalid payload")):
        response = _post_json(client, "/api/v1/map/search", {"query": "故宫"})

    assert response.status_code == 500
    assert "解析失败" in response.json()["message"]
