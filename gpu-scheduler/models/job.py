"""任务模型 — 定义 GPU 任务的数据结构和状态机"""

from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class JobStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"           # 等待调度
    SCHEDULED = "scheduled"       # 已分配资源
    RUNNING = "running"           # 运行中
    COMPLETED = "completed"       # 完成
    FAILED = "failed"             # 失败
    CANCELLED = "cancelled"       # 已取消


class JobPriority(int, Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class JobRequest(BaseModel):
    """提交任务的请求"""
    name: str = Field(..., min_length=1, max_length=128, description="任务名称")
    gpu_count: int = Field(default=1, ge=1, le=8, description="申请 GPU 数量")
    gpu_memory_mb: int = Field(default=0, ge=0, description="显存需求(MB)，0=整卡")
    priority: JobPriority = Field(default=JobPriority.NORMAL, description="优先级")
    duration_seconds: int = Field(default=300, ge=10, le=86400, description="预计运行时长(秒)")
    command: str = Field(default="python train.py", description="执行命令")
    preemptible: bool = Field(default=True, description="是否可被抢占")
    tenant_id: str = Field(default="default", description="租户 ID")


class Job(BaseModel):
    """GPU 任务"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    gpu_count: int = 1
    gpu_memory_mb: int = 0
    priority: JobPriority = JobPriority.NORMAL
    duration_seconds: int = 300
    command: str = "python train.py"
    preemptible: bool = True
    tenant_id: str = "default"
    status: JobStatus = JobStatus.PENDING
    assigned_node: Optional[str] = None       # 分配的节点 ID
    assigned_gpus: list[int] = []             # 分配的 GPU 索引
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    preemptible: bool = True

    @property
    def wait_time_seconds(self) -> float:
        """等待时长"""
        if self.started_at:
            return (self.started_at - self.created_at).total_seconds()
        return (datetime.utcnow() - self.created_at).total_seconds()

    @property
    def run_time_seconds(self) -> float:
        """运行时长"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        if self.started_at:
            return (datetime.utcnow() - self.started_at).total_seconds()
        return 0.0

    def to_response(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "priority": self.priority.value,
            "gpu_count": self.gpu_count,
            "gpu_memory_mb": self.gpu_memory_mb,
            "tenant_id": self.tenant_id,
            "assigned_node": self.assigned_node,
            "assigned_gpus": self.assigned_gpus,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "wait_time_seconds": self.wait_time_seconds,
            "run_time_seconds": self.run_time_seconds,
        }
