"""LLM 客户端，支持多 Provider 自动回退（DeepSeek / 豆包 / Moonshot 等 OpenAI 兼容接口）"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

from mindflow_map.config import settings

logger = logging.getLogger(__name__)


class LLMModel:
    """单个模型端点配置。"""

    def __init__(self, base_url: str, api_key: str, model: str, label: str = "") -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.label = label or model
        self.client = AsyncOpenAI(api_key=api_key, base_url=self.base_url)

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and not self.api_key.startswith("your_"))

    def __repr__(self) -> str:
        return f"LLMModel({self.label}@{self.base_url})"


class LLMClient:
    """LLM 客户端，带多模型自动回退与指数退避重试。

    调用逻辑：
    1. 优先使用主模型（由 .env OPENAI_BASE_URL / OPENAI_API_KEY / AI_MODEL 决定）
    2. 主模型失败（超时、429、503 等）时，按 model_fallbacks 顺序尝试下一个
    3. 每个模型自带 2 次指数退避重试（避免单模型瞬断）
    4. 全部失败时抛出 RuntimeError，携带失败摘要
    """

    def __init__(self) -> None:
        self._models: List[LLMModel] = self._build_model_chain()
        # 方便外部访问的主模型属性（向后兼容）
        primary = self._models[0] if self._models else None
        self.model: str = primary.model if primary else (settings.ai_model or "deepseek-chat")
        self.api_key: str = primary.api_key if primary else ""
        self._timeout: float = float(getattr(settings, "llm_timeout", 10.0) or 10.0)
        self._max_retries_per_model: int = int(getattr(settings, "llm_max_retries", 2) or 2)

    # --- 向后兼容属性（旧代码通过 client / api_key 访问） ---

    @property
    def client(self) -> AsyncOpenAI:
        """返回主模型的 OpenAI 客户端，兼容旧代码直接访问 client 属性的写法。"""
        if self._models:
            return self._models[0].client
        # 没有配置任何模型时，返回一个指向 settings 的占位客户端（调用时会报错）
        return AsyncOpenAI(api_key=self.api_key, base_url=settings.openai_base_url)

    @client.setter
    def client(self, value: AsyncOpenAI) -> None:
        """允许测试直接注入 mock 客户端，同时保持 api_key 一致。"""
        if self._models:
            self._models[0].client = value
        else:
            stub = LLMModel(
                base_url=settings.openai_base_url,
                api_key=self.api_key or "injected",
                model=self.model,
                label="injected",
            )
            stub.client = value
            self._models.append(stub)

    # ------------------------------------------------------------------ #
    # 内部工具
    # ------------------------------------------------------------------ #

    def _build_model_chain(self) -> List[LLMModel]:
        """从 Settings 组装有序模型链：主模型 + 回退列表。"""
        models: List[LLMModel] = []

        # 主模型
        primary_key = (settings.openai_api_key or "").strip()
        primary_url = (settings.openai_base_url or "https://api.deepseek.com/v1").strip()
        primary_model = (settings.ai_model or "deepseek-chat").strip()
        if primary_key and not primary_key.startswith("your_"):
            models.append(LLMModel(primary_url, primary_key, primary_model, label=f"primary:{primary_model}"))

        # 回退模型
        for idx, fb in enumerate(settings.model_fallbacks):
            fb_key = (fb.get("api_key") or "").strip()
            fb_url = (fb.get("base_url") or "").strip()
            fb_model = (fb.get("model") or "").strip()
            if not fb_key or fb_key.startswith("your_"):
                continue
            if not fb_url or not fb_model:
                continue
            # 跳过与主模型完全相同的配置，避免无意义重复
            if fb_url.rstrip("/") == primary_url.rstrip("/") and fb_model == primary_model:
                continue
            models.append(LLMModel(fb_url, fb_key, fb_model, label=f"fallback[{idx}]:{fb_model}"))

        return models

    @staticmethod
    def _is_retriable(exc: Exception) -> bool:
        """判断异常是否值得回退到下一个模型。

        4xx 中仅 429（限流）视为可回退；其他 4xx（401/403/400）直接抛错。
        超时、连接错误、5xx 等均视为可回退。
        """
        status = getattr(exc, "status_code", None)
        if status is not None:
            if status == 429:
                return True
            if 400 <= status < 500:
                return False  # 认证错误等，下一个 provider 也一样会失败
            if status >= 500:
                return True
        # asyncio.TimeoutError、网络错误等
        return True

    # ------------------------------------------------------------------ #
    # 公开 API
    # ------------------------------------------------------------------ #

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 256,
    ) -> str:
        """发送聊天请求。

        依次尝试模型链中的每个模型：
        - 当前模型内部做指数退避重试
        - 超时/限流/5xx 时回退到下一个模型
        - 最终成功时打印使用了第几个模型（方便排错）
        """
        if not self._models:
            raise RuntimeError(
                "没有可用的 LLM 模型 —— 请检查 .env 中 OPENAI_API_KEY 和 MODEL_FALLBACKS 配置"
            )

        last_exc: Exception | None = None
        fallback_count = 0

        for model_idx, model in enumerate(self._models):
            if model_idx > 0:
                fallback_count += 1
                logger.warning(
                    "🔄 LLM 回退 #%d：尝试 %s（前一个失败：%s）",
                    fallback_count,
                    model.label,
                    last_exc,
                )

            # 单模型内部重试（指数退避）
            for attempt in range(1, self._max_retries_per_model + 1):
                try:
                    t0 = time.perf_counter()
                    response = await asyncio.wait_for(
                        model.client.chat.completions.create(
                            model=model.model,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                        ),
                        timeout=self._timeout,
                    )
                    latency = (time.perf_counter() - t0) * 1000.0
                    choice = response.choices[0]
                    content = choice.message.content or ""

                    if fallback_count > 0:
                        logger.info(
                            "✅ LLM 调用成功（经过 %d 次回退，耗时 %.0fms）：%s",
                            fallback_count,
                            latency,
                            model.label,
                        )
                    return content

                except asyncio.TimeoutError:
                    last_exc = asyncio.TimeoutError(f"{model.label} 调用超时（>{self._timeout}s）")
                    logger.warning(
                        "⏱️  %s 超时（attempt %d/%d）",
                        model.label, attempt, self._max_retries_per_model,
                    )

                except Exception as exc:
                    last_exc = exc
                    if not self._is_retriable(exc):
                        # 认证错误等不可回退的情况，直接抛出
                        raise
                    logger.warning(
                        "⚠️  %s 失败（attempt %d/%d）：%s",
                        model.label, attempt, self._max_retries_per_model, exc,
                    )

                if attempt < self._max_retries_per_model:
                    backoff = 2 ** (attempt - 1)
                    await asyncio.sleep(backoff)

            # 当前模型已耗尽重试，继续下一个模型（循环顶部的 warning 会打印回退信息）

        # 所有模型都失败了
        raise RuntimeError(
            f"LLM 调用失败 —— 已尝试 {len(self._models)} 个模型，全部失败。最后一个错误：{last_exc}"
        ) from last_exc
