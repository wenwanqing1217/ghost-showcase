"""Message bus for multi-agent collaboration.

Provides a pub/sub message passing system that allows multiple agents
to collaborate on complex tasks, inspired by AutoGen's message-passing
architecture and CrewAI's agent collaboration patterns.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine


@dataclass
class AgentMessage:
    """Message passed between agents."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""
    recipient: str = ""
    topic: str = ""
    content: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reply_to: str | None = None


@dataclass
class AgentDescriptor:
    """Description of an agent in the system."""

    id: str
    name: str
    role: str
    system_prompt: str
    tools: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class MessageBus:
    """Asynchronous message bus for agent communication."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[AgentMessage], Coroutine[Any, Any, None]]]] = {}
        self._history: list[AgentMessage] = []
        self._lock = asyncio.Lock()

    async def subscribe(self, agent_id: str, handler: Callable[[AgentMessage], Coroutine[Any, Any, None]]) -> None:
        """Subscribe an agent to messages."""
        async with self._lock:
            self._subscribers.setdefault(agent_id, []).append(handler)

    async def publish(self, message: AgentMessage) -> None:
        """Publish a message to all subscribers."""
        async with self._lock:
            self._history.append(message)
        handlers = []
        for agent_id, agent_handlers in self._subscribers.items():
            if message.recipient == "*" or message.recipient == agent_id or agent_id == message.sender:
                handlers.extend(agent_handlers)
        if handlers:
            await asyncio.gather(*(handler(message) for handler in handlers), return_exceptions=True)

    async def request(
        self,
        sender: str,
        recipient: str,
        content: Any,
        topic: str = "",
        metadata: dict[str, Any] | None = None,
        timeout: float = 60.0,
    ) -> AgentMessage | None:
        """Send a request and wait for a response."""
        request = AgentMessage(
            sender=sender,
            recipient=recipient,
            topic=topic or "request",
            content=content,
            metadata=metadata or {},
        )
        await self.publish(request)
        # Simple response waiting
        deadline = asyncio.get_event_loop().time() + timeout
        while True:
            now = asyncio.get_event_loop().time()
            if now > deadline:
                return None
            await asyncio.sleep(0.1)
            async with self._lock:
                for msg in reversed(self._history):
                    if msg.reply_to == request.id:
                        return msg

    @property
    def history(self) -> list[AgentMessage]:
        return list(self._history)


class CollaborationEngine:
    """Engine for multi-agent task collaboration."""

    def __init__(self) -> None:
        self.bus = MessageBus()
        self.agents: dict[str, AgentDescriptor] = {}

    def register_agent(self, agent: AgentDescriptor) -> None:
        """Register an agent with the collaboration engine."""
        self.agents[agent.id] = agent

    async def run_conversation(
        self,
        participants: list[str],
        initial_message: AgentMessage,
        max_rounds: int = 10,
    ) -> list[AgentMessage]:
        """Run a multi-agent conversation.

        Args:
            participants: List of agent IDs to include.
            initial_message: Starting message.
            max_rounds: Maximum conversation rounds.

        Returns:
            List of messages exchanged.
        """
        conversation: list[AgentMessage] = [initial_message]
        current_message = initial_message

        for _ in range(max_rounds):
            next_sender = None
            for participant in participants:
                if participant != current_message.sender:
                    next_sender = participant
                    break

            if next_sender is None:
                break

            response = await self.bus.request(
                sender=current_message.sender,
                recipient=next_sender,
                content=current_message.content,
                topic=current_message.topic,
                metadata={"reply_context": current_message.id},
                timeout=5.0,
            )

            if response is None:
                break

            response.reply_to = current_message.id
            conversation.append(response)
            current_message = response

        return conversation
