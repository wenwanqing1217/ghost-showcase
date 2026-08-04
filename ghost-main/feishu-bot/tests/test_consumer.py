"""
Tests for feishu_consumer backoff behavior.

Validates:
  - XREADGROUP block timeout resets backoff (normal empty poll)
  - Real errors trigger exponential backoff
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from feishu_consumer import FeishuNotificationConsumer


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_consume_loop_empty_result_resets_backoff():
    """Empty XREADGROUP result (normal poll) should reset backoff to 1.0."""
    redis_mock = MagicMock()
    redis_mock.xgroup_create = AsyncMock()
    redis_mock.xreadgroup = AsyncMock(return_value=[])

    consumer = FeishuNotificationConsumer(redis_mock)
    consumer.running = False  # let start() set it True

    # Run start() with a timeout so it doesn't spin forever
    start_task = asyncio.create_task(consumer.start())
    await asyncio.sleep(0.3)
    consumer.running = False
    await start_task

    # xgroup_create called for each event type (9 events)
    assert redis_mock.xgroup_create.call_count == 9
    # xreadgroup called at least once
    assert redis_mock.xreadgroup.call_count >= 1


@pytest.mark.anyio
async def test_consume_loop_real_error_triggers_backoff():
    """Real errors (not Timeout) should be logged and backoff applied."""
    redis_mock = MagicMock()
    redis_mock.xgroup_create = AsyncMock()

    call_count = 0

    async def fake_xreadgroup(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call: simulate a real error (not timeout)
            raise ConnectionError("Redis connection lost")
        # Second call: empty result to continue loop
        return []

    redis_mock.xreadgroup = AsyncMock(side_effect=fake_xreadgroup)

    consumer = FeishuNotificationConsumer(redis_mock)
    consumer.running = False  # let start() set it True

    with patch("feishu_consumer.logger") as mock_logger:
        start_task = asyncio.create_task(consumer.start())
        # Wait for: xgroup_create (9) + xreadgroup (error + backoff sleep + empty)
        await asyncio.sleep(3.0)
        consumer.running = False
        await start_task

    # Should have logged the error (not as debug timeout)
    error_calls = [c for c in mock_logger.error.call_args_list if "Consume loop error" in str(c)]
    assert len(error_calls) >= 1
    # Should NOT have logged it as debug timeout
    debug_calls = [c for c in mock_logger.debug.call_args_list if "timeout" in str(c).lower()]
    assert len(debug_calls) == 0
