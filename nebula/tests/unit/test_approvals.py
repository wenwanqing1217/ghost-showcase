"""Multi-level approval form system tests."""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from mindflow_map.main import app
from mindflow_map.schemas.approval import (
    ApprovalDefinition,
    ApprovalLevel,
    ApprovalStatus,
)

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def _close_module_client():
    """模块测试结束后关闭 TestClient，避免泄漏 portal 线程/事件循环。"""
    yield
    client.close()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_approval(
    approval_id: str | None = None,
    workflow_id: str = "wf-1",
    requester_id: str = "user-1",
    title: str = "Test Approval",
    description: str = "Test description",
    levels: list[dict] | None = None,
    status: ApprovalStatus = ApprovalStatus.PENDING,
    current_level: int = 1,
) -> ApprovalDefinition:
    return ApprovalDefinition(
        approval_id=approval_id or str(uuid.uuid4()),
        workflow_id=workflow_id,
        requester_id=requester_id,
        title=title,
        description=description,
        levels=levels or [ApprovalLevel(level=1, approver_ids=["approver-1"])],
        status=status,
        current_level=current_level,
        created_at=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
# Create approval
# ---------------------------------------------------------------------------


class TestCreateApproval:
    def test_create_single_level_approval(self):
        payload = {
            "workflow_id": "wf-1",
            "requester_id": "user-1",
            "title": "Leave Request",
            "description": "Annual leave",
            "levels": [{"level": 1, "approver_ids": ["mgr-1"]}],
        }
        resp = client.post("/api/v1/approvals", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert body["workflow_id"] == "wf-1"
        assert body["status"] == "pending"
        assert body["current_level"] == 1
        assert len(body["levels"]) == 1

    def test_create_multi_level_approval(self):
        payload = {
            "workflow_id": "wf-2",
            "requester_id": "user-2",
            "title": "Budget Approval",
            "description": "Q4 budget",
            "levels": [
                {"level": 1, "approver_ids": ["mgr-1"]},
                {"level": 2, "approver_ids": ["dir-1"]},
            ],
        }
        resp = client.post("/api/v1/approvals", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert len(body["levels"]) == 2
        assert body["levels"][0]["level"] == 1
        assert body["levels"][1]["level"] == 2

    def test_create_requires_title(self):
        payload = {
            "workflow_id": "wf-1",
            "requester_id": "user-1",
            "description": "No title",
            "levels": [{"level": 1, "approver_ids": ["mgr-1"]}],
        }
        resp = client.post("/api/v1/approvals", json=payload)
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# List approvals
# ---------------------------------------------------------------------------


class TestListApprovals:
    def test_list_returns_created_approvals(self):
        # Create first
        client.post("/api/v1/approvals", json={
            "workflow_id": "wf-list-1",
            "requester_id": "user-list",
            "title": "List Test",
            "description": "",
            "levels": [{"level": 1, "approver_ids": ["a1"]}],
        })
        resp = client.get("/api/v1/approvals")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert any(a["workflow_id"] == "wf-list-1" for a in body)

    def test_list_filter_by_status(self):
        resp = client.get("/api/v1/approvals", params={"status": "pending"})
        assert resp.status_code == 200
        body = resp.json()
        assert all(a["status"] == "pending" for a in body)


# ---------------------------------------------------------------------------
# Get approval detail
# ---------------------------------------------------------------------------


class TestGetApproval:
    def test_get_existing_approval(self):
        create_resp = client.post("/api/v1/approvals", json={
            "workflow_id": "wf-get-1",
            "requester_id": "user-get",
            "title": "Get Test",
            "description": "",
            "levels": [{"level": 1, "approver_ids": ["a1"]}],
        })
        approval_id = create_resp.json()["approval_id"]
        resp = client.get(f"/api/v1/approvals/{approval_id}")
        assert resp.status_code == 200
        assert resp.json()["approval_id"] == approval_id

    def test_get_missing_returns_404(self):
        resp = client.get("/api/v1/approvals/nonexistent")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Decision / approval flow
# ---------------------------------------------------------------------------


class TestApprovalDecision:
    def test_approve_last_level_marks_approved(self):
        create_resp = client.post("/api/v1/approvals", json={
            "workflow_id": "wf-dec-1",
            "requester_id": "user-dec",
            "title": "Decision Test",
            "description": "",
            "levels": [{"level": 1, "approver_ids": ["a1"]}],
        })
        approval_id = create_resp.json()["approval_id"]

        resp = client.post(
            f"/api/v1/approvals/{approval_id}/decide",
            json={"approval_id": approval_id, "approver_id": "a1", "approved": True},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "approved"
        assert body["decided_by"] == "a1"

    def test_reject_marks_rejected(self):
        create_resp = client.post("/api/v1/approvals", json={
            "workflow_id": "wf-dec-2",
            "requester_id": "user-dec",
            "title": "Reject Test",
            "description": "",
            "levels": [{"level": 1, "approver_ids": ["a1"]}],
        })
        approval_id = create_resp.json()["approval_id"]

        resp = client.post(
            f"/api/v1/approvals/{approval_id}/decide",
            json={"approval_id": approval_id, "approver_id": "a1", "approved": False, "comment": "Not needed"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "rejected"
        assert body["comment"] == "Not needed"

    def test_approve_multi_level_advances(self):
        create_resp = client.post("/api/v1/approvals", json={
            "workflow_id": "wf-dec-3",
            "requester_id": "user-dec",
            "title": "Multi Level",
            "description": "",
            "levels": [
                {"level": 1, "approver_ids": ["a1"]},
                {"level": 2, "approver_ids": ["a2"]},
            ],
        })
        approval_id = create_resp.json()["approval_id"]

        # Level 1 approve
        resp1 = client.post(
            f"/api/v1/approvals/{approval_id}/decide",
            json={"approval_id": approval_id, "approver_id": "a1", "approved": True},
        )
        assert resp1.status_code == 200
        assert resp1.json()["current_level"] == 2
        assert resp1.json()["status"] == "pending"

        # Level 2 approve
        resp2 = client.post(
            f"/api/v1/approvals/{approval_id}/decide",
            json={"approval_id": approval_id, "approver_id": "a2", "approved": True},
        )
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "approved"

    def test_decide_on_non_pending_returns_400(self):
        create_resp = client.post("/api/v1/approvals", json={
            "workflow_id": "wf-dec-4",
            "requester_id": "user-dec",
            "title": "Finalized",
            "description": "",
            "levels": [{"level": 1, "approver_ids": ["a1"]}],
        })
        approval_id = create_resp.json()["approval_id"]

        # First approve
        client.post(
            f"/api/v1/approvals/{approval_id}/decide",
            json={"approval_id": approval_id, "approver_id": "a1", "approved": True},
        )
        # Second decide should fail
        resp = client.post(
            f"/api/v1/approvals/{approval_id}/decide",
            json={"approval_id": approval_id, "approver_id": "a1", "approved": False},
        )
        assert resp.status_code == 400
