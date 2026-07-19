"""Notification service for autopilot.

Supports Feishu and WeChat notifications for workflow events,
approval requests, and status updates.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any


class Notifier(ABC):
    """Base notifier interface."""

    @abstractmethod
    async def send(self, title: str, content: str, **kwargs: Any) -> bool:
        """Send a notification.

        Args:
            title: Notification title.
            content: Notification content.
            **kwargs: Additional platform-specific parameters.

        Returns:
            True if notification was sent successfully.
        """
        ...


class FeishuNotifier(Notifier):
    """Feishu notification sender."""

    def __init__(self, app_id: str | None = None, app_secret: str | None = None) -> None:
        self.app_id = app_id
        self.app_secret = app_secret

    async def send(self, title: str, content: str, **kwargs: Any) -> bool:
        try:
            from lark_o_api import Client
            from lark_o_api.api.im.v1 import CreateMessageRequestBody, CreateMessageRequest

            receive_id = kwargs.get("receive_id", "")
            if not receive_id:
                return False

            body = CreateMessageRequestBody.builder() \
                .receive_id(receive_id) \
                .msg_type("text") \
                .content(json.dumps({"text": f"{title}\n\n{content}"}, ensure_ascii=False)) \
                .build()

            request = CreateMessageRequest.builder() \
                .receive_id(receive_id) \
                .request_body(body) \
                .build()

            client = Client.builder() \
                .app_id(self.app_id or "") \
                .app_secret(self.app_secret or "") \
                .build()

            response = client.im.v1.message.create(request)
            return response.success()
        except Exception:
            return False


class WeChatNotifier(Notifier):
    """WeChat notification sender."""

    def __init__(self, webhook_url: str | None = None) -> None:
        self.webhook_url = webhook_url

    async def send(self, title: str, content: str, **kwargs: Any) -> bool:
        try:
            import httpx

            webhook = self.webhook_url or kwargs.get("webhook_url", "")
            if not webhook:
                return False

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook,
                    json={
                        "msgtype": "text",
                        "text": {"content": f"{title}\n\n{content}"},
                    },
                    timeout=10.0,
                )
                return response.status_code == 200
        except Exception:
            return False


class CompositeNotifier(Notifier):
    """Send notifications through multiple channels."""

    def __init__(self, notifiers: list[Notifier]) -> None:
        self.notifiers = notifiers

    async def send(self, title: str, content: str, **kwargs: Any) -> bool:
        results = [await notifier.send(title, content, **kwargs) for notifier in self.notifiers]
        return any(results)


class NotificationService:
    """Central notification service for autopilot."""

    def __init__(self, default_notifier: Notifier | None = None) -> None:
        self.default_notifier = default_notifier
        self._notifiers: dict[str, Notifier] = {}

    def register_notifier(self, name: str, notifier: Notifier) -> None:
        """Register a named notifier."""
        self._notifiers[name] = notifier

    async def notify(self, title: str, content: str, channel: str = "default", **kwargs: Any) -> bool:
        """Send a notification.

        Args:
            title: Notification title.
            content: Notification content.
            channel: Notifier channel name.
            **kwargs: Additional parameters.

        Returns:
            True if sent successfully.
        """
        notifier = self._notifiers.get(channel, self.default_notifier)
        if not notifier:
            return False
        return await notifier.send(title, content, **kwargs)

    async def notify_approval(self, approval_request: Any) -> bool:
        """Notify approvers about a pending approval."""
        content = (
            f"Approval required for workflow step: {approval_request.step_id}\n"
            f"Description: {approval_request.description}\n"
            f"Data: {json.dumps(approval_request.data, ensure_ascii=False)}"
        )
        return await self.notify(
            title=f"Approval Required: {approval_request.title}",
            content=content,
            channel="approval",
        )

    async def notify_workflow_complete(self, workflow_run: Any) -> bool:
        """Notify about workflow completion."""
        status = workflow_run.status
        content = f"Workflow {workflow_run.workflow_id} finished with status: {status}"
        if workflow_run.error:
            content += f"\nError: {workflow_run.error}"
        return await self.notify(
            title=f"Workflow {status}: {workflow_run.workflow_id}",
            content=content,
            channel="workflow",
        )
