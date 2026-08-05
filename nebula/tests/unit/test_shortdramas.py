"""短剧内容预审工作流与 API 测试"""

from unittest.mock import AsyncMock, patch

import pytest

from mindflow_map.workflows.engine import WorkflowEngine


@pytest.fixture
def engine():
    return WorkflowEngine()


@pytest.mark.asyncio
async def test_precheck_intent_triggered_by_keywords(engine):
    """预审关键词应触发 shortdramas 意图"""
    result = await engine.execute("预审一下《霸道总裁爱上我》能不能发", user_id="test-user")
    assert result["intent"]["type"] == "shortdramas"
    assert result["intent"]["action"] == "precheck"
    assert result["intent"]["title"] == "霸道总裁爱上我"


@pytest.mark.asyncio
async def test_precheck_intent_fallback_without_title(engine):
    """预审关键词无标题时仍触发短剧意图"""
    result = await engine.execute("帮我审核一下这段内容", user_id="test-user")
    assert result["intent"]["type"] == "shortdramas"
    assert result["intent"]["action"] == "precheck"


@pytest.mark.asyncio
async def test_precheck_tool_returns_blocked_when_ai_scanner_blocks(engine):
    """当 AI 预扫描返回 blocked 时，工具应直接拒绝"""
    blocked_result = {
        "risk_level": "blocked",
        "violations": ["色情低俗内容"],
        "suggestions": ["请修改"],
        "summary": "包含违规内容",
    }

    with patch("mindflow_map.integration.shortdramas.AIContentScanner.scan", new_callable=AsyncMock) as mock_scan:
        mock_scan.return_value = blocked_result
        with patch("mindflow_map.integration.shortdramas.ShortDramasClient.submit_precheck", new_callable=AsyncMock) as mock_submit:
            result = await engine.execute("预审《违规内容》", user_id="test-user")
            assert result["intent"]["type"] == "shortdramas"
            assert result["result"]["type"] == "shortdramas"
            assert result["result"]["data"]["status"] == "rejected"
            assert result["result"]["data"]["rejected_by"] == "ai_local"
            assert "色情低俗内容" in result["text"]
            mock_submit.assert_not_called()


@pytest.mark.asyncio
async def test_precheck_tool_returns_pending_when_ai_passes(engine):
    """当 AI 预扫描通过时，工具应提交到平台"""
    ai_result = {
        "risk_level": "safe",
        "violations": [],
        "suggestions": [],
        "summary": "内容安全",
    }
    platform_result = {
        "success": True,
        "job_id": "job-123",
        "status": "pending",
        "platform_status": "queued",
        "demo": True,
        "message": "演示模式",
    }

    with patch("mindflow_map.integration.shortdramas.AIContentScanner.scan", new_callable=AsyncMock) as mock_scan:
        mock_scan.return_value = ai_result
        with patch("mindflow_map.integration.shortdramas.ShortDramasClient.submit_precheck", new_callable=AsyncMock) as mock_submit:
            mock_submit.return_value = platform_result
            result = await engine.execute("预审《我的短剧》", user_id="test-user")
            assert result["intent"]["type"] == "shortdramas"
            assert result["result"]["type"] == "shortdramas"
            assert result["result"]["data"]["job_id"] == "job-123"
            assert result["result"]["data"]["status"] == "pending"
            mock_submit.assert_called_once()
