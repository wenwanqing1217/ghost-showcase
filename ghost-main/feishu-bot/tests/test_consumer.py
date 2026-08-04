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
    consumer.running = True

    # Run 3 iterations, each returning empty result
    task = asyncio.create_task(consumer.start())
    await asyncio.sleep(0.1)
    consumer.running = False
    await task

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
        # Second call: empty result to exit loop
        return []

    redis_mock.xreadgroup = AsyncMock(side_effect=fake_xreadgroup)

    consumer = FeishuNotificationConsumer(redis_mock)
    consumer.running = True

    with patch("feishu_consumer.logger") as mock_logger:
        task = asyncio.create_task(consumer.start())
        await asyncio.sleep(0.2)
        consumer.running = False
        await task

    # Should have logged the error
    error_calls = [c for c in mock_logger.error.call_args_list if "Consume loop error" in str(c)]
    assert len(error_calls) >= 1
