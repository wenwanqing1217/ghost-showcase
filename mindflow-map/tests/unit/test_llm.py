"""LLM client tests."""

from __future__ import annotations

import pytest
from openai import AsyncOpenAI
from unittest.mock import AsyncMock, MagicMock, patch

from mindflow_map.ai.llm import LLMClient
from mindflow_map.config import settings


class TestLLMClient:
    """Tests for the real OpenAI-compatible LLM client."""

    def test_client_initializes_with_settings(self):
        client = LLMClient()
        assert client.model == (settings.ai_model or "deepseek-chat")
        assert client.api_key == settings.openai_api_key or ""

    @patch("mindflow_map.ai.llm.AsyncOpenAI")
    async def test_chat_calls_openai_api(self, mock_openai_cls):
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = '{"result": "ok"}'
        mock_response.choices = [mock_choice]

        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        llm = LLMClient()
        llm.client = mock_client
        llm.api_key = "test-key"

        result = await llm.chat(messages=[{"role": "user", "content": "hello"}])

        assert result == '{"result": "ok"}'
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == llm.model
        assert call_kwargs["temperature"] == 0.3
        assert call_kwargs["max_tokens"] == 256

    @patch("mindflow_map.ai.llm.AsyncOpenAI")
    async def test_chat_handles_empty_content(self, mock_openai_cls):
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = None
        mock_response.choices = [mock_choice]

        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        llm = LLMClient()
        llm.client = mock_client
        llm.api_key = "test-key"

        result = await llm.chat(messages=[{"role": "user", "content": "hello"}])
        assert result == ""
