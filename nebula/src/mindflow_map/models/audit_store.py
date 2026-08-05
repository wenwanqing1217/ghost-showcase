"""SQLAlchemy-backed audit log store."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from mindflow_map.models.database import AuditLogModel
from mindflow_map.schemas.audit import AuditLog, AuditLogFilter

logger = logging.getLogger(__name__)


class SQLAuditStore:
    """Database-backed audit log store."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, log: AuditLog) -> AuditLog:
        """Append an audit log."""
        model = AuditLogModel(
            log_id=log.log_id or str(uuid.uuid4()),
            tenant_id=log.tenant_id,
            user_id=log.user_id,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            request_id=log.request_id,
            detail=log.detail,
            created_at=log.created_at or datetime.now(timezone.utc),
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_schema(model)

    async def query(self, filter: AuditLogFilter) -> list[AuditLog]:
        """Query audit logs with filters."""
        query = select(AuditLogModel).order_by(desc(AuditLogModel.created_at))

        if filter.tenant_id:
            query = query.where(AuditLogModel.tenant_id == filter.tenant_id)
        if filter.user_id:
            query = query.where(AuditLogModel.user_id == filter.user_id)
        if filter.action:
            query = query.where(AuditLogModel.action == filter.action)
        if filter.resource_type:
            query = query.where(AuditLogModel.resource_type == filter.resource_type)
        if filter.resource_id:
            query = query.where(AuditLogModel.resource_id == filter.resource_id)
        if filter.start_time:
            query = query.where(AuditLogModel.created_at >= filter.start_time)
        if filter.end_time:
            query = query.where(AuditLogModel.created_at <= filter.end_time)

        query = query.offset(filter.offset).limit(filter.limit)
        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._to_schema(model) for model in models]

    def _to_schema(self, model: AuditLogModel) -> AuditLog:
        """Convert database model to schema."""
        return AuditLog(
            log_id=model.log_id,
            tenant_id=model.tenant_id,
            user_id=model.user_id,
            action=model.action,
            resource_type=model.resource_type,
            resource_id=model.resource_id,
            ip_address=model.ip_address,
            user_agent=model.user_agent,
            request_id=model.request_id,
            detail=model.detail or {},
            created_at=model.created_at,
        )
