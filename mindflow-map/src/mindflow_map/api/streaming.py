"""SSE 流式工作流执行 API"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from mindflow_map.workflows.engine import WorkflowEngine

logger = logging.getLogger(__name__)

router = APIRouter()
# workflow_engine 由 main.py lifespan 注入


async def _stream_workflow_execution(text: str, user_id: str) -> AsyncGenerator[str, None]:
    """流式执行工作流并推送进度事件。"""
    engine: WorkflowEngine | None = getattr(router, "_workflow_engine", None)
    if engine is None:
        yield f"event: error\ndata: {json.dumps({'error': 'Workflow engine not initialized'})}\n\n"
        return

    try:
        yield f"event: start\ndata: {json.dumps({'text': text, 'user_id': user_id})}\n\n"

        user_context, intent = await asyncio.gather(
            engine._get_user_context(user_id),
            engine.intent_parser.parse(text),
        )
        yield f"event: intent\ndata: {json.dumps({'intent': intent})}\n\n"

        tool_name = engine._select_tool(intent)
        tool = engine.tools.get(tool_name) if tool_name else None

        if not tool:
            yield f"event: result\ndata: {json.dumps({'status': 'no_tool', 'intent': intent})}\n\n"
            yield f"event: done\ndata: {json.dumps({'success': True})}\n\n"
            return

        params = engine._build_params(intent, text, user_context)

        async def _run_tool() -> Dict[str, Any]:
            return await tool.execute(params)

        result = await _run_tool()
        yield f"event: result\ndata: {json.dumps({'status': 'completed', 'result': result})}\n\n"

        reply = engine._format_reply(result, intent)
        yield f"event: message\ndata: {json.dumps({'text': reply})}\n\n"
        yield f"event: done\ndata: {json.dumps({'success': True})}\n\n"

    except Exception as exc:  # noqa: BLE001
        logger.error("SSE workflow execution failed: %s", exc)
        yield f"event: error\ndata: {json.dumps({'error': str(exc)})}\n\n"
        yield f"event: done\ndata: {json.dumps({'success': False})}\n\n"


class StreamWorkflowRequest(BaseModel):
    text: str
    user_id: str = "default"


@router.post("/stream")
async def stream_workflow(request: StreamWorkflowRequest):
    """流式执行工作流，返回 SSE 事件流。"""
    return StreamingResponse(
        _stream_workflow_execution(request.text, request.user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
