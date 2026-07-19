"""基于 LLM 的意图识别，失败时 fallback 到规则引擎"""

import json
from typing import Any, Dict, Optional

from mindflow_map.ai.llm import LLMClient


_INTENT_SYSTEM_PROMPT = """\
你是 MindFlow 工作流引擎的意图分类器。请根据用户消息，返回最匹配的意图 JSON。

可用意图类型：
- map/search：搜索地点，如"查一下附近的咖啡厅"
- map/navigate：路线导航，如"怎么去天安门"
- douyin/publish：发布短剧，如"帮我发一个短剧《xxx》"
- shopify/optimize：店铺优化，如"优化我的 Shopify 店铺"
- shortdramas/precheck：内容预审，如"预审一下《xxx》能不能发"
- chat：普通对话，以上都不是

严格返回 JSON，不要额外文字：
{
  "type": "意图类型",
  "action": "对应动作",
  "description": "一句话描述用户想做什么",
  "confidence": 0.0-1.0,
  "entities": {
    "query": "地点搜索词（仅 map/search 需要）",
    "destination": "目的地（仅 map/navigate 需要）",
    "title": "短剧标题（仅 douyin/publish 或 shortdramas/precheck 需要）"
  }
}
"""


class IntentParser:
    """基于 LLM 的意图识别器，失败时 fallback 到规则引擎"""

    def __init__(self, llm: Optional[LLMClient] = None):
        self.llm = llm or LLMClient()
        self._fallback_parser: Any = None

    def _get_fallback(self):
        if self._fallback_parser is None:
            from mindflow_map.ai.fallback_rules import parse_by_rules
            self._fallback_parser = parse_by_rules
        return self._fallback_parser

    async def parse(self, text: str) -> Dict[str, Any]:
        api_key = (self.llm.api_key or "").strip()
        if not api_key or api_key.startswith("your_") or api_key.endswith("_key"):
            return self._fallback_rule(text)

        try:
            content = await self.llm.chat(
                messages=[
                    {"role": "system", "content": _INTENT_SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                temperature=0.2,
                max_tokens=128,
            )
            # 兼容 markdown code block 包裹
            content = content.strip()
            if content.startswith("```"):
                content = content.split("```", 2)[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            intent = json.loads(content)
            intent.setdefault("confidence", 0.9)
            return intent
        except Exception:
            return self._fallback_rule(text)

    def _fallback_rule(self, text: str) -> Dict[str, Any]:
        """回退到规则引擎（纯函数，零外部依赖）"""
        parser = self._get_fallback()
        return parser(text)
