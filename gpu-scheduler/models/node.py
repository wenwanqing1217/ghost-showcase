"""GPU 节点模型 — 定义 GPU 节点和设备的数据结构"""

from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class GPUStatus(str, Enum):
    """GPU 设备状态"""
    AVAILABLE = "available"       # 可用
    ALLOCATED = "allocated"       # 已分配
    MIG_SLICE = "mig_slice"      # MIG 切分中
    OFFLINE = "offline"          # 离线


class MIGProfile(str, Enum):
    """MIG 切分配置 (A100/H100 支持)"""
    FULL = "full"                 # 整卡
    ONE_10G = "1g.10gb"          # 1/7 卡，10GB 显存
    TWO_20G = "2g.20gb"          # 2/7 卡，20GB 显存
    THREE_40G = "3g.40gb"        # 3/7 卡，40GB 显存


class GPUDevice(BaseModel):
    """单个 GPU 设备"""
    index: int = Field(..., description="GPU 索引")
    name: str = Field(default="NVIDIA A100-SXM4-80GB", description="GPU 型号")
    total_memory_mb: int = Field(default=81920, description="总显存(MB)")
    used_memory_mb: int = Field(default=0, description="已用显存(MB)")
    utilization: float = Field(default=0.0, ge=0.0, le=100.0, description="利用率(%)")
    temperature: float = Field(default=35.0, ge=0.0, le=100.0, description="温度(℃)")
    power_watts: float = Field(default=0.0, description="功耗(W)")
    status: GPUStatus = Field(default=GPUStatus.AVAILABLE)
    mig_profile: MIGProfile = Field(default=MIGProfile.FULL)
    assigned_job_id: Optional[str] = None

    @property
    def free_memory_mb(self) -> int:
        return self.total_memory_mb - self.used_memory_mb

    @property
    def is_available(self) -> bool:
        return self.status == GPUStatus.AVAILABLE and self.assigned_job_id is None

    def can_fit(self, memory_mb: int) -> bool:
        """检查是否能容纳指定显存需求"""
        if not self.is_available:
            return False
        if memory_mb == 0:
            return True  # 整卡需求
        return self.free_memory_mb >= memory_mb


class GPUNode(BaseModel):
    """GPU 节点（一台物理机）"""
    id: str = Field(..., description="节点 ID")
    name: str = Field(..., description="节点名称")
    region: str = Field(default="cn-east-1", description="区域")
    gpus: list[GPUDevice] = Field(default_factory=list)
    labels: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_healthy: bool = Field(default=True)

    @property
    def total_gpus(self) -> int:
        return len(self.gpus)

    @property
    def available_gpus(self) -> int:
        return sum(1 for g in self.gpus if g.is_available)

    @property
    def total_memory_mb(self) -> int:
        return sum(g.total_memory_mb for g in self.gpus)

    @property
    def used_memory_mb(self) -> int:
        return sum(g.used_memory_mb for g in self.gpus)

    @property
    def avg_utilization(self) -> float:
        if not self.gpus:
            return 0.0
        return sum(g.utilization for g in self.gpus) / len(self.gpus)

    @property
    def avg_temperature(self) -> float:
        if not self.gpus:
            return 0.0
        return sum(g.temperature for g in self.gpus) / len(self.gpus)

    def to_response(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "region": self.region,
            "total_gpus": self.total_gpus,
            "available_gpus": self.available_gpus,
            "total_memory_mb": self.total_memory_mb,
            "used_memory_mb": self.used_memory_mb,
            "avg_utilization": round(self.avg_utilization, 1),
            "avg_temperature": round(self.avg_temperature, 1),
            "is_healthy": self.is_healthy,
            "gpus": [
                {
                    "index": g.index,
                    "name": g.name,
                    "status": g.status.value,
                    "total_memory_mb": g.total_memory_mb,
                    "used_memory_mb": g.used_memory_mb,
                    "utilization": g.utilization,
                    "temperature": g.temperature,
                    "mig_profile": g.mig_profile.value,
                    "assigned_job_id": g.assigned_job_id,
                }
                for g in self.gpus
            ],
        }
