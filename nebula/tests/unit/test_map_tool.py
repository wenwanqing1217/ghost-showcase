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
    mock_response = _build_mock_response({"status": 0, "result": [{"name": "中关村", "location": {"lat": 39.98, "lng": 116.32}}]})
    with patch("mindflow_map.tools.baidu_map.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        result = await baidu_map.search_location("中关村")
        assert len(result) == 1
        assert result[0]["name"] == "中关村"


@pytest.mark.asyncio
async def test_geocode(baidu_map):
    mock_response = _build_mock_response({"status": 0, "result": {"location": {"lat": 39.98, "lng": 116.32}}})
    with patch("mindflow_map.tools.baidu_map.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        result = await baidu_map.geocode("中关村")
        assert result["location"]["lat"] == 39.98


@pytest.mark.asyncio
async def test_weather(baidu_map):
    mock_response = _build_mock_response({
        "status": 0,
        "result": {"region": "北京", "weather": "晴", "temperature": "28°C"},
    })
    with patch("mindflow_map.tools.baidu_map.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        result = await baidu_map.weather(region="北京", latitude=39.9042, longitude=116.4074)
        assert result["region"] == "北京"
        assert result["weather"] == "晴"
