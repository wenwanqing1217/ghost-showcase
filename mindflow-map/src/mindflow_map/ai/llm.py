"""LLM 客户端，支持 DeepSeek / 豆包等 OpenAI 兼容接口"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from openai import AsyncOpenAI

from mindflow_map.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM 客户端，带可配置超时与指数退避重试。"""

    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self.model: str = settings.ai_model or "deepseek-chat"
        self.api_key: str = settings.openai_api_key or ""
        # 超时 / 重试配置：优先用 Settings，其次读环境变量
        self._timeout: float = float(
            getattr(settings, "llm_timeout", 10.0) or 10.0
        )
        self._max_retries: int = int(
            getattr(settings, "llm_max_retries", 3) or 3
        )

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 256,
    ) -> str:
        """发送聊天请求，带超时和指数退避重试。"""
        if not self.api_key or self.api_key.startswith("your_"):
            raise RuntimeError("OPENAI_API_KEY 未配置，无法调用 LLM")

        last_exc: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    ),
                    timeout=self._timeout,
                )
                choice = response.choices[0]
                return choice.message.content or ""

            except asyncio.TimeoutError:
                last_exc = asyncio.TimeoutError(
                    f"LLM 调用超时（>{self._timeout}s）"
                )
                logger.warning(
                    "LLM 调用超时，attempt %d/%d", attempt, self._max_retries
                )

            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                status_code = getattr(
                    getattr(exc, "status_code", None), "value", None
                ) or getattr(exc, "status_code", None)
                if status_code is not None and 400 <= status_code < 500:
                    raise
                logger.warning(
                    "LLM 调用失败（attempt %d/%d）：%s",
                    attempt,
                    self._max_retries,
                    exc,
                )

            if attempt < self._max_retries:
                backoff = 2 ** (attempt - 1)
                await asyncio.sleep(backoff)

        raise RuntimeError(
            f"LLM 调用失败，已重试 {self._max_retries} 次: {last_exc}"
        ) from last_exc

