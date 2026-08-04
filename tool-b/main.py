"""ToolB — 代码优化/验证服务（端口 8082）

接收 ToolA 生成的代码，进行优化和验证。
Orchestrator 调用: POST /v1/optimize {requirement, task_id, tool_a_result}
"""
from fastapi import FastAPI
from pydantic import BaseModel
import os
import httpx
import logging

logger = logging.getLogger("tool-b")

app = FastAPI(title="ToolB — Code Optimizer")


class OptimizeRequest(BaseModel):
    requirement: str
    task_id: str
    tool_a_result: dict


class OptimizeResponse(BaseModel):
    task_id: str
    original_code: str
    optimized_code: str
    suggestions: list[str]
    status: str


@app.get("/health")
async def health():
    return {"status": "ok", "service": "tool-b", "version": "0.1.0"}


@app.post("/v1/optimize", response_model=OptimizeResponse)
async def optimize(req: OptimizeRequest):
    """Optimize and validate code from ToolA."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
    model = os.getenv("TOOL_B_MODEL", "deepseek-chat")

    original_code = req.tool_a_result.get("code", "")

    if not api_key:
        logger.warning("ToolB: no API key configured, returning stub response")
        return OptimizeResponse(
            task_id=req.task_id,
            original_code=original_code,
            optimized_code=original_code,
            suggestions=["No LLM configured — optimization skipped"],
            status="stub",
        )

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{base_url}/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are a code reviewer. Output optimized code and a list of suggestions."},
                        {"role": "user", "content": f"Optimize this code:\n```\n{original_code}\n```\n\nRequirement: {req.requirement}"},
                    ],
                    "max_tokens": 2048,
                },
            )
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return OptimizeResponse(
                task_id=req.task_id,
                original_code=original_code,
                optimized_code=content or original_code,
                suggestions=["Optimization applied via LLM"],
                status="optimized",
            )
    except Exception as e:
        logger.error("ToolB optimization failed: %s", e)
        return OptimizeResponse(
            task_id=req.task_id,
            original_code=original_code,
            optimized_code=original_code,
            suggestions=[f"Error: {str(e)}"],
            status="error",
        )
