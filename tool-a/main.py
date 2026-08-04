"""ToolA — 代码生成服务（端口 8081）

接收需求描述，通过 LLM 生成代码。
Orchestrator 调用: POST /v1/generate {requirement, task_id}
"""
from fastapi import FastAPI
from pydantic import BaseModel
import os
import httpx
import logging

logger = logging.getLogger("tool-a")

app = FastAPI(title="ToolA — Code Generator")


class GenerateRequest(BaseModel):
    requirement: str
    task_id: str


class GenerateResponse(BaseModel):
    task_id: str
    code: str
    language: str
    status: str


@app.get("/health")
async def health():
    return {"status": "ok", "service": "tool-a", "version": "0.1.0"}


@app.post("/v1/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    """Generate code from requirement description using LLM."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
    model = os.getenv("TOOL_A_MODEL", "deepseek-chat")

    if not api_key:
        logger.warning("ToolA: no API key configured, returning stub response")
        return GenerateResponse(
            task_id=req.task_id,
            code=f"# TODO: implement {req.requirement}\n# (no LLM configured)",
            language="python",
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
                        {"role": "system", "content": "You are a code generator. Output only code, no explanation."},
                        {"role": "user", "content": f"Generate code for: {req.requirement}"},
                    ],
                    "max_tokens": 2048,
                },
            )
            text = resp.text[:500]
            try:
                data = resp.json()
                code = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return GenerateResponse(
                    task_id=req.task_id,
                    code=code or f"# Empty response for: {req.requirement}",
                    language="python",
                    status="generated",
                )
            except Exception:
                logger.error("ToolA LLM returned non-JSON (status=%s): %s", resp.status_code, text)
                return GenerateResponse(
                    task_id=req.task_id,
                    code=f"# LLM error (HTTP {resp.status_code}): {text[:200]}",
                    language="python",
                    status="error",
                )
    except Exception as e:
        logger.error("ToolA generation failed: %s", e)
        return GenerateResponse(
            task_id=req.task_id,
            code=f"# Error: {str(e)}",
            language="python",
            status="error",
        )
