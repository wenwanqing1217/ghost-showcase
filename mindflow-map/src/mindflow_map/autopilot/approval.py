"""Approval flow for human-in-the-loop.

Provides approval gates that pause autonomous execution and wait
for human approval, matching Feishu/WeChat Work approval flows.
"""

from __future__ import annotations

import dataclasses
import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Coroutine


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclasses.dataclass
class ApprovalRequest:
    id: str
    workflow_run_id: str
    step_id: str
    title: str
    description: str
    data: dict[str, Any]
    status: ApprovalStatus
    approver: str | None
    comment: str | None
    created_at: datetime
    responded_at: datetime | None
    expires_at: datetime | None


class ApprovalStore:
    """Persistent storage for approval requests."""

    def __init__(self, storage_path: str | os.PathLike[str] | None = None) -> None:
        self.storage_path = Path(storage_path) if storage_path is not None else Path("memory/approvals.json")
        self._requests: dict[str, ApprovalRequest] = {}
        self._load()

    def _load(self) -> None:
        if self.storage_path.exists():
            try:
                raw = json.loads(self.storage_path.read_text(encoding="utf-8"))
                for data in raw:
                    self._requests[data["id"]] = ApprovalRequest(
                        id=data["id"],
                        workflow_run_id=data["workflow_run_id"],
                        step_id=data["step_id"],
                        title=data["title"],
                        description=data["description"],
                        data=data.get("data", {}),
                        status=ApprovalStatus(data["status"]),
                        approver=data.get("approver"),
                        comment=data.get("comment"),
                        created_at=datetime.fromisoformat(data["created_at"]),
                        responded_at=datetime.fromisoformat(data["responded_at"]) if data.get("responded_at") else None,
                        expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
                    )
            except (json.JSONDecodeError, KeyError, OSError):
                self._requests = {}

    def _save(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        raw = []
        for req in self._requests.values():
            raw.append(
                {
                    "id": req.id,
                    "workflow_run_id": req.workflow_run_id,
                    "step_id": req.step_id,
                    "title": req.title,
                    "description": req.description,
                    "data": req.data,
                    "status": req.status.value,
                    "approver": req.approver,
                    "comment": req.comment,
                    "created_at": req.created_at.isoformat(),
                    "responded_at": req.responded_at.isoformat() if req.responded_at else None,
                    "expires_at": req.expires_at.isoformat() if req.expires_at else None,
                }
            )
        self.storage_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")

    def create(
        self,
        workflow_run_id: str,
        step_id: str,
        title: str,
        description: str,
        data: dict[str, Any],
        approver: str | None = None,
        ttl_seconds: int = 86400,
    ) -> ApprovalRequest:
        request = ApprovalRequest(
            id=str(uuid.uuid4()),
            workflow_run_id=workflow_run_id,
            step_id=step_id,
            title=title,
            description=description,
            data=data,
            status=ApprovalStatus.PENDING,
            approver=approver,
            comment=None,
            created_at=datetime.now(timezone.utc),
            responded_at=None,
            expires_at=datetime.now(timezone.utc) + __import__('datetime').timedelta(seconds=ttl_seconds),
        )
        self._requests[request.id] = request
        self._save()
        return request

    def get(self, request_id: str) -> ApprovalRequest | None:
        return self._requests.get(request_id)

    def list_pending(self) -> list[ApprovalRequest]:
        return [r for r in self._requests.values() if r.status == ApprovalStatus.PENDING]

    def approve(self, request_id: str, approver: str, comment: str | None = None) -> ApprovalRequest | None:
        request = self._requests.get(request_id)
        if not request or request.status != ApprovalStatus.PENDING:
            return None
        request.status = ApprovalStatus.APPROVED
        request.approver = approver
        request.comment = comment
        request.responded_at = datetime.now(timezone.utc)
        self._save()
        return request

    def reject(self, request_id: str, approver: str, comment: str | None = None) -> ApprovalRequest | None:
        request = self._requests.get(request_id)
        if not request or request.status != ApprovalStatus.PENDING:
            return None
        request.status = ApprovalStatus.REJECTED
        request.approver = approver
        request.comment = comment
        request.responded_at = datetime.now(timezone.utc)
        self._save()
        return request


class ApprovalFlow:
    """Manage approval flows for workflow steps."""

    def __init__(
        self,
        store: ApprovalStore,
        notifier: Callable[[ApprovalRequest], Coroutine[Any, Any, None]] | None = None,
    ) -> None:
        self.store = store
        self.notifier = notifier

    async def request_approval(
        self,
        workflow_run_id: str,
        step_id: str,
        title: str,
        description: str,
        data: dict[str, Any],
        approver: str | None = None,
        notify: bool = True,
    ) -> ApprovalRequest:
        """Create an approval request and optionally notify."""
        request = self.store.create(
            workflow_run_id=workflow_run_id,
            step_id=step_id,
            title=title,
            description=description,
            data=data,
            approver=approver,
        )
        if notify and self.notifier:
            await self.notifier(request)
        return request

    async def wait_for_approval(self, request_id: str, timeout: float = 86400.0) -> ApprovalRequest | None:
        """Wait for an approval decision."""
        import asyncio
        deadline = asyncio.get_event_loop().time() + timeout
        while True:
            request = self.store.get(request_id)
            if not request:
                return None
            if request.status != ApprovalStatus.PENDING:
                return request
            now = asyncio.get_event_loop().time()
            if now > deadline:
                request.status = ApprovalStatus.EXPIRED
                self.store._save()
                return request
            await asyncio.sleep(1.0)

    def check_approval(self, request_id: str) -> ApprovalRequest | None:
        """Non-blocking check of approval status."""
        return self.store.get(request_id)
