"""地图相关 API"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from mindflow_map.config import settings
from mindflow_map.schemas.map import LocationSearchRequest, RoutePlanRequest
from mindflow_map.tools.baidu_map import BaiduMapTool

router = APIRouter()


def _demo_search_location(query: str, city: Optional[str] = None) -> dict:
    return {
        "status": 0,
        "message": "demo mode",
        "results": [
            {
                "name": f"{query}（演示结果）",
                "address": f"{city or '北京市'}演示地址",
                "location": {"lat": 39.9042, "lng": 116.4074},
                "uid": "demo-uid-001",
            }
        ],
    }


def _demo_plan_route(origin: str, destination: str, mode: str = "driving", departure_time: Optional[str] = None) -> dict:
    return {
        "status": 0,
        "message": "demo mode",
        "result": {
            "origin": {"address": origin, "location": {"lat": 39.9042, "lng": 116.4074}},
            "destination": {"address": destination, "location": {"lat": 39.9163, "lng": 116.3972}},
            "routes": [
                {
                    "distance": "5.2公里",
                    "duration": "15分钟",
                    "steps": [{"instruction": "沿演示路线行驶"}, {"instruction": "到达目的地"}],
                }
            ],
        },
    }


def _demo_geocode(address: str) -> dict:
    return {
        "status": 0,
        "message": "demo mode",
        "result": {"location": {"lat": 39.9042, "lng": 116.4074}, "precise": 1, "confidence": 80, "level": "street"},
    }


@router.post("/search")
async def search_location(request: LocationSearchRequest):
    """搜索地点"""
    if settings.demo_mode or not settings.baidu_map_auth_token:
        return {"success": True, "data": _demo_search_location(request.query, request.city)}
    try:
        baidu_map = BaiduMapTool()
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
    if settings.demo_mode or not settings.baidu_map_auth_token:
        return {"success": True, "data": _demo_plan_route(request.origin, request.destination, request.mode, request.departure_time)}
    try:
        baidu_map = BaiduMapTool()
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
    if settings.demo_mode or not settings.baidu_map_auth_token:
        return {"success": True, "data": _demo_geocode(address)}
    try:
        baidu_map = BaiduMapTool()
        result = await baidu_map.geocode(address)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
