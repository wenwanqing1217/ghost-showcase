"""Tests for advanced autopilot components."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from mindflow_map.autopilot.approval import ApprovalFlow, ApprovalStore, ApprovalStatus
from mindflow_map.autopilot.collaboration import AgentDescriptor, AgentMessage, CollaborationEngine, MessageBus
from mindflow_map.autopilot.memory import LearningEngine, MemoryStore, MemoryEntry
from mindflow_map.autopilot.scheduler import CronExpression, ScheduledJob, WorkflowScheduler
from mindflow_map.autopilot.workflows import WorkflowDefinitionLoader, YamlWorkflowEngine, WorkflowStep, WorkflowDefinition


class TestMessageBus:
    def test_publish_and_history(self) -> None:
        bus = MessageBus()
        message = AgentMessage(sender="a", recipient="b", topic="t", content="hello")

        async def test() -> None:
            await bus.publish(message)
            assert message in bus.history

        import asyncio
        asyncio.run(test())

    def test_subscribe_receives_message(self) -> None:
        bus = MessageBus()
        received = []

        async def handler(msg: AgentMessage) -> None:
            received.append(msg)

        async def test() -> None:
            await bus.subscribe("b", handler)
            message = AgentMessage(sender="a", recipient="b", topic="t", content="hello")
            await bus.publish(message)
            assert len(received) == 1
            assert received[0].content == "hello"

        import asyncio
        asyncio.run(test())


class TestCollaborationEngine:
    def test_register_agent(self) -> None:
        engine = CollaborationEngine()
        agent = AgentDescriptor(id="a1", name="Test", role="tester", system_prompt="test")
        engine.register_agent(agent)
        assert "a1" in engine.agents

    def test_run_conversation_returns_messages(self) -> None:
        engine = CollaborationEngine()
        a1 = AgentDescriptor(id="a1", name="A", role="architect", system_prompt="")
        a2 = AgentDescriptor(id="a2", name="B", role="reviewer", system_prompt="")
        engine.register_agent(a1)
        engine.register_agent(a2)

        async def handler(msg: AgentMessage) -> None:
            pass

        async def test() -> None:
            await engine.bus.subscribe("a1", handler)
            await engine.bus.subscribe("a2", handler)
            msg = AgentMessage(sender="a1", recipient="*", topic="review", content="check this")
            conversation = await engine.run_conversation(["a1", "a2"], msg, max_rounds=2)
            assert len(conversation) >= 1
            assert conversation[0].id == msg.id

        import asyncio
        asyncio.run(test())


class TestMemoryStore:
    def test_store_and_query(self, tmp_path: Path) -> None:
        store = MemoryStore(tmp_path / "memory.json")
        entry = MemoryEntry(
            id="1", task="refactor engine", context={}, result={},
            success=True, timestamp=datetime.now(timezone.utc)
        )
        store.store(entry)
        results = store.query("refactor engine")
        assert len(results) == 1
        assert results[0].id == "1"

    def test_success_rate(self, tmp_path: Path) -> None:
        store = MemoryStore(tmp_path / "memory.json")
        for i, success in enumerate([True, True, False]):
            store.store(MemoryEntry(
                id=str(i), task="task", context={}, result={},
                success=success, timestamp=datetime.now(timezone.utc)
            ))
        assert abs(store.get_success_rate() - 2/3) < 0.01


class TestLearningEngine:
    def test_suggest_improvements(self, tmp_path: Path) -> None:
        store = MemoryStore(tmp_path / "memory.json")
        store.store(MemoryEntry(
            id="1", task="fix bug", context={}, result={"error": "null pointer"},
            success=False, timestamp=datetime.now(timezone.utc)
        ))
        engine = LearningEngine(store)
        suggestions = engine.suggest_improvements("fix bug")
        assert len(suggestions) > 0


class TestApprovalFlow:
    def test_create_and_approve(self, tmp_path: Path) -> None:
        store = ApprovalStore(tmp_path / "approvals.json")
        flow = ApprovalFlow(store)
        req = store.create("run1", "step1", "Deploy", "Deploy to prod", {})
        assert req.status == ApprovalStatus.PENDING
        store.approve(req.id, "admin", "Looks good")
        assert store.get(req.id).status == ApprovalStatus.APPROVED

    def test_reject(self, tmp_path: Path) -> None:
        store = ApprovalStore(tmp_path / "approvals.json")
        flow = ApprovalFlow(store)
        req = store.create("run1", "step1", "Deploy", "Deploy", {})
        store.reject(req.id, "admin", "Not ready")
        assert store.get(req.id).status == ApprovalStatus.REJECTED


class TestYamlWorkflowEngine:
    def test_load_workflow(self, tmp_path: Path) -> None:
        loader = WorkflowDefinitionLoader(tmp_path)
        definition = WorkflowStep(id="s1", type="task", name="Lint", prompt="run lint")
        wf = WorkflowDefinition(
            id="wf1", name="Test", description="", version="1.0.0",
            steps=[definition], triggers=[]
        )
        loader.save(wf)
        loaded = loader.load("wf1")
        assert loaded is not None
        assert loaded.name == "Test"
        assert len(loaded.steps) == 1

    def test_start_workflow(self, tmp_path: Path) -> None:
        loader = WorkflowDefinitionLoader(tmp_path)
        definition = WorkflowStep(id="s1", type="task", name="Lint", prompt="run lint")
        wf = WorkflowDefinition(
            id="wf1", name="Test", description="", version="1.0.0",
            steps=[definition], triggers=[]
        )
        loader.save(wf)
        engine = YamlWorkflowEngine(workflows_dir=tmp_path)
        run = engine.start("wf1", {"key": "value"})
        assert run is not None
        assert run.status == "running"
        assert run.state["key"] == "value"


class TestCronExpression:
    def test_matches_exact_minute(self) -> None:
        import datetime
        cron = CronExpression("5 * * * *")
        assert cron.matches(datetime.datetime(2024, 1, 1, 12, 5)) is True
        assert cron.matches(datetime.datetime(2024, 1, 1, 12, 6)) is False

    def test_matches_every_minute(self) -> None:
        import datetime
        cron = CronExpression("* * * * *")
        assert cron.matches(datetime.datetime(2024, 1, 1, 12, 5)) is True
        assert cron.matches(datetime.datetime(2024, 1, 1, 12, 6)) is True

    def test_rejects_invalid_expression(self) -> None:
        with pytest.raises(ValueError):
            CronExpression("* * *")


class TestWorkflowScheduler:
    def test_schedule_persists_job(self, tmp_path: Path) -> None:
        engine = YamlWorkflowEngine(workflows_dir=tmp_path)
        scheduler = WorkflowScheduler(workflow_engine=engine, storage_path=tmp_path / "jobs.json")
        scheduler.stop = lambda: None
        job = scheduler.schedule("wf1", "*/5 * * * *")
        assert job.workflow_id == "wf1"
        assert scheduler.list_jobs() == [job]

    def test_list_jobs_filters_by_workflow(self, tmp_path: Path) -> None:
        engine = YamlWorkflowEngine(workflows_dir=tmp_path)
        scheduler = WorkflowScheduler(workflow_engine=engine, storage_path=tmp_path / "jobs.json")
        scheduler.stop = lambda: None
        scheduler.schedule("wf1", "*/5 * * * *")
        scheduler.schedule("wf2", "*/10 * * * *")
        assert len(scheduler.list_jobs()) == 2
        assert len(scheduler.list_jobs(workflow_id="wf1")) == 1

    def test_cancel_removes_job(self, tmp_path: Path) -> None:
        engine = YamlWorkflowEngine(workflows_dir=tmp_path)
        scheduler = WorkflowScheduler(workflow_engine=engine, storage_path=tmp_path / "jobs.json")
        scheduler.stop = lambda: None
        job = scheduler.schedule("wf1", "*/5 * * * *")
        assert scheduler.cancel(job.id) is True
        assert scheduler.list_jobs() == []
