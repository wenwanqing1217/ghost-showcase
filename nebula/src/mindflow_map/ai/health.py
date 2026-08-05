"""LLM 健康检查 — 轻量探测调用，返回延迟与模型信息。"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict

from mindflow_map.ai.llm import LLMClient
from mindflow_map.config import settings

logger = logging.getLogger(__name__)

# 最小探测 prompt，尽量节省 token
_HEALTH_PROMPT = '请回复一个字符: "ok"'


async def check_llm_health() -> Dict[str, Any]:
    """对已配置的 LLM 执行一次最小化探测调用。"""
    api_key = (settings.openai_api_key or "").strip()
    if not api_key or api_key.startswith("your_") or api_key.endswith("_key"):
        return {"status": "not_configured"}

    client = LLMClient()
    start = time.perf_counter()

    try:
        await client.chat(
            messages=[{"role": "user", "content": _HEALTH_PROMPT}],
            temperature=0.0,
            max_tokens=4,
        )
        latency_ms = (time.perf_counter() - start) * 1000.0
        return {
            "status": "ok",
            "latency_ms": round(latency_ms, 1),
            "model": client.model,
        }

    except Exception as exc:
        logger.debug("LLM health check failed: %s", exc)
        return {"status": "error", "error": str(exc)}
