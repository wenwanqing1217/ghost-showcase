"""LLM 意图识别测试"""

import json
from unittest.mock import AsyncMock

import pytest

from mindflow_map.ai.intent import IntentParser
from mindflow_map.ai.llm import LLMClient


@pytest.fixture
def mock_llm_client():
    client = AsyncMock(spec=LLMClient)
    client.api_key = "test-api-key"
    return client


@pytest.mark.asyncio
async def test_parse_map_search(mock_llm_client):
    mock_llm_client.chat.return_value = json.dumps({
        "type": "map",
        "action": "search",
        "description": "搜索附近的咖啡厅",
        "confidence": 0.9,
        "entities": {"query": "附近的咖啡厅"},
    })

    parser = IntentParser(llm=mock_llm_client)
    result = await parser.parse("查一下附近的咖啡厅")

    assert result["type"] == "map"
    assert result["action"] == "search"
    assert result["confidence"] == 0.9


@pytest.mark.asyncio
async def test_parse_map_navigate(mock_llm_client):
    mock_llm_client.chat.return_value = json.dumps({
        "type": "map",
        "action": "navigate",
        "description": "导航到天安门",
        "confidence": 0.95,
        "entities": {"destination": "天安门"},
    })

    parser = IntentParser(llm=mock_llm_client)
    result = await parser.parse("怎么去天安门")

    assert result["type"] == "map"
    assert result["action"] == "navigate"
    assert result["entities"]["destination"] == "天安门"


@pytest.mark.asyncio
async def test_parse_douyin_publish(mock_llm_client):
    mock_llm_client.chat.return_value = json.dumps({
        "type": "douyin",
        "action": "publish",
        "description": "发布短剧《xxx》",
        "confidence": 0.85,
        "entities": {"title": "霸道总裁爱上我"},
    })

    parser = IntentParser(llm=mock_llm_client)
    result = await parser.parse("帮我发一个短剧《霸道总裁爱上我》")

    assert result["type"] == "douyin"
    assert result["action"] == "publish"
    assert result["entities"]["title"] == "霸道总裁爱上我"


@pytest.mark.asyncio
async def test_parse_shopify_optimize(mock_llm_client):
    mock_llm_client.chat.return_value = json.dumps({
        "type": "shopify",
        "action": "optimize",
        "description": "优化 Shopify 店铺",
        "confidence": 0.8,
    })

    parser = IntentParser(llm=mock_llm_client)
    result = await parser.parse("优化我的 Shopify 店铺")

    assert result["type"] == "shopify"
    assert result["action"] == "optimize"


@pytest.mark.asyncio
async def test_parse_chat_fallback(mock_llm_client):
    mock_llm_client.chat.return_value = json.dumps({
        "type": "chat",
        "action": "reply",
        "description": "普通对话",
        "confidence": 0.5,
    })

    parser = IntentParser(llm=mock_llm_client)
    result = await parser.parse("你好")

    assert result["type"] == "chat"


@pytest.mark.asyncio
async def test_parse_llm_failure_falls_back_to_rules(mock_llm_client):
    """LLM 失败时回退到规则引擎"""
    mock_llm_client.chat.side_effect = Exception("API 调用失败")

    parser = IntentParser(llm=mock_llm_client)
    result = await parser.parse("怎么去中关村")

    # 应该回退到规则引擎，返回 map/navigate
    assert result["type"] == "map"
    assert result["action"] == "navigate"


@pytest.mark.asyncio
async def test_parse_llm_returns_markdown_code_block(mock_llm_client):
    """兼容 LLM 返回 markdown code block 的情况"""
    mock_llm_client.chat.return_value = "```json\n" + json.dumps({
        "type": "map",
        "action": "search",
        "description": "搜索中关村",
        "confidence": 0.9,
    }) + "\n```"

    parser = IntentParser(llm=mock_llm_client)
    result = await parser.parse("查一下中关村")

    assert result["type"] == "map"
    assert result["action"] == "search"


@pytest.mark.asyncio
async def test_parse_no_api_key_falls_back_immediately():
    """没有配置 API key 时直接回退规则引擎"""
    parser = IntentParser()
    # conftest 已 mock API key，直接走规则引擎
    result = await parser.parse("查一下中关村")
    assert result["type"] == "map"
    assert result["action"] == "search"
