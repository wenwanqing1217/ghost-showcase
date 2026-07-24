"""百度地图工具 - 封装百度地图 Agent Plan API — 复用单一 httpx 客户端"""

import httpx
from typing import Any, Dict, List, Optional

from mindflow_map.config import settings


class BaiduMapTool:
    """百度地图 Agent Plan API 封装 — 复用实例级别 httpx.AsyncClient

    使用 Bearer Token 鉴权，调用 Agent Plan 能力：
    - 语义化地点检索
    - AI 路线规划
    - 地理编码与逆地理编码
    - 天气查询
    """

    def __init__(self):
        self.auth_token = settings.baidu_map_auth_token
        self.base_url = "https://api.map.baidu.com/agent_plan/v1"
        # 复用连接池，避免每请求创建新 client
        self._client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """发送 HTTP 请求"""
        if self.auth_token:
            params["baidu_map_auth_token"] = self.auth_token

        response = await self._client.get(
            f"{self.base_url}/{endpoint}",
            params=params,
        )
        response.raise_for_status()
        data = response.json()

        # 检查百度地图 API 业务错误码
        status = data.get("status")
        if status not in (0, "0", None):
            message = data.get("message", "未知错误")
            return {
                "message": f"百度地图 API 错误：{message}",
                "status": status,
                "raw": data,
            }

        return data.get("result", data)

    async def search_location(
        self,
        query: str,
        city: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> Dict[str, Any]:
        """地点搜索（语义化 AI 地点检索）"""
        params = {
            "user_raw_request": query,
        }
        if city:
            params["region"] = city
        if latitude is not None and longitude is not None:
            params["center"] = f"{latitude:.6f},{longitude:.6f}"
        
        data = await self._request("place", params)
        return data
    
    async def geocode(self, address: str, region: Optional[str] = None) -> Dict[str, Any]:
        """地址转坐标"""
        params = {"address": address}
        if region:
            params["region"] = region
        
        data = await self._request("geocoding", params)
        return data
    
    async def reverse_geocode(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """坐标转地址"""
        params = {"location": f"{latitude:.6f},{longitude:.6f}"}
        data = await self._request("reverse_geocoding", params)
        return data
    
    async def plan_route(
        self,
        origin: str,
        destination: str,
        mode: str = "driving",
        departure_time: Optional[str] = None,
        origin_lat: Optional[float] = None,
        origin_lng: Optional[float] = None,
        dest_lat: Optional[float] = None,
        dest_lng: Optional[float] = None,
    ) -> Dict[str, Any]:
        """路线规划（语义化 AI 路线规划）"""
        # 映射交通方式
        mode_map = {
            "driving": "驾车",
            "transit": "公交",
            "walking": "步行",
            "riding": "骑行",
        }
        travel_mode = mode_map.get(mode, "驾车")
        
        if origin:
            user_raw_request = f"帮我规划从{origin}到{destination}的{travel_mode}路线"
        else:
            user_raw_request = f"帮我规划到{destination}的{travel_mode}路线"
        
        params = {"user_raw_request": user_raw_request}
        
        # 如果有坐标，传入 location 参数
        if origin_lat is not None and origin_lng is not None:
            params["location"] = f"{origin_lat:.6f},{origin_lng:.6f}"
        
        data = await self._request("direction", params)
        return data
    
    async def weather(self, region: Optional[str] = None, latitude: Optional[float] = None, longitude: Optional[float] = None) -> Dict[str, Any]:
        """天气查询"""
        params = {}
        if region:
            params["region"] = region
        if latitude is not None and longitude is not None:
            params["location"] = f"{latitude:.6f},{longitude:.6f}"
        
        data = await self._request("weather", params)
        return data

    @staticmethod
    def render_map_url(resource_key: str) -> str:
        """生成百度地图展示链接"""
        if not resource_key:
            return ""
        return f"https://lbs.baidu.com/mapstatic/agentui_resource.html?resource_key={resource_key}"
