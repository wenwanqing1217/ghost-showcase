"""Autopilot system leveraging zcode-brain agent architecture.

This package provides autonomous task execution with:
- Role matching from zcode-brain roles
- Safety guardrails from zcode-brain safety
- Task decomposition and expert assignment
- LLM-backed code generation
- Self-loop code improvement
- Multi-agent collaboration
- YAML workflow definitions
- Approval flows with human-in-the-loop
- Persistent memory and learning
- Notifications via Feishu/WeChat
- Workflow scheduling with cron triggers
- Git automation
"""

from .roles import load_roles, match_role
from .safety import load_guardrails, check_safety
from .prompt import assemble_prompt
from .runner import TaskRunner
from .orchestrator import TaskOrchestrator
from .executor import CodeExecutor
from .git_workflow import GitWorkflow
from .self_loop import SelfLoop, CodebaseScanner, IssuePrioritizer
from .collaboration import CollaborationEngine, MessageBus, AgentDescriptor, AgentMessage
from .memory import MemoryStore, LearningEngine
from .workflows import WorkflowEngine, WorkflowDefinitionLoader, WorkflowDefinition
from .approval import ApprovalFlow, ApprovalStore
from .notifications import NotificationService, FeishuNotifier, WeChatNotifier
from .scheduler import WorkflowScheduler, CronExpression, ScheduledJob

__all__ = [
    "load_roles",
    "match_role",
    "load_guardrails",
    "check_safety",
    "assemble_prompt",
    "TaskRunner",
    "TaskOrchestrator",
    "CodeExecutor",
    "GitWorkflow",
    "SelfLoop",
    "CodebaseScanner",
    "IssuePrioritizer",
    "CollaborationEngine",
    "MessageBus",
    "AgentDescriptor",
    "AgentMessage",
    "MemoryStore",
    "LearningEngine",
    "WorkflowEngine",
    "WorkflowDefinitionLoader",
    "WorkflowDefinition",
    "ApprovalFlow",
    "ApprovalStore",
    "NotificationService",
    "FeishuNotifier",
    "WeChatNotifier",
    "WorkflowScheduler",
    "CronExpression",
    "ScheduledJob",
]
