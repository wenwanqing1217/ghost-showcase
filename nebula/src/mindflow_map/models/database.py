"""Database models for approvals, audit logs, and auth."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Boolean, DateTime, JSON, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from mindflow_map.memory.store import Base
from mindflow_map.schemas.approval import ApprovalStatus, ApprovalLevel as ApprovalLevelSchema
from mindflow_map.schemas.auth import RoleType, PermissionType, TenantStatus
from mindflow_map.schemas.audit import AuditAction


# ---------------------------------------------------------------------------
# Multi-tenancy / Auth models
# ---------------------------------------------------------------------------


class Tenant(Base):
    """租户模型"""
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    status: Mapped[TenantStatus] = mapped_column(SQLEnum(TenantStatus), default=TenantStatus.ACTIVE)
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    users: Mapped[list["User"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")


class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("tenants.tenant_id"), index=True)
    username: Mapped[str] = mapped_column(String(255))
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[RoleType] = mapped_column(SQLEnum(RoleType), default=RoleType.MEMBER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    tenant: Mapped["Tenant"] = relationship(back_populates="users")
    tokens: Mapped[list["Token"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Token(Base):
    """Token 模型"""
    __tablename__ = "tokens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    token_value: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.user_id"), index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    role: Mapped[RoleType] = mapped_column(SQLEnum(RoleType))
    scope: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    user: Mapped["User"] = relationship(back_populates="tokens")


# ---------------------------------------------------------------------------
# Approval models
# ---------------------------------------------------------------------------


class ApprovalModel(Base):
    """审批模型"""
    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    approval_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    workflow_id: Mapped[str] = mapped_column(String(64), index=True)
    requester_id: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    levels: Mapped[list] = mapped_column(JSON)  # List of ApprovalLevel dicts
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[ApprovalStatus] = mapped_column(SQLEnum(ApprovalStatus), default=ApprovalStatus.PENDING)
    current_level: Mapped[int] = mapped_column(default=1)
    decided_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    history: Mapped[list["ApprovalHistoryModel"]] = relationship(back_populates="approval", cascade="all, delete-orphan")


class ApprovalHistoryModel(Base):
    """审批历史模型"""
    __tablename__ = "approval_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    approval_id: Mapped[str] = mapped_column(String(64), ForeignKey("approvals.approval_id"), index=True)
    action: Mapped[str] = mapped_column(String(32))  # created|approved|rejected
    actor_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    detail: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    approval: Mapped["ApprovalModel"] = relationship(back_populates="history")


# ---------------------------------------------------------------------------
# Audit log models
# ---------------------------------------------------------------------------


class AuditLogModel(Base):
    """审计日志模型"""
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    log_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    action: Mapped[AuditAction] = mapped_column(SQLEnum(AuditAction, name="audit_action"), index=True)
    resource_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    detail: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
