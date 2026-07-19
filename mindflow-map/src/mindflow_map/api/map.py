"""地图相关 API"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from mindflow_map.tools.baidu_map import BaiduMapTool

router = APIRouter()
baidu_map = BaiduMapTool()


class LocationSearchRequest(BaseModel):
    query: str
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class RoutePlanRequest(BaseModel):
    origin: str
    destination: str
    mode: str = "driving"  # driving/transit/walking
    departure_time: Optional[str] = None


@router.post("/search")
async def search_location(request: LocationSearchRequest):
    """搜索地点"""
    try:
        result = await baidu_map.search_location(
            query=request.query,
            city=request.city,
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/route")
async def plan_route(request: RoutePlanRequest):
    """规划路线"""
    try:
        result = await baidu_map.plan_route(
            origin=request.origin,
            destination=request.destination,
            mode=request.mode,
            departure_time=request.departure_time,
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/geocode")
async def geocode(address: str):
    """地址转坐标"""
    try:
        result = await baidu_map.geocode(address)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
