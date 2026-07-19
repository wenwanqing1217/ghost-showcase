"""自动化模块 API"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from mindflow_map.config import settings

router = APIRouter()


class DouyinPublishRequest(BaseModel):
    title: str
    content: str


class ShopifyProductRequest(BaseModel):
    title: str
    body_html: str
    price: float


@router.post("/douyin/publish")
async def douyin_publish(request: DouyinPublishRequest):
    """抖音短剧发布"""
    if not settings.douyin_username or not settings.douyin_password:
        return {
            "success": False,
            "platform": "抖音短剧",
            "demo": True,
            "note": "未配置 DOUYIN_USERNAME / DOUYIN_PASSWORD，当前返回模拟结果。",
            "title": request.title,
            "url": "https://www.douyin.com/creator-center",
        }

    try:
        from mindflow_map.automation.douyin import DouyinAutomation
        douyin = DouyinAutomation()
        result = await douyin.publish(title=request.title, content=request.content)
        return {
            "success": result.get("success", False),
            "platform": "抖音短剧",
            "demo": False,
            **result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/douyin/stats")
async def douyin_stats():
    """抖音数据统计"""
    if not settings.douyin_username or not settings.douyin_password:
        return {
            "platform": "抖音短剧",
            "demo": True,
            "note": "未配置 DOUYIN_USERNAME / DOUYIN_PASSWORD，当前返回模拟数据。",
            "data": {
                "views": 0,
                "likes": 0,
                "shares": 0,
            },
        }

    try:
        from mindflow_map.automation.douyin import DouyinAutomation
        douyin = DouyinAutomation()
        result = await douyin.get_stats()
        return {
            "platform": "抖音短剧",
            "demo": False,
            **result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shopify/products")
async def shopify_products():
    """Shopify 商品列表"""
    if not settings.shopify_shop_domain or not settings.shopify_access_token:
        return {
            "success": False,
            "platform": "shopify",
            "demo": True,
            "note": "未配置 SHOPIFY_SHOP_DOMAIN / SHOPIFY_ACCESS_TOKEN，当前返回模拟结果。",
            "products": [],
        }

    try:
        from mindflow_map.automation.shopify import ShopifyClient
        client = ShopifyClient()
        result = await client.list_products()
        return {
            "success": True,
            "platform": "shopify",
            "demo": False,
            **result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/shopify/products")
async def shopify_create_product(request: ShopifyProductRequest):
    """Shopify 创建商品"""
    if not settings.shopify_shop_domain or not settings.shopify_access_token:
        return {
            "success": False,
            "platform": "shopify",
            "demo": True,
            "note": "未配置 SHOPIFY_SHOP_DOMAIN / SHOPIFY_ACCESS_TOKEN，当前返回模拟结果。",
            "product": {
                "title": request.title,
                "body_html": request.body_html,
                "price": request.price,
            },
        }

    try:
        from mindflow_map.automation.shopify import ShopifyClient
        client = ShopifyClient()
        result = await client.create_product(
            {
                "title": request.title,
                "body_html": request.body_html,
                "price": request.price,
            }
        )
        return {
            "success": True,
            "platform": "shopify",
            "demo": False,
            **result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
