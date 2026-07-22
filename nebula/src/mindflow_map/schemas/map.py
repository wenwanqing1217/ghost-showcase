"""地图相关请求/响应模型。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class LocationSearchRequest(BaseModel):
    """地点搜索请求。"""

    query: str = Field(..., min_length=1, max_length=200, description="搜索关键词")
    city: str | None = Field(default=None, max_length=100, description="城市名称，可选")
    latitude: float | None = Field(default=None, description="纬度，可选")
    longitude: float | None = Field(default=None, description="经度，可选")


class RoutePlanRequest(BaseModel):
    """路线规划请求。"""

    origin: str = Field(..., min_length=1, max_length=200, description="起点")
    destination: str = Field(..., min_length=1, max_length=200, description="终点")
    mode: Literal["driving", "walking", "transit", "riding"] = Field(
        default="driving",
        description="出行方式",
    )
    departure_time: str | None = Field(default=None, description="出发时间，ISO 8601 格式，可选")
    origin_latitude: float | None = Field(default=None, description="起点纬度，可选")
    origin_longitude: float | None = Field(default=None, description="起点经度，可选")
    destination_latitude: float | None = Field(default=None, description="终点纬度，可选")
    destination_longitude: float | None = Field(default=None, description="终点经度，可选")


class WeatherQueryRequest(BaseModel):
    """天气查询请求。"""

    region: str | None = Field(default=None, max_length=100, description="地区名称，可选")
    latitude: float | None = Field(default=None, description="纬度，可选")
    longitude: float | None = Field(default=None, description="经度，可选")


class GeocodeRequest(BaseModel):
    """地理编码请求。"""

    address: str = Field(..., min_length=1, max_length=200, description="地址")
    region: str | None = Field(default=None, max_length=100, description="城市或行政区，可选")
