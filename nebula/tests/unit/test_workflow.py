"""工作流引擎测试"""

import pytest
from mindflow_map.workflows.engine import WorkflowEngine


@pytest.fixture
def engine():
    return WorkflowEngine()


@pytest.mark.asyncio
async def test_map_navigation(engine):
    result = await engine.execute("怎么去中关村", user_id="test-user")
    assert result["intent"]["type"] == "map"
    assert "中关村" in result["intent"].get("destination", "")


@pytest.mark.asyncio
async def test_location_search(engine):
    result = await engine.execute("查一下附近的咖啡厅", user_id="test-user")
    assert result["intent"]["type"] == "map"
    assert result["intent"]["action"] == "search"


@pytest.mark.asyncio
async def test_douyin_publish(engine):
    result = await engine.execute("帮我发一个短剧《霸道总裁爱上我》", user_id="test-user")
    assert result["intent"]["type"] == "douyin"
    assert result["intent"]["title"] == "霸道总裁爱上我"


@pytest.mark.asyncio
async def test_shopify_optimize(engine):
    result = await engine.execute("优化我的 Shopify 店铺", user_id="test-user")
    assert result["intent"]["type"] == "shopify"


@pytest.mark.asyncio
async def test_chat_fallback(engine):
    result = await engine.execute("你好", user_id="test-user")
    assert result["intent"]["type"] == "chat"
