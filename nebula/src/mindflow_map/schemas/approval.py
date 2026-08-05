"""Approval request/response models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ApprovalLevel(BaseModel):
    level: int
    approver_ids: List[str]
    timeout_minutes: int = 60


class ApprovalDefinition(BaseModel):
    approval_id: str
    workflow_id: str
    requester_id: str
    title: str
    description: str
    levels: List[ApprovalLevel]
    current_level: int = 1
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    decided_at: Optional[datetime] = None
    decided_by: Optional[str] = None
    comment: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class ApprovalDecisionRequest(BaseModel):
    approval_id: str
    approver_id: str
    approved: bool
    comment: Optional[str] = None


class ApprovalHistoryItem(BaseModel):
    action: str
    actor_id: str
    at: datetime
    comment: Optional[str] = None
    detail: Dict[str, Any] = Field(default_factory=dict)
