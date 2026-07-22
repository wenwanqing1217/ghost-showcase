"""地图相关 API"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import httpx

from mindflow_map.config import settings
from mindflow_map.schemas.map import (
    GeocodeRequest,
    LocationSearchRequest,
    RoutePlanRequest,
    WeatherQueryRequest,
)
from mindflow_map.tools.baidu_map import BaiduMapTool

router = APIRouter()


def _demo_search_location(query: str, city: Optional[str] = None) -> dict:
    return {
        "status": 0,
        "message": "ok",
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
        "message": "ok",
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
        "message": "ok",
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
            latitude=request.latitude,
            longitude=request.longitude,
        )
        return {"success": True, "data": result}
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"百度地图 API HTTP 错误: {e.response.status_code}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"百度地图 API 网络错误: {e}")
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=500, detail=f"百度地图响应解析失败: {e}")


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
            origin_lat=request.origin_latitude,
            origin_lng=request.origin_longitude,
            dest_lat=request.destination_latitude,
            dest_lng=request.destination_longitude,
        )
        return {"success": True, "data": result}
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"百度地图 API HTTP 错误: {e.response.status_code}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"百度地图 API 网络错误: {e}")
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=500, detail=f"路线响应解析失败: {e}")


@router.get("/geocode")
async def geocode(address: str, region: Optional[str] = Query(default=None, max_length=100)):
    """地址转坐标"""
    if settings.demo_mode or not settings.baidu_map_auth_token:
        return {"success": True, "data": _demo_geocode(address)}
    try:
        baidu_map = BaiduMapTool()
        result = await baidu_map.geocode(address, region=region)
        return {"success": True, "data": result}
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"百度地图 API HTTP 错误: {e.response.status_code}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"百度地图 API 网络错误: {e}")
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=500, detail=f"地理编码响应解析失败: {e}")


_WEATHER_TOOL_FAILED = "天气查询暂时不可用：工具调用失败"


@router.post("/weather")
async def weather_query(request: WeatherQueryRequest):
    """天气查询"""
    if settings.demo_mode or not settings.baidu_map_auth_token:
        return {
            "success": True,
            "data": {
                "status": 0,
                "message": "ok",
                "result": {
                    "region": request.region or "北京市",
                    "location": {"lat": 39.9042, "lng": 116.4074},
                    "weather": "演示天气：晴 26°C",
                },
            },
        }
    try:
        baidu_map = BaiduMapTool()
        result = await baidu_map.weather(
            region=request.region,
            latitude=request.latitude,
            longitude=request.longitude,
        )
        if isinstance(result, dict) and result.get("status") not in (0, "0", None):
            message = result.get("message", "未知错误")
            raise HTTPException(status_code=502, detail=f"{_WEATHER_TOOL_FAILED}：{message}")
        return {"success": True, "data": result}
    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"{_WEATHER_TOOL_FAILED}：HTTP {e.response.status_code}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"{_WEATHER_TOOL_FAILED}：网络错误 {e}")
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=500, detail=f"{_WEATHER_TOOL_FAILED}：响应解析失败 {e}")
