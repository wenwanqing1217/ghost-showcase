"""Audit logging tests."""

from __future__ import annotations

import uuid

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from mindflow_map.middleware.audit import AuditMiddleware
from mindflow_map.models.audit_store import SQLAuditStore
from mindflow_map.models.database import Base
from mindflow_map.models.session import Database
from mindflow_map.schemas.audit import AuditAction, AuditLog, AuditLogFilter

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_db() -> Database:
    return Database("sqlite+aiosqlite:///:memory:")


async def _init_db(db: Database) -> None:
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ---------------------------------------------------------------------------
# SQLAuditStore tests
# ---------------------------------------------------------------------------


class TestSQLAuditStore:
    def test_append_and_query_all(self):
        import asyncio

        async def run():
            db = _make_db()
            await _init_db(db)
            async with db.get_session() as session:
                store = SQLAuditStore(session)
                log = AuditLog(
                    log_id=str(uuid.uuid4()),
                    action=AuditAction.WORKFLOW_CREATED,
                    resource_type="workflow",
                    resource_id="wf-1",
                )
                await store.append(log)
                results = await store.query(AuditLogFilter())
                assert len(results) == 1
                assert results[0].resource_id == "wf-1"
            await db.close()

        asyncio.run(run())

    def test_query_filter_by_action(self):
        import asyncio

        async def run():
            db = _make_db()
            await _init_db(db)
            async with db.get_session() as session:
                store = SQLAuditStore(session)
                await store.append(AuditLog(log_id=str(uuid.uuid4()), action=AuditAction.WORKFLOW_CREATED, resource_type="workflow"))
                await store.append(AuditLog(log_id=str(uuid.uuid4()), action=AuditAction.USER_LOGIN, resource_type="auth"))
                results = await store.query(AuditLogFilter(action=AuditAction.USER_LOGIN))
                assert len(results) == 1
                assert results[0].action == AuditAction.USER_LOGIN
            await db.close()

        asyncio.run(run())

    def test_query_filter_by_tenant(self):
        import asyncio

        async def run():
            db = _make_db()
            await _init_db(db)
            async with db.get_session() as session:
                store = SQLAuditStore(session)
                await store.append(AuditLog(log_id=str(uuid.uuid4()), action=AuditAction.WORKFLOW_CREATED, resource_type="workflow", tenant_id="t1"))
                await store.append(AuditLog(log_id=str(uuid.uuid4()), action=AuditAction.WORKFLOW_CREATED, resource_type="workflow", tenant_id="t2"))
                results = await store.query(AuditLogFilter(tenant_id="t1"))
                assert len(results) == 1
                assert results[0].tenant_id == "t1"
            await db.close()

        asyncio.run(run())

    def test_query_pagination(self):
        import asyncio

        async def run():
            db = _make_db()
            await _init_db(db)
            async with db.get_session() as session:
                store = SQLAuditStore(session)
                for i in range(5):
                    await store.append(AuditLog(log_id=str(uuid.uuid4()), action=AuditAction.WORKFLOW_CREATED, resource_type="workflow"))
                results = await store.query(AuditLogFilter(limit=2, offset=2))
                assert len(results) == 2
            await db.close()

        asyncio.run(run())


# ---------------------------------------------------------------------------
# Middleware / integration tests
# ---------------------------------------------------------------------------


class TestAuditMiddleware:
    def test_middleware_attaches_audit_logger(self):
        db = _make_db()

        import asyncio
        asyncio.run(_init_db(db))

        app = FastAPI()
        app.add_middleware(AuditMiddleware, db=db)

        @app.get("/test")
        def test_endpoint(request: Request):
            logger = request.state.audit_logger
            import asyncio as aio
            aio.run(logger.log(AuditAction.WORKFLOW_CREATED, "workflow", "wf-1"))
            return {"ok": True}

        client = TestClient(app)
        resp = client.get("/test")
        assert resp.status_code == 200
