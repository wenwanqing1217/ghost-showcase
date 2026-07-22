"""短剧平台内容预审 API"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Dict, Optional
import hashlib
import hmac

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from mindflow_map.config import settings
from mindflow_map.memory.store import MemoryStore
from mindflow_map.integration.shortdramas import ShortDramasClient

logger = logging.getLogger(__name__)

router = APIRouter()

# 全局 memory store（懒加载）
_store: Optional[MemoryStore] = None
_store_initialized = False


async def _get_store() -> MemoryStore:
    global _store, _store_initialized
    if _store is None:
        db_url = settings.database_url or "sqlite+aiosqlite:///./mindflow_map.db"
        _store = MemoryStore(database_url=db_url)
    if not _store_initialized:
        await _store.init()
        _store_initialized = True
    return _store


# ---------- 请求/响应模型 ----------

class PrecheckSubmitRequest(BaseModel):
    title: str
    content: str
    content_type: str = "video"
    callback_url: Optional[str] = None


class PrecheckQueryRequest(BaseModel):
    job_id: str


# ---------- 路由 ----------

@router.post("/submit")
async def submit_precheck(request: PrecheckSubmitRequest):
    """提交短剧内容预审"""
    if not settings.shortdramas_api_url or not settings.shortdramas_api_key:
        return {
            "success": False,
            "demo": True,
            "platform": "shortdramas",
            "message": "缺少 SHORTDRAMAS_API_URL / SHORTDRAMAS_API_KEY 配置，当前为演示模式",
            "job_id": f"demo-{uuid.uuid4().hex[:12]}",
            "status": "pending",
        }

    client = ShortDramasClient()
    try:
        result = await client.submit_precheck(
            title=request.title,
            content=request.content,
            content_type=request.content_type,
            callback_url=request.callback_url,
        )
    except Exception as exc:
        logger.error("Submit precheck failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))

    job_id = result.get("job_id", "")
    if job_id:
        try:
            store = await _get_store()
            await store.create_precheck_job(
                job_id=job_id,
                user_id="api-user",
                title=request.title,
                content_type=request.content_type,
                callback_url=request.callback_url,
            )
            await store.update_precheck_job(
                job_id,
                platform_status=result.get("platform_status"),
                platform_result=result,
            )
        except Exception as exc:
            logger.warning("Persist precheck job failed: %s", exc)

    return {
        "success": result.get("success", False),
        "platform": "shortdramas",
        "demo": result.get("demo", False),
        **result,
    }


@router.post("/query")
async def query_precheck(request: PrecheckQueryRequest):
    """查询预审任务状态"""
    job_id = request.job_id
    
    # 先查本地缓存
    try:
        store = await _get_store()
        local_job = await store.get_precheck_job(job_id)
        if local_job and local_job.platform_status in ("approved", "rejected"):
            return {
                "success": True,
                "platform": "shortdramas",
                "job_id": job_id,
                "status": local_job.platform_status,
                "platform_result": local_job.platform_result,
                "source": "local_cache",
            }
    except Exception as exc:
        logger.warning("Local precheck query failed: %s", exc)

    if not settings.shortdramas_api_url or not settings.shortdramas_api_key:
        return {
            "success": False,
            "demo": True,
            "platform": "shortdramas",
            "job_id": job_id,
            "status": "unknown",
            "message": "缺少配置，当前为演示模式",
        }

    client = ShortDramasClient()
    try:
        result = await client.query_precheck(job_id)
    except Exception as exc:
        logger.error("Query precheck failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))

    return {
        "success": result.get("success", False),
        "platform": "shortdramas",
        "demo": result.get("demo", False),
        **result,
    }


@router.get("/jobs")
async def list_precheck_jobs(limit: int = 20):
    """获取预审任务列表（演示接口）"""
    try:
        store = await _get_store()
        jobs = await store.list_precheck_jobs("api-user", limit=limit)
        return {
            "success": True,
            "jobs": [
                {
                    "job_id": job.job_id,
                    "title": job.title,
                    "status": job.status,
                    "platform_status": job.platform_status,
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                }
                for job in jobs
            ],
        }
    except Exception as exc:
        logger.error("List precheck jobs failed: %s", exc)
        return {
            "success": False,
            "jobs": [],
            "error": str(exc),
        }


@router.post("/webhook/shortdramas/callback")
async def shortdramas_callback(request: Request):
    """
    短剧平台回调接口
    
    当平台完成人工复核后，会向此地址推送最终结果。
    支持两种回调验证方式：
    1. Header 签名验证：X-Signature
    2. 平台配置的 webhook_secret
    """
    body = await request.body()
    
    # 签名验证
    signature = request.headers.get("X-Signature", "")
    if signature and settings.shortdramas_webhook_secret:
        expected = hmac.new(
            settings.shortdramas_webhook_secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        payload = json.loads(body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    job_id = payload.get("job_id") or payload.get("task_id")
    status = payload.get("status", "")
    platform_result = payload.get("result") or payload.get("platform_result")

    if not job_id:
        raise HTTPException(status_code=400, detail="Missing job_id")

    # 更新本地任务状态
    try:
        store = await _get_store()
        update_data: Dict[str, Any] = {
            "platform_status": status,
            "platform_result": platform_result,
        }
        
        if status == "approved":
            update_data["status"] = "approved"
        elif status == "rejected":
            update_data["status"] = "rejected"
        elif status == "manual_review":
            update_data["status"] = "manual_review"
        
        updated_job = await store.update_precheck_job(job_id, **update_data)
        if updated_job:
            logger.info("Precheck job %s updated to %s via callback", job_id, status)
    except Exception as exc:
        logger.warning("Update precheck job from callback failed: %s", exc)

    return {"success": True, "message": "Callback received"}
