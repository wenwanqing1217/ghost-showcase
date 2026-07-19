"""LLM 客户端，支持 DeepSeek / 豆包等 OpenAI 兼容接口"""

from openai import AsyncOpenAI

from mindflow_map.config import settings


class LLMClient:
    """LLM 客户端"""

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self.model = settings.ai_model or "deepseek-chat"
        self.api_key = settings.openai_api_key or ""

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 256,
    ) -> str:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY 未配置，无法调用 LLM")

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        choice = response.choices[0]
        return choice.message.content or ""
