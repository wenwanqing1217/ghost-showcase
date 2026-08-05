"""基于 LLM 的意图识别，失败时 fallback 到规则引擎"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, Optional

from mindflow_map.ai.circuit_breaker import CircuitBreaker
from mindflow_map.ai.llm import LLMClient

logger = logging.getLogger(__name__)

_INTENT_SYSTEM_PROMPT = """\
你是 MindFlow 工作流引擎的意图分类器。请根据用户消息，返回最匹配的意图 JSON。

type 和 action 是两个独立的字段，不要合并成斜杠格式。

可用的 type 值（与 action 配合使用）：
- type="map"        + action="search"   \u2192 搜索地点，如"查一下附近的咖啡厅"
- type="map"        + action="navigate" \u2192 路线导航，如"怎么去天安门"
- type="douyin"     + action="publish"  \u2192 发布短剧，如"帮我发一个短剧《xxx》"
- type="shopify"    + action="optimize" \u2192 店铺优化，如"优化我的 Shopify 店铺"
- type="shortdramas" + action="precheck" \u2192 内容预审，如"预审一下《xxx》能不能发"
- type="channel_copy" + action="generate" \u2192 生成闲鱼/小红书文案，如"帮我写个闲鱼文案卖香薰""帮我写小红书种草笔记"
- type="video_generate" + action="create" \u2192 生成视频，如"帮我做个视频""生成一个香薰种草视频"
- type="video_publish" + action="upload" \u2192 发布视频到平台，如"把视频发到 TikTok""发布视频 abc123"
- type="chat"       + action="reply"    \u2192 普通对话，以上都不是

严格返回 JSON，不要额外文字：
{
  "type": "type 值（必填，不带斜杠）",
  "action": "action 值（必填）",
  "description": "一句话描述用户想做什么",
  "confidence": 0.0-1.0,
  "entities": {
    "query": "地点搜索词（map/search 需要）",
    "destination": "目的地（map/navigate 需要）",
    "title": "标题（douyin/shortdramas/channel_copy/video_generate 需要）",
    "description": "卖点描述（channel_copy 可选）",
    "price": "价格（channel_copy 可选）",
    "condition": "成色（channel_copy 可选）",
    "task_id": "视频任务 ID（video_publish 需要）",
    "platforms": "发布平台，逗号分隔（video_publish 可选，默认 tiktok）"
  }
}
"""


class IntentParser:
    """基于 LLM 的意图识别器，失败时 fallback 到规则引擎。"""

    def __init__(
        self,
        llm: Optional[LLMClient] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
    ) -> None:
        self.llm = llm or LLMClient()
        self._fallback_parser: Any = None
        self._circuit_breaker = circuit_breaker or CircuitBreaker()

    def _get_fallback(self):
        if self._fallback_parser is None:
            from mindflow_map.ai.fallback_rules import parse_by_rules
            self._fallback_parser = parse_by_rules
        return self._fallback_parser

    @staticmethod
    def _normalize_intent(intent: Dict[str, Any]) -> Dict[str, Any]:
        """标准化意图字典：处理 LLM 可能返回的斜杠格式。"""
        raw_type = intent.get("type", "")
        if "/" in raw_type:
            parts = raw_type.split("/", 1)
            intent["type"] = parts[0]
            if len(parts) > 1 and not intent.get("action"):
                intent["action"] = parts[1]
        return intent

    async def parse(self, text: str) -> Dict[str, Any]:
        api_key = (self.llm.api_key or "").strip()
        if not api_key or api_key.startswith("your_") or api_key.endswith("_key"):
            result = self._get_fallback()(text)
            logger.info("Intent mode=rule (no_api_key) text=%r", text[:50])
            return result

        start = time.perf_counter()

        try:
            content = await self._circuit_breaker.call(
                self.llm.chat,
                messages=[
                    {"role": "system", "content": _INTENT_SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                temperature=0.2,
                max_tokens=128,
            )
        except Exception:
            logger.warning("Intent mode=rule (llm_exception) text=%r", text[:50])
            return self._get_fallback()(text)

        latency_ms = (time.perf_counter() - start) * 1000.0

        if content is None:
            result = self._get_fallback()(text)
            logger.warning(
                "Intent mode=rule (circuit_open|llm_error) "
                "breaker_state=%s latency_ms=%.1f text=%r",
                self._circuit_breaker.state.value,
                latency_ms,
                text[:50],
            )
            return result

        content = content.strip()
        if content.startswith("```"):
            content = content.split("```", 2)[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        try:
            intent: Dict[str, Any] = json.loads(content)
        except json.JSONDecodeError:
            logger.warning(
                "Intent mode=rule (bad_json) content=%r text=%r",
                content[:100], text[:50],
            )
            return self._get_fallback()(text)

        intent.setdefault("confidence", 0.9)
        intent = self._normalize_intent(intent)

        logger.info(
            "Intent mode=llm type=%s latency_ms=%.1f text=%r",
            intent.get("type"),
            latency_ms,
            text[:50],
        )
        return intent

    def _fallback_rule(self, text: str) -> Dict[str, Any]:
        """回退到规则引擎（纯函数，零外部依赖）"""
        parser = self._get_fallback()
        return parser(text)
