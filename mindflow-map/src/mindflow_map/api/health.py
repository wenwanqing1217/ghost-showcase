"""健康检查"""

from fastapi import APIRouter
from datetime import datetime

from mindflow_map.config_validator import check_all

router = APIRouter()


@router.get("/")
async def health_check():
    return {
        "status": "ok",
        "service": "mindflow-map",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/config")
async def config_status():
    """平台配置状态"""
    return check_all()
