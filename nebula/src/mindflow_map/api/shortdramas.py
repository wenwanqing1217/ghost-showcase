"""短剧平台内容预审 API"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from mindflow_map.config import settings
from mindflow_map.integration.shortdramas import ShortDramasClient

router = APIRouter()


class ShortDramasSubmitRequest(BaseModel):
    title: str
    content: str
    content_type: str = "video"
    callback_url: Optional[str] = None


class ShortDramasQueryRequest(BaseModel):
    job_id: str


# 演示模式下的内存任务存储
_demo_jobs: Dict[str, Dict[str, Any]] = {}


@router.post("/submit")
async def shortdramas_submit(request: ShortDramasSubmitRequest):
    """提交短剧内容预审"""
    client = ShortDramasClient()
    try:
        # 未配置 API 时返回演示模式
        if not settings.shortdramas_api_url:
            job_id = f"demo-{uuid.uuid4().hex[:12]}"
            _demo_jobs[job_id] = {
                "title": request.title,
                "status": "pending",
                "created_at": time.time(),
            }
            return {
                "success": True,
                "demo": True,
                "job_id": job_id,
                "status": "pending",
                "message": "演示模式：未配置 SHORTDRAMAS_API_URL",
            }

        result = await client.submit_precheck(
            title=request.title,
            content=request.content,
            content_type=request.content_type,
            callback_url=request.callback_url,
        )
        return result
    finally:
        await client.close()


@router.post("/query")
async def shortdramas_query(request: ShortDramasQueryRequest):
    """查询短剧预审任务状态"""
    client = ShortDramasClient()
    try:
        # 未配置 API 时返回演示模式
        if not settings.shortdramas_api_url:
            job = _demo_jobs.get(request.job_id)
            if job:
                return {
                    "success": True,
                    "demo": True,
                    "job_id": request.job_id,
                    "status": job["status"],
                }
            return {
                "success": True,
                "demo": True,
                "job_id": request.job_id,
                "status": "unknown",
            }

        result = await client.query_precheck(job_id=request.job_id)
        return result
    finally:
        await client.close()


@router.get("/jobs")
async def shortdramas_list_jobs():
    """列出所有预审任务（仅演示模式）"""
    return {
        "success": True,
        "demo": True,
        "jobs": [
            {"job_id": k, **v}
            for k, v in _demo_jobs.items()
        ],
    }
