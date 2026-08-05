"""Feishu Notification Routes — /v1/notify/*
=============================================
REST API for sending Feishu notifications from any backend service.

Architecture:
  Event Bus Consumer → Gateway /v1/notify/send → Feishu Bot → Feishu API

This route enables any service (Nebula, DS webhook, AlphaID) to send
Feishu notifications without directly importing the Feishu SDK.

Routes:
  POST /v1/notify/send         — Send a text message
  POST /v1/notify/card         — Send an interactive card
  POST /v1/notify/approval     — Send an approval request
  GET  /v1/notify/status       — Get Feishu service status
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from services.proxy import fail, ok

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/notify", tags=["notify"])


# ── Request Schemas ──


class SendMessageRequest(BaseModel):
    """Send a text message to a Feishu user."""
    user_id: str = Field(..., description="Feishu user open_id or user_id")
    content: str = Field(..., description="Message text content")
    user_id_type: str = Field("open_id", description="ID type: open_id | user_id | chat_id")


class SendCardRequest(BaseModel):
    """Send an interactive card message."""
    user_id: str = Field(...)
    title: str = Field(...)
    content: str = Field(...)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    user_id_type: str = Field("open_id")


class SendNotificationRequest(BaseModel):
    """Send a structured notification."""
    user_id: str = Field(...)
    notification_type: str = Field(..., description="Notification type enum value")
    title: str = Field("")
    body: str = Field("")
    data: Dict[str, Any] = Field(default_factory=dict)
    priority: str = Field("normal")
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    user_id_type: str = Field("open_id")


class SendApprovalRequest(BaseModel):
    """Send an approval request."""
    approver_id: str = Field(...)
    approval_id: str = Field(...)
    title: str = Field(...)
    description: str = Field(...)
    requester: str = Field(...)
    data: Dict[str, Any] = Field(default_factory=dict)
    actions: List[Dict[str, Any]] = Field(default_factory=list)


class BroadcastRequest(BaseModel):
    """Broadcast notification to multiple users."""
    user_ids: List[str] = Field(..., min_items=1)
    notification_type: str = Field(...)
    title: str = Field("")
    body: str = Field("")
    data: Dict[str, Any] = Field(default_factory=dict)


# ── Helpers ──


def _get_feishu_service():
    """Get or import the Feishu service from feishu-bot."""
    try:
        # Try importing from the feishu-bot container
        # In Docker, this works because feishu-bot shares the codebase
        sys_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        feishu_bot_path = os.path.join(sys_path, "ghost-main", "feishu-bot")
        if feishu_bot_path not in __import__("sys").path:
            __import__("sys").path.insert(0, feishu_bot_path)

        from feishu_service import get_feishu_service
        return get_feishu_service()
    except (ImportError, Exception) as e:
        logger.warning("FeishuService not available: %s", e)
        return None


# ── Routes ──


@router.post("/send")
async def send_message(request: Request, body: SendMessageRequest):
    """Send a text message to a Feishu user."""
    service = _get_feishu_service()
    if not service:
        return fail("Feishu service not available", 503, request)

    result = await service.send_message(
        receive_id=body.user_id,
        content=body.content,
        receive_id_type=body.user_id_type,
    )
    return ok(result, request)


@router.post("/card")
async def send_card(request: Request, body: SendCardRequest):
    """Send an interactive card to a Feishu user."""
    service = _get_feishu_service()
    if not service:
        return fail("Feishu service not available", 503, request)

    result = await service.send_card(
        receive_id=body.user_id,
        title=body.title,
        content=body.content,
        actions=body.actions,
        receive_id_type=body.user_id_type,
    )
    return ok(result, request)


@router.post("/notify")
async def send_notification(request: Request, body: SendNotificationRequest):
    """Send a structured notification to a Feishu user."""
    service = _get_feishu_service()
    if not service:
        return fail("Feishu service not available", 503, request)

    try:
        from feishu_service import NotificationType
        ntype = NotificationType(body.notification_type)
    except (ImportError, ValueError):
        ntype = None

    result = await service.notify(
        receive_id=body.user_id,
        notification_type=ntype or body.notification_type,
        title=body.title,
        body=body.body,
        data=body.data,
        priority=body.priority,
        actions=body.actions,
        receive_id_type=body.user_id_type,
    )
    return ok(result, request)


@router.post("/approval")
async def send_approval(request: Request, body: SendApprovalRequest):
    """Send an approval request to a Feishu user."""
    service = _get_feishu_service()
    if not service:
        return fail("Feishu service not available", 503, request)

    from feishu_service import ApprovalRequest, ApprovalType

    # Try to resolve the approval type
    try:
        atype = ApprovalType(body.data.get("approval_type", body.title))
    except ValueError:
        atype = ApprovalType.SUPPLY_SOURCE_CONNECT

    approval = ApprovalRequest(
        approval_id=body.approval_id,
        type=atype,
        title=body.title,
        description=body.description,
        requester=body.requester,
        data=body.data,
        actions=body.actions,
    )

    result = await service.send_approval(
        approver_id=body.approver_id,
        request=approval,
    )
    return ok(result, request)


@router.post("/broadcast")
async def broadcast_notification(request: Request, body: BroadcastRequest):
    """Broadcast notification to multiple users."""
    service = _get_feishu_service()
    if not service:
        return fail("Feishu service not available", 503, request)

    try:
        from feishu_service import NotificationType
        ntype = NotificationType(body.notification_type)
    except (ImportError, ValueError):
        ntype = body.notification_type

    results = await service.broadcast(
        receive_ids=body.user_ids,
        notification_type=ntype,
        title=body.title,
        body=body.body,
        data=body.data,
    )
    return ok({"sent": len(results), "results": results}, request)


@router.get("/status")
async def feishu_status(request: Request):
    """Get Feishu service status."""
    service = _get_feishu_service()
    if not service:
        return ok({"enabled": False, "error": "Feishu service not loaded"}, request)
    return ok(service.get_status(), request)
