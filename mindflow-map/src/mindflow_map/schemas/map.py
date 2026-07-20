"""地图相关请求/响应模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class LocationSearchRequest(BaseModel):
    """地点搜索请求。"""

    query: str = Field(..., min_length=1, max_length=200, description="搜索关键词")
    city: str | None = Field(default=None, max_length=100, description="城市名称，可选")


class RoutePlanRequest(BaseModel):
    """路线规划请求。"""

    origin: str = Field(..., min_length=1, max_length=200, description="起点")
    destination: str = Field(..., min_length=1, max_length=200, description="终点")
    mode: str = Field(default="driving", description="出行方式：driving/walking/transit")
    departure_time: str | None = Field(default=None, description="出发时间，ISO 8601 格式，可选")
