"""Multi-level approval form system."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from mindflow_map.models.approval_store import SQLApprovalStore
from mindflow_map.models.session import get_session
from mindflow_map.schemas.approval import (
    ApprovalDecisionRequest,
    ApprovalDefinition,
    ApprovalHistoryItem,
    ApprovalLevel,
    ApprovalStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class CreateApprovalRequest(BaseModel):
    workflow_id: str
    requester_id: str
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    levels: List[ApprovalLevel] = Field(..., min_length=1)
    payload: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", status_code=201)
async def create_approval(
    request: CreateApprovalRequest,
    session: AsyncSession = Depends(get_session),
) -> ApprovalDefinition:
    approval_id = f"apr_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    approval = ApprovalDefinition(
        approval_id=approval_id,
        workflow_id=request.workflow_id,
        requester_id=request.requester_id,
        title=request.title,
        description=request.description,
        levels=request.levels,
        payload=request.payload,
        created_at=now,
    )
    store = SQLApprovalStore(session)
    result = await store.create(approval)
    logger.info("Approval created: %s by %s", approval_id, request.requester_id)
    return result


@router.get("")
async def list_approvals(
    status: Optional[str] = Query(None, description="Filter by status: pending, approved, rejected, cancelled"),
    session: AsyncSession = Depends(get_session),
) -> List[ApprovalDefinition]:
    status_enum = None
    if status:
        try:
            status_enum = ApprovalStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    store = SQLApprovalStore(session)
    return await store.list_by_status(status_enum)


@router.get("/{approval_id}")
async def get_approval(
    approval_id: str,
    session: AsyncSession = Depends(get_session),
) -> ApprovalDefinition:
    store = SQLApprovalStore(session)
    approval = await store.get(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return approval


@router.post("/{approval_id}/decide")
async def decide_approval(
    approval_id: str,
    request: ApprovalDecisionRequest,
    session: AsyncSession = Depends(get_session),
) -> ApprovalDefinition:
    if request.approval_id != approval_id:
        raise HTTPException(status_code=400, detail="Approval ID mismatch")

    store = SQLApprovalStore(session)

    # Pre-checks for proper HTTP status codes
    approval = await store.get(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Approval is already {approval.status}")

    level_def = next((l for l in approval.levels if l.level == approval.current_level), None)
    if not level_def:
        raise HTTPException(status_code=400, detail=f"Invalid level: {approval.current_level}")

    if request.approver_id not in level_def.approver_ids:
        raise HTTPException(status_code=403, detail="You are not authorized for this level")

    result = await store.decide(approval_id, request)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to decide approval")

    logger.info("Approval %s %s by %s at level %s", approval_id, "approved" if request.approved else "rejected", request.approver_id, approval.current_level)
    return result


@router.get("/{approval_id}/history")
async def get_approval_history(
    approval_id: str,
    session: AsyncSession = Depends(get_session),
) -> List[ApprovalHistoryItem]:
    store = SQLApprovalStore(session)
    approval = await store.get(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return await store.get_history(approval_id)
