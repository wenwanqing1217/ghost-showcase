"""地图工具测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from mindflow_map.tools.baidu_map import BaiduMapTool


@pytest.fixture
def baidu_map():
    tool = BaiduMapTool()
    tool.ak = "test-ak"
    return tool


def _build_mock_response(json_data):
    mock_response = MagicMock()
    mock_response.json = MagicMock(return_value=json_data)
    mock_response.raise_for_status = MagicMock()
    return mock_response


@pytest.mark.asyncio
async def test_search_location(baidu_map):
    """地点搜索：mock 应作用于实例的 _client，而非 AsyncClient 类"""
    mock_response = _build_mock_response({"status": 0, "result": [{"name": "中关村", "location": {"lat": 39.98, "lng": 116.32}}]})
    baidu_map._client = AsyncMock()
    baidu_map._client.get.return_value = mock_response
    result = await baidu_map.search_location("中关村")
    assert len(result) == 1
    assert result[0]["name"] == "中关村"


@pytest.mark.asyncio
async def test_geocode(baidu_map):
    """地理编码：验证返回结构，使用 pytest.approx 处理浮点精度"""
    mock_response = _build_mock_response({"status": 0, "result": {"location": {"lat": 39.98, "lng": 116.32}}})
    baidu_map._client = AsyncMock()
    baidu_map._client.get.return_value = mock_response
    result = await baidu_map.geocode("中关村")
    assert result["location"]["lat"] == pytest.approx(39.98)
    assert result["location"]["lng"] == pytest.approx(116.32)


@pytest.mark.asyncio
async def test_weather(baidu_map):
    """天气查询：验证返回结构中的核心字段"""
    mock_response = _build_mock_response({
        "status": 0,
        "result": {"region": "北京", "weather": "晴", "temperature": "28°C"},
    })
    baidu_map._client = AsyncMock()
    baidu_map._client.get.return_value = mock_response
    result = await baidu_map.weather(region="北京", latitude=39.9042, longitude=116.4074)
    assert result["region"] == "北京"
    assert result["weather"] == "晴"


@pytest.mark.asyncio
async def test_search_location_api_error(baidu_map):
    """地点搜索：API 业务错误时返回错误结构"""
    mock_response = _build_mock_response({
        "status": 200,
        "message": "Parameter Invalid",
    })
    baidu_map._client = AsyncMock()
    baidu_map._client.get.return_value = mock_response
    result = await baidu_map.search_location("invalid")
    # 业务错误码非 0 时，_request 返回错误结构
    assert "message" in result
    assert "百度地图 API 错误" in result["message"]
