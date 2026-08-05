"""SQLAlchemy-backed auth provider."""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mindflow_map.models.database import Tenant as TenantModel
from mindflow_map.models.database import Token as TokenModel
from mindflow_map.models.database import User as UserModel
from mindflow_map.schemas.auth import PermissionType, RoleType, Tenant, TenantContext, TokenPayload, User

logger = logging.getLogger(__name__)


class SQLAuthProvider:
    """Database-backed auth provider."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._permissions: dict[str, List[PermissionType]] = {}

    # ------------------------------------------------------------------
    # Tenant management
    # ------------------------------------------------------------------

    async def create_tenant(self, tenant: Tenant) -> Tenant:
        """Create a new tenant."""
        model = TenantModel(
            tenant_id=tenant.tenant_id,
            name=tenant.name,
            status=tenant.status,
            settings=tenant.settings,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._tenant_to_schema(model)

    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID."""
        result = await self._session.execute(
            select(TenantModel).where(TenantModel.tenant_id == tenant_id)
        )
        model = result.scalar_one_or_none()
        return self._tenant_to_schema(model) if model else None

    async def list_tenants(self) -> List[Tenant]:
        """List all tenants."""
        result = await self._session.execute(select(TenantModel))
        models = result.scalars().all()
        return [self._tenant_to_schema(model) for model in models]

    # ------------------------------------------------------------------
    # User management
    # ------------------------------------------------------------------

    async def create_user(self, user: User) -> User:
        """Create a new user."""
        model = UserModel(
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            username=user.name,  # schema uses `name`, DB uses `username`
            email=user.email,
            role=user.role,
            is_active=user.is_active,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._user_to_schema(model)

    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await self._session.execute(
            select(UserModel).where(UserModel.user_id == user_id)
        )
        model = result.scalar_one_or_none()
        return self._user_to_schema(model) if model else None

    async def list_users_by_tenant(self, tenant_id: str) -> List[User]:
        """List users in a tenant."""
        result = await self._session.execute(
            select(UserModel).where(UserModel.tenant_id == tenant_id)
        )
        models = result.scalars().all()
        return [self._user_to_schema(model) for model in models]

    async def set_role(self, user_id: str, tenant_id: str, role: RoleType) -> None:
        """Set user role."""
        result = await self._session.execute(
            select(UserModel).where(UserModel.user_id == user_id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.role = role
            await self._session.flush()

    async def get_role(self, user_id: str, tenant_id: str) -> RoleType:
        """Get user role."""
        result = await self._session.execute(
            select(UserModel).where(UserModel.user_id == user_id)
        )
        model = result.scalar_one_or_none()
        return model.role if model else RoleType.MEMBER

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    async def issue_token(
        self,
        user_id: str,
        tenant_id: str,
        role: RoleType,
        ttl_seconds: int = 3600,
        scope: Optional[List[PermissionType]] = None,
    ) -> str:
        """Issue a new token."""
        token_value = secrets.token_urlsafe(32)
        model = TokenModel(
            token_value=token_value,
            user_id=user_id,
            tenant_id=tenant_id,
            role=role,
            scope=scope or [],
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds),
        )
        self._session.add(model)
        await self._session.flush()
        return token_value

    async def validate_token(self, token_value: str) -> Optional[TokenPayload]:
        """Validate a token."""
        result = await self._session.execute(
            select(TokenModel).where(TokenModel.token_value == token_value)
        )
        model = result.scalar_one_or_none()
        if not model or model.is_revoked:
            return None
        # SQLite returns naive datetimes; normalize to UTC-aware for safe comparison
        expires_at = model.expires_at
        if expires_at is not None and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at and expires_at < datetime.now(timezone.utc):
            await self._session.delete(model)
            await self._session.flush()
            return None
        return TokenPayload(
            user_id=model.user_id,
            tenant_id=model.tenant_id,
            role=model.role,
            exp=expires_at,
            scope=model.scope or [],
        )

    async def revoke_token(self, token_value: str) -> None:
        """Revoke a token."""
        result = await self._session.execute(
            select(TokenModel).where(TokenModel.token_value == token_value)
        )
        model = result.scalar_one_or_none()
        if model:
            model.is_revoked = True
            await self._session.flush()

    # ------------------------------------------------------------------
    # Permissions
    # ------------------------------------------------------------------

    def get_permissions(self, role: RoleType) -> List[PermissionType]:
        """Get permissions for a role."""
        return self._permissions.get(role, [])

    def set_permissions(self, role: RoleType, permissions: List[PermissionType]) -> None:
        """Set permissions for a role."""
        self._permissions[role] = permissions

    def has_permission(self, user_id: str, tenant_id: str, permission: PermissionType) -> bool:
        """Check if user has permission (in-memory lookup for performance)."""
        role = self.get_role(user_id, tenant_id)
        return permission in self.get_permissions(role)

    async def get_tenant_context(self, user_id: str, tenant_id: str) -> TenantContext:
        """Get tenant context for a user."""
        role = await self.get_role(user_id, tenant_id)
        permissions = self.get_permissions(role)
        return TenantContext(
            tenant_id=tenant_id,
            user_id=user_id,
            role=role,
            permissions=permissions,
        )

    # ------------------------------------------------------------------
    # Converters
    # ------------------------------------------------------------------

    def _tenant_to_schema(self, model: TenantModel) -> Tenant:
        """Convert tenant model to schema."""
        return Tenant(
            tenant_id=model.tenant_id,
            name=model.name,
            status=model.status,
            settings=model.settings or {},
        )

    def _user_to_schema(self, model: UserModel) -> User:
        """Convert user model to schema."""
        return User(
            user_id=model.user_id,
            tenant_id=model.tenant_id,
            name=model.username,  # DB column is `username`, schema field is `name`
            email=model.email,
            role=model.role,
            is_active=model.is_active,
        )
