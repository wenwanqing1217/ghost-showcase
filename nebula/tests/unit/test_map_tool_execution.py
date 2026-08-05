"""地图工具执行参数测试。"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from mindflow_map.workflows.engine import MapNavigationTool


@pytest.fixture
def map_tool():
    tool = MapNavigationTool()
    return tool


@pytest.mark.asyncio
async def test_execute_route_forwards_coordinates_and_mode(map_tool):
    plan_response = AsyncMock(return_value={
        "status": 0,
        "result": {
            "origin": {"address": "天安门", "location": {"lat": 39.9087, "lng": 116.3975}},
            "destination": {"address": "故宫", "location": {"lat": 39.9163, "lng": 116.3972}},
            "routes": [{"distance": "2.1公里", "duration": "30分钟"}],
        },
    })

    with patch.object(map_tool.baidu_map, "plan_route", plan_response):
        result = await map_tool.execute({
            "action": "navigate",
            "origin": "天安门",
            "destination": "故宫",
            "mode": "walking",
            "origin_lat": 39.9087,
            "origin_lng": 116.3975,
            "dest_lat": 39.9163,
            "dest_lng": 116.3972,
        })

    assert result["type"] == "map"
    plan_response.assert_awaited_once_with(
        origin="天安门",
        destination="故宫",
        mode="walking",
        origin_lat=39.9087,
        origin_lng=116.3975,
        dest_lat=39.9163,
        dest_lng=116.3972,
    )


@pytest.mark.asyncio
async def test_execute_search_forwards_query(map_tool):
    search_response = AsyncMock(return_value={
        "status": 0,
        "results": [{"name": "故宫", "address": "北京市东城区景山前街4号"}],
    })

    with patch.object(map_tool.baidu_map, "search_location", search_response):
        result = await map_tool.execute({"action": "search", "query": "故宫"})

    assert result["type"] == "map"
    search_response.assert_awaited_once_with(query="故宫", city=None, latitude=None, longitude=None)


@pytest.mark.asyncio
async def test_execute_returns_error_when_location_info_missing(map_tool):
    result = await map_tool.execute({})

    assert result["type"] == "map"
    assert result["data"] == {"error": "缺少地点信息"}
