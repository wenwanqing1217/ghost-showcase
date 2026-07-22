"""Test config: mock LLM for fast tests."""
import pytest
from unittest.mock import patch

@pytest.fixture(autouse=True)
def mock_llm_api_key():
    with patch("mindflow_map.config.settings.openai_api_key", ""), patch("mindflow_map.config.settings.model_fallbacks", []):
        yield
