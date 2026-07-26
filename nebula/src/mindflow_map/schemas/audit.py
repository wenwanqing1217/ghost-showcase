"""Audit logging schemas and models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class AuditAction(str, Enum):
    # HTTP request-level
    ACCESS = "access"
    # Workflow
    WORKFLOW_CREATED = "workflow.created"
    WORKFLOW_UPDATED = "workflow.updated"
    WORKFLOW_DELETED = "workflow.deleted"
    WORKFLOW_EXECUTED = "workflow.executed"
    # Approval
    APPROVAL_CREATED = "approval.created"
    APPROVAL_DECIDED = "approval.decided"
    # Auth
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    TOKEN_ISSUED = "token.issued"
    TOKEN_REVOKED = "token.revoked"
    # Integration
    INTEGRATION_CONNECTED = "integration.connected"
    INTEGRATION_DISCONNECTED = "integration.disconnected"
    # System
    SYSTEM_CONFIG_CHANGED = "system.config_changed"


class AuditLog(BaseModel):
    log_id: str
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    action: AuditAction
    resource_type: str
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    detail: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AuditLogFilter(BaseModel):
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    action: Optional[AuditAction] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
