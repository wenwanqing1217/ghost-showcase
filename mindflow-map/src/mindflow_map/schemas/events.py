from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class EventType(str, Enum):
    # Feishu
    FEISHU_MESSAGE = "feishu.message"
    FEISHU_APPROVAL = "feishu.approval"
    # WeChat
    WECHAT_MESSAGE = "wechat.message"
    WECHAT_EVENT = "wechat.event"
    # Internal
    WORKFLOW_TRIGGERED = "workflow.triggered"
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_RESULT = "approval.result"


class Platform(str, Enum):
    FEISHU = "feishu"
    WECHAT = "wechat"
    INTERNAL = "internal"


class BaseEvent(BaseModel):
    event_id: str
    event_type: EventType
    platform: Platform
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    payload: Dict[str, Any]
    source: str = "unknown"


class FeishuMessageEvent(BaseEvent):
    event_type: EventType = EventType.FEISHU_MESSAGE
    platform: Platform = Platform.FEISHU
    message_id: str
    chat_id: str
    sender_id: str
    text: str
    msg_type: str = "text"


class WechatMessageEvent(BaseEvent):
    event_type: EventType = EventType.WECHAT_MESSAGE
    platform: Platform = Platform.WECHAT
    from_user: str
    to_user: str
    content: str
    msg_id: Optional[int] = None
    create_time: int


class ApprovalRequestedEvent(BaseEvent):
    event_type: EventType = EventType.APPROVAL_REQUESTED
    platform: Platform = Platform.INTERNAL
    approval_id: str
    workflow_id: str
    requester_id: str
    level: int = 1
    data: Dict[str, Any] = Field(default_factory=dict)


class ApprovalResultEvent(BaseEvent):
    event_type: EventType = EventType.APPROVAL_RESULT
    platform: Platform = Platform.INTERNAL
    approval_id: str
    workflow_id: str
    approved: bool
    approver_id: str
    comment: Optional[str] = None
