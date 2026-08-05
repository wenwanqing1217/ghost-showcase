#!/usr/bin/env python3
"""
Feishu Interactive Bus — Unified Feishu Service
=================================================
Four-in-one Feishu integration:

  1. 💬 Chat  — Receive/send messages, AI-powered responses
  2. ⚡ Execute — Code runner (AtomCode/Codex/ZCode backends)
  3. 🔔 Notify — Proactive notifications (orders, inventory, alerts)
  4. ✅ Approve — Approval flows (supply source, skill publish, refunds)

Architecture:
  Gateway → FeishuService (this module)
              ↓
         ┌────┴────┐
         ↓         ↓
   Feishu Bot   Event Bus
   (WebSocket)  (consumers call FeishuService.notify())

Usage:
  from feishu_service import get_feishu_service
  service = get_feishu_service()
  await service.notify(user_id, "order:paid", {"order_id": "123", "amount": 99.9})
  await service.send_card(user_id, title, content, actions)
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


# ── Enums ──


class MessageType(str, Enum):
    TEXT = "text"
    RICH_TEXT = "rich_text"
    CARD = "interactive"
    MARKDOWN = "markdown"


class NotificationType(str, Enum):
    ORDER_CREATED = "order:created"
    ORDER_PAID = "order:paid"
    ORDER_FULFILLED = "order:fulfilled"
    ORDER_REFUNDED = "order:refunded"
    INVENTORY_LOW = "inventory:low"
    INVENTORY_STOCKOUT = "inventory:stockout"
    SUPPLY_ERROR = "supply:error"
    SYSTEM_ALERT = "system:alert"
    TASK_COMPLETED = "task:completed"
    TASK_FAILED = "task:failed"


class ApprovalType(str, Enum):
    SUPPLY_SOURCE_CONNECT = "supply:source:connect"
    SKILL_PUBLISH = "skill:publish"
    REFUND_APPROVAL = "order:refund:approve"
    BULK_SYNC = "sync:bulk:approve"


# ── Data Models ──


@dataclass
class FeishuUser:
    """Feishu user identity."""
    user_id: str
    open_id: str
    name: str = ""
    avatar_url: str = ""
    tenant_key: str = ""


@dataclass
class FeishuMessage:
    """Outgoing message to Feishu."""
    receive_id: str  # user_id or chat_id
    receive_id_type: str = "open_id"  # open_id | user_id | chat_id
    msg_type: MessageType = MessageType.TEXT
    content: str = ""
    card: Optional[Dict[str, Any]] = None


@dataclass
class NotificationPayload:
    """Structured notification data."""
    type: NotificationType
    title: str
    body: str
    data: Dict[str, Any] = field(default_factory=dict)
    priority: str = "normal"  # normal | high | urgent
    actions: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class ApprovalRequest:
    """Approval flow request."""
    approval_id: str
    type: ApprovalType
    title: str
    description: str
    requester: str
    data: Dict[str, Any] = field(default_factory=dict)
    actions: List[Dict[str, str]] = field(default_factory=list)
    expires_at: Optional[str] = None


# ── Notification Templates ──

_NOTIFICATION_TEMPLATES: Dict[NotificationType, Dict[str, str]] = {
    NotificationType.ORDER_CREATED: {
        "title": "📦 新订单",
        "emoji": "📦",
        "color": "blue",
    },
    NotificationType.ORDER_PAID: {
        "title": "💰 订单已付款",
        "emoji": "💰",
        "color": "green",
    },
    NotificationType.ORDER_FULFILLED: {
        "title": "🚚 订单已发货",
        "emoji": "🚚",
        "color": "green",
    },
    NotificationType.ORDER_REFUNDED: {
        "title": "💸 订单已退款",
        "emoji": "💸",
        "color": "red",
    },
    NotificationType.INVENTORY_LOW: {
        "title": "⚠️ 库存预警",
        "emoji": "⚠️",
        "color": "orange",
    },
    NotificationType.INVENTORY_STOCKOUT: {
        "title": "🚫 库存告罄",
        "emoji": "🚫",
        "color": "red",
    },
    NotificationType.SUPPLY_ERROR: {
        "title": "❌ 货源异常",
        "emoji": "❌",
        "color": "red",
    },
    NotificationType.SYSTEM_ALERT: {
        "title": "🔔 系统通知",
        "emoji": "🔔",
        "color": "blue",
    },
    NotificationType.TASK_COMPLETED: {
        "title": "✅ 任务完成",
        "emoji": "✅",
        "color": "green",
    },
    NotificationType.TASK_FAILED: {
        "title": "❌ 任务失败",
        "emoji": "❌",
        "color": "red",
    },
}


# ── Feishu Service ──


class FeishuService:
    """Unified Feishu service for chat, execution, notifications, and approvals."""

    def __init__(self):
        self._app_id = os.getenv("FEISHU_APP_ID", "")
        self._app_secret = os.getenv("FEISHU_APP_SECRET", "")
        self._enabled = bool(self._app_id and self._app_secret)
        self._tenant_access_token: Optional[str] = None
        self._token_expires_at = 0
        self._message_log: List[Dict[str, Any]] = []
        self._approval_store: Dict[str, ApprovalRequest] = {}

        if not self._enabled:
            logger.warning("FeishuService: FEISHU_APP_ID/FEISHU_APP_SECRET not configured, running in mock mode")

    # ── Auth ──

    async def _get_tenant_access_token(self) -> Optional[str]:
        """Get or refresh tenant access token."""
        if self._tenant_access_token and time.time() < self._token_expires_at:
            return self._tenant_access_token

        if not self._enabled:
            return None

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
                    json={
                        "app_id": self._app_id,
                        "app_secret": self._app_secret,
                    },
                )
                data = resp.json()
                if data.get("code") == 0:
                    self._tenant_access_token = data["tenant_access_token"]
                    self._token_expires_at = time.time() + data.get("expire", 7200) - 300
                    return self._tenant_access_token
                logger.error("Feishu auth failed: %s", data)
        except Exception as e:
            logger.error("Feishu auth error: %s", e)

        return None

    # ── 1. Chat ──

    async def send_message(
        self,
        receive_id: str,
        content: str,
        receive_id_type: str = "open_id",
        msg_type: MessageType = MessageType.TEXT,
    ) -> Dict[str, Any]:
        """Send a message to a user or group chat.

        Args:
            receive_id: Feishu user ID or chat ID
            content: Message text content
            receive_id_type: 'open_id' | 'user_id' | 'chat_id'
            msg_type: Message type

        Returns:
            API response dict
        """
        if not self._enabled:
            return {"mock": True, "receive_id": receive_id, "content": content}

        token = await self._get_tenant_access_token()
        if not token:
            return {"error": "Failed to get access token"}

        try:
            import httpx
            msg_content = json.dumps({"text": content}) if msg_type == MessageType.TEXT else content

            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://open.feishu.cn/open-apis/im/v1/messages",
                    params={"receive_id_type": receive_id_type},
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "receive_id": receive_id,
                        "msg_type": msg_type.value,
                        "content": msg_content,
                    },
                )
                result = resp.json()
                self._log_message("send", receive_id, content, result)
                return result
        except Exception as e:
            logger.error("Feishu send message error: %s", e)
            return {"error": str(e)}

    async def send_card(
        self,
        receive_id: str,
        title: str,
        content: str,
        actions: List[Dict[str, str]] = None,
        receive_id_type: str = "open_id",
    ) -> Dict[str, Any]:
        """Send an interactive card message with optional action buttons."""
        card = self._build_card(title, content, actions or [])
        return await self.send_message(
            receive_id,
            json.dumps(card),
            receive_id_type=receive_id_type,
            msg_type=MessageType.CARD,
        )

    async def reply_message(
        self,
        message_id: str,
        content: str,
        msg_type: MessageType = MessageType.TEXT,
    ) -> Dict[str, Any]:
        """Reply to an existing message thread."""
        if not self._enabled:
            return {"mock": True, "message_id": message_id, "content": content}

        token = await self._get_tenant_access_token()
        if not token:
            return {"error": "Failed to get access token"}

        try:
            import httpx
            msg_content = json.dumps({"text": content}) if msg_type == MessageType.TEXT else content

            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://open.feishu.cn/open-apis/im/v1/messages/reply",
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "message_id": message_id,
                        "content": msg_content,
                        "msg_type": msg_type.value,
                    },
                )
                return resp.json()
        except Exception as e:
            logger.error("Feishu reply error: %s", e)
            return {"error": str(e)}

    # ── 2. Execute (Code Runner) ──

    async def execute_code(
        self,
        code: str,
        language: str = "python",
        chat_id: str = "",
    ) -> Dict[str, Any]:
        """Execute code via the configured backend (AtomCode/Codex/ZCode).

        This is a thin wrapper around code_runner.BackendRunner,
        providing a unified interface for the Feishu chat context.
        """
        try:
            from code_runner import BackendRunner
            runner = BackendRunner()
            result = await runner.run(code, chat_id=chat_id)
            return {
                "success": True,
                "output": result,
                "language": language,
                "executed_at": datetime.utcnow().isoformat(),
            }
        except ImportError:
            logger.warning("code_runner not available, code execution disabled")
            return {
                "success": False,
                "error": "Code runner not available",
                "output": "代码执行模块未安装",
            }
        except Exception as e:
            logger.error("Code execution error: %s", e)
            return {
                "success": False,
                "error": str(e),
                "output": f"执行失败: {e}",
            }

    # ── 3. Notify ──

    async def notify(
        self,
        receive_id: str,
        notification_type: NotificationType,
        title: str = "",
        body: str = "",
        data: Dict[str, Any] = None,
        priority: str = "normal",
        actions: List[Dict[str, str]] = None,
        receive_id_type: str = "open_id",
    ) -> Dict[str, Any]:
        """Send a structured notification to a user.

        Uses templates for common notification types, falls back to
        custom title/body for unknown types.

        Args:
            receive_id: Target user ID
            notification_type: Type of notification (determines template)
            title: Custom title (overrides template)
            body: Notification body text
            data: Additional data (included in card)
            priority: 'normal' | 'high' | 'urgent'
            actions: Optional action buttons
            receive_id_type: ID type
        """
        template = _NOTIFICATION_TEMPLATES.get(notification_type, {})
        emoji = template.get("emoji", "📢")
        color = template.get("color", "blue")
        display_title = title or template.get("title", notification_type.value)

        # Build rich card for the notification
        card_title = f"{emoji} {display_title}"
        card_content = body or self._format_notification_body(notification_type, data or {})

        # Add action buttons
        card_actions = actions or []
        if notification_type == NotificationType.ORDER_PAID and "order_id" in (data or {}):
            card_actions.append({
                "tag": "button",
                "text": {"tag": "plain_text", "content": "查看订单"},
                "type": "primary",
                "url": f"/orders/{data['order_id']}",
            })
        if notification_type == NotificationType.INVENTORY_LOW and "product_id" in (data or {}):
            card_actions.append({
                "tag": "button",
                "text": {"tag": "plain_text", "content": "补货"},
                "type": "primary",
                "url": f"/products/{data['product_id']}",
            })

        result = await self.send_card(
            receive_id,
            title=card_title,
            content=card_content,
            actions=card_actions,
            receive_id_type=receive_id_type,
        )

        self._log_notification(notification_type, receive_id, result)
        return result

    async def broadcast(
        self,
        receive_ids: List[str],
        notification_type: NotificationType,
        title: str = "",
        body: str = "",
        data: Dict[str, Any] = None,
    ) -> List[Dict[str, Any]]:
        """Send notification to multiple users in parallel."""
        import asyncio
        tasks = [
            self.notify(uid, notification_type, title, body, data)
            for uid in receive_ids
        ]
        return list(await asyncio.gather(*tasks, return_exceptions=True))

    # ── 4. Approve ──

    async def send_approval(
        self,
        approver_id: str,
        request: ApprovalRequest,
        receive_id_type: str = "open_id",
    ) -> Dict[str, Any]:
        """Send an approval request to a user with approve/reject buttons.

        The approval flow:
          1. Send card with approve/reject buttons
          2. User clicks button → Feishu callback
          3. Callback handler processes the decision
          4. Result stored in approval_store
        """
        self._approval_store[request.approval_id] = request

        card = self._build_approval_card(request)
        result = await self.send_message(
            approver_id,
            json.dumps(card),
            receive_id_type=receive_id_type,
            msg_type=MessageType.CARD,
        )

        logger.info("Approval sent: %s to %s (type=%s)", request.approval_id, approver_id, request.type)
        return result

    def get_approval(self, approval_id: str) -> Optional[ApprovalRequest]:
        """Get pending approval request by ID."""
        return self._approval_store.get(approval_id)

    def resolve_approval(self, approval_id: str, approved: bool, reason: str = "") -> Optional[Dict[str, Any]]:
        """Resolve an approval request."""
        request = self._approval_store.get(approval_id)
        if not request:
            return None

        result = {
            "approval_id": approval_id,
            "type": request.type,
            "approved": approved,
            "reason": reason,
            "resolved_at": datetime.utcnow().isoformat(),
            "data": request.data,
        }

        if approved:
            del self._approval_store[approval_id]

        return result

    # ── Card Builders ──

    def _build_card(
        self,
        title: str,
        content: str,
        actions: List[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Build a Feishu interactive card."""
        elements = [{"tag": "div", "text": {"tag": "lark_md", "content": content}}]

        if actions:
            actions_elem = {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": action.get("label", "Action")},
                        "type": action.get("type", "default"),
                        "url": action.get("url", ""),
                    }
                    for action in actions
                ],
            }
            elements.append(actions_elem)

        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": "blue",
            },
            "elements": elements,
        }

    def _build_video_card(
        self,
        title: str,
        video_url: str,
        preview_url: str = "",
        description: str = "",
        actions: List[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Build a Feishu interactive card with inline video player.

        Uses Feishu Card Video element for direct playback in chat.
        Falls back to a link button if the video element is not supported.

        Args:
            title: Card header title
            video_url: Direct URL to the video file (MP4)
            preview_url: URL to a preview thumbnail image
            description: Description text below the video
            actions: Optional action buttons
        """
        elements = []

        # Card Video element — plays inline in Feishu chat
        if video_url:
            video_elem = {
                "tag": "video",
                "title": {"tag": "plain_text", "content": title},
                "url": video_url,
            }
            if preview_url:
                video_elem["preview_url"] = preview_url
            elements.append(video_elem)

        # Description text
        if description:
            elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": description},
            })

        # Action buttons
        if actions:
            elements.append({
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": action.get("label", "Action")},
                        "type": action.get("type", "default"),
                        "url": action.get("url", ""),
                    }
                    for action in actions
                ],
            })

        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": f"🎬 {title}"},
                "template": "green",
            },
            "elements": elements,
        }

    def _build_game_card(
        self,
        title: str,
        iframe_url: str,
        description: str = "",
        actions: List[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Build a Feishu interactive card with embedded iframe for games.

        Args:
            title: Card header title
            iframe_url: URL to embed in iframe
            description: Description text
            actions: Optional action buttons
        """
        elements = []

        # Card Iframe element — embeds web content directly in chat
        if iframe_url:
            elements.append({
                "tag": "iframe",
                "url": iframe_url,
                "width": 800,
                "height": 600,
                "align": "center",
            })

        if description:
            elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": description},
            })

        if actions:
            elements.append({
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": action.get("label", "Action")},
                        "type": action.get("type", "default"),
                        "url": action.get("url", ""),
                    }
                    for action in actions
                ],
            })

        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": f"🎮 {title}"},
                "template": "purple",
            },
            "elements": elements,
        }

    def _build_approval_card(self, request: ApprovalRequest) -> Dict[str, Any]:
        """Build an approval card with approve/reject buttons."""
        elements = [
            {"tag": "div", "text": {"tag": "lark_md", "content": f"**申请人**: {request.requester}"}},
            {"tag": "div", "text": {"tag": "lark_md", "content": f"**描述**: {request.description}"}},
            {"tag": "hr"},
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "✅ 批准"},
                        "type": "primary",
                        "value": json.dumps({
                            "action": "approve",
                            "approval_id": request.approval_id,
                        }),
                    },
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "❌ 拒绝"},
                        "type": "danger",
                        "value": json.dumps({
                            "action": "reject",
                            "approval_id": request.approval_id,
                        }),
                    },
                ],
            },
        ]

        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": f"📋 审批请求: {request.title}"},
                "template": "orange",
            },
            "elements": elements,
        }

    # ── Helpers ──

    def _format_notification_body(
        self, notification_type: NotificationType, data: Dict[str, Any]
    ) -> str:
        """Format notification body from data dict."""
        lines = []

        if notification_type in (NotificationType.ORDER_CREATED, NotificationType.ORDER_PAID,
                                  NotificationType.ORDER_FULFILLED, NotificationType.ORDER_REFUNDED):
            lines.append(f"**订单号**: {data.get('order_id', 'N/A')}")
            lines.append(f"**金额**: {data.get('amount', 'N/A')} {data.get('currency', 'USD')}")
            if data.get('customer_name'):
                lines.append(f"**客户**: {data['customer_name']}")
            if data.get('tracking_number'):
                lines.append(f"**物流单号**: {data['tracking_number']}")

        elif notification_type in (NotificationType.INVENTORY_LOW, NotificationType.INVENTORY_STOCKOUT):
            lines.append(f"**商品**: {data.get('title', 'N/A')}")
            lines.append(f"**SKU**: {data.get('sku', 'N/A')}")
            lines.append(f"**当前库存**: {data.get('inventory', 0)}")

        elif notification_type == NotificationType.SUPPLY_ERROR:
            lines.append(f"**适配器**: {data.get('adapter', 'N/A')}")
            lines.append(f"**错误**: {data.get('error', 'Unknown')}")

        elif notification_type == NotificationType.TASK_COMPLETED:
            lines.append(f"**任务**: {data.get('task_name', 'N/A')}")
            lines.append(f"**耗时**: {data.get('duration', 'N/A')}")

        elif notification_type == NotificationType.TASK_FAILED:
            lines.append(f"**任务**: {data.get('task_name', 'N/A')}")
            lines.append(f"**错误**: {data.get('error', 'Unknown')}")

        return "\n".join(lines) if lines else str(data)

    def _log_message(self, direction: str, receive_id: str, content: str, result: Dict):
        """Log message for audit trail."""
        self._message_log.append({
            "direction": direction,
            "receive_id": receive_id,
            "content": content[:200],
            "result": "ok" if not result.get("error") else "error",
            "timestamp": datetime.utcnow().isoformat(),
        })

    def _log_notification(self, ntype: NotificationType, receive_id: str, result: Dict):
        """Log notification for audit trail."""
        self._message_log.append({
            "type": "notification",
            "notification_type": ntype.value,
            "receive_id": receive_id,
            "result": "ok" if not result.get("error") else "error",
            "timestamp": datetime.utcnow().isoformat(),
        })

    # ── Health & Status ──

    @property
    def enabled(self) -> bool:
        """Whether Feishu integration is configured."""
        return self._enabled

    def get_status(self) -> Dict[str, Any]:
        """Get service status."""
        return {
            "enabled": self._enabled,
            "authenticated": self._tenant_access_token is not None,
            "message_count": len(self._message_log),
            "pending_approvals": len(self._approval_store),
            "app_id_configured": bool(self._app_id),
            "app_secret_configured": bool(self._app_secret),
        }

    def get_message_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent message log."""
        return self._message_log[-limit:]


# ── Singleton ──

_service_instance: Optional[FeishuService] = None


def get_feishu_service() -> FeishuService:
    """Get or create the global FeishuService instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = FeishuService()
    return _service_instance


def reset_feishu_service():
    """Reset the global instance (for testing)."""
    global _service_instance
    _service_instance = None
