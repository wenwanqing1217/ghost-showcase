"""SQLAlchemy-backed approval store."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from mindflow_map.models.database import ApprovalHistoryModel, ApprovalModel
from mindflow_map.schemas.approval import (
    ApprovalDecisionRequest,
    ApprovalDefinition,
    ApprovalHistoryItem,
    ApprovalLevel,
    ApprovalStatus,
)

logger = logging.getLogger(__name__)


class SQLApprovalStore:
    """Database-backed approval store."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, approval: ApprovalDefinition) -> ApprovalDefinition:
        """Create a new approval."""
        model = ApprovalModel(
            approval_id=approval.approval_id,
            workflow_id=approval.workflow_id,
            requester_id=approval.requester_id,
            title=approval.title,
            description=approval.description,
            levels=[level.model_dump() for level in approval.levels],
            payload=approval.payload,
            status=approval.status,
            current_level=approval.current_level,
            created_at=approval.created_at or datetime.now(timezone.utc),
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)

        # Add history
        history = ApprovalHistoryModel(
            approval_id=model.approval_id,
            action="created",
            actor_id=approval.requester_id,
            at=model.created_at,
            detail={"workflow_id": approval.workflow_id},
        )
        self._session.add(history)
        await self._session.flush()

        return self._to_schema(model)

    async def get(self, approval_id: str) -> Optional[ApprovalDefinition]:
        """Get approval by ID."""
        result = await self._session.execute(
            select(ApprovalModel).where(ApprovalModel.approval_id == approval_id)
        )
        model = result.scalar_one_or_none()
        return self._to_schema(model) if model else None

    async def list_by_status(self, status: Optional[ApprovalStatus] = None) -> list[ApprovalDefinition]:
        """List approvals, optionally filtered by status."""
        query = select(ApprovalModel).order_by(desc(ApprovalModel.created_at))
        if status is not None:
            query = query.where(ApprovalModel.status == status)
        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._to_schema(model) for model in models]

    async def add_history(self, approval_id: str, item: ApprovalHistoryItem) -> None:
        """Add history item to approval."""
        history = ApprovalHistoryModel(
            approval_id=approval_id,
            action=item.action,
            actor_id=item.actor_id,
            at=item.at,
            comment=item.comment,
            detail=item.detail,
        )
        self._session.add(history)
        await self._session.flush()

    async def get_history(self, approval_id: str) -> list[ApprovalHistoryItem]:
        """Get approval history."""
        result = await self._session.execute(
            select(ApprovalHistoryModel)
            .where(ApprovalHistoryModel.approval_id == approval_id)
            .order_by(ApprovalHistoryModel.at)
        )
        models = result.scalars().all()
        return [
            ApprovalHistoryItem(
                action=model.action,
                actor_id=model.actor_id,
                at=model.at,
                comment=model.comment,
                detail=model.detail or {},
            )
            for model in models
        ]

    async def decide(self, approval_id: str, request: ApprovalDecisionRequest) -> Optional[ApprovalDefinition]:
        """Make a decision on an approval."""
        result = await self._session.execute(
            select(ApprovalModel).where(ApprovalModel.approval_id == approval_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None

        if model.status != ApprovalStatus.PENDING:
            return None

        # Find current level
        levels = [ApprovalLevel(**level) for level in model.levels]
        current_level = model.current_level
        level_def = next((lvl for lvl in levels if lvl.level == current_level), None)
        if not level_def:
            return None

        if request.approver_id not in level_def.approver_ids:
            return None

        now = datetime.now(timezone.utc)
        if request.approved:
            if current_level >= len(levels):
                model.status = ApprovalStatus.APPROVED
                model.current_level = current_level
            else:
                model.current_level = current_level + 1
            action = "approved"
        else:
            model.status = ApprovalStatus.REJECTED
            model.current_level = current_level
            action = "rejected"

        model.decided_by = request.approver_id
        model.decided_at = now
        model.comment = request.comment

        # Add history
        history = ApprovalHistoryModel(
            approval_id=approval_id,
            action=action,
            actor_id=request.approver_id,
            at=now,
            comment=request.comment,
            detail={"level": current_level},
        )
        self._session.add(history)
        await self._session.flush()
        await self._session.refresh(model)

        return self._to_schema(model)

    def _to_schema(self, model: ApprovalModel) -> ApprovalDefinition:
        """Convert database model to schema."""
        return ApprovalDefinition(
            approval_id=model.approval_id,
            workflow_id=model.workflow_id,
            requester_id=model.requester_id,
            title=model.title,
            description=model.description or "",
            levels=[ApprovalLevel(**level) for level in model.levels],
            status=model.status,
            current_level=model.current_level,
            decided_by=model.decided_by,
            decided_at=model.decided_at,
            comment=model.comment,
            payload=model.payload or {},
            created_at=model.created_at,
        )
