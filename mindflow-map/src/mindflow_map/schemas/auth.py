"""RBAC and multi-tenancy schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class TenantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class RoleType(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class PermissionType(str, Enum):
    WORKFLOW_READ = "workflow:read"
    WORKFLOW_WRITE = "workflow:write"
    WORKFLOW_EXECUTE = "workflow:execute"
    APPROVAL_READ = "approval:read"
    APPROVAL_DECIDE = "approval:decide"
    ADMIN_MANAGE = "admin:manage"
    INTEGRATION_READ = "integration:read"
    INTEGRATION_WRITE = "integration:write"


class Tenant(BaseModel):
    tenant_id: str
    name: str
    status: TenantStatus = TenantStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    settings: dict = Field(default_factory=dict)


class User(BaseModel):
    user_id: str
    tenant_id: str
    email: str
    name: str
    role: RoleType = RoleType.MEMBER
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None


class Role(BaseModel):
    role_id: str
    tenant_id: str
    name: str
    permissions: List[PermissionType] = Field(default_factory=list)
    description: str = ""


class TokenPayload(BaseModel):
    user_id: str
    tenant_id: str
    role: RoleType
    exp: Optional[datetime] = None
    scope: List[PermissionType] = Field(default_factory=list)


class CurrentUser(BaseModel):
    user: User
    token: Optional[TokenPayload] = None


class TenantContext(BaseModel):
    tenant_id: str
    user_id: str
    role: RoleType
    permissions: List[PermissionType] = Field(default_factory=list)
