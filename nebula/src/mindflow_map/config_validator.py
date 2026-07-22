"""平台配置校验 - 启动时检查微信公众号/抖音/Shopify 配置"""

from __future__ import annotations

from typing import Any, Dict

from mindflow_map.config import settings


def check_wechat() -> Dict[str, Any]:
    """检查微信公众号配置"""
    missing = []
    if not settings.wechat_app_id:
        missing.append("WECHAT_APP_ID")
    if not settings.wechat_app_secret:
        missing.append("WECHAT_APP_SECRET")
    if not settings.wechat_token:
        missing.append("WECHAT_TOKEN")

    return {
        "platform": "wechat",
        "configured": len(missing) == 0,
        "missing": missing,
        "message": "微信公众号配置完整" if not missing else f"缺少配置: {', '.join(missing)}",
    }


def check_douyin() -> Dict[str, Any]:
    """检查抖音短剧配置"""
    missing = []
    if not settings.douyin_username:
        missing.append("DOUYIN_USERNAME")
    if not settings.douyin_password:
        missing.append("DOUYIN_PASSWORD")

    return {
        "platform": "douyin",
        "configured": len(missing) == 0,
        "missing": missing,
        "message": "抖音配置完整" if not missing else f"缺少配置: {', '.join(missing)}",
    }


def check_shopify() -> Dict[str, Any]:
    """检查 Shopify 配置"""
    missing = []
    if not settings.shopify_shop_domain:
        missing.append("SHOPIFY_SHOP_DOMAIN")
    if not settings.shopify_access_token:
        missing.append("SHOPIFY_ACCESS_TOKEN")

    return {
        "platform": "shopify",
        "configured": len(missing) == 0,
        "missing": missing,
        "message": "Shopify 配置完整" if not missing else f"缺少配置: {', '.join(missing)}",
    }


def check_shortdramas() -> Dict[str, Any]:
    """检查短剧平台内容预审配置"""
    missing = []
    if not settings.shortdramas_api_url:
        missing.append("SHORTDRAMAS_API_URL")
    if not settings.shortdramas_api_key:
        missing.append("SHORTDRAMAS_API_KEY")

    return {
        "platform": "shortdramas",
        "configured": len(missing) == 0,
        "missing": missing,
        "message": "短剧平台预审配置完整" if not missing else f"缺少配置: {', '.join(missing)}",
    }


def check_all() -> Dict[str, Any]:
    """检查所有平台配置"""
    return {
        "wechat": check_wechat(),
        "douyin": check_douyin(),
        "shopify": check_shopify(),
        "shortdramas": check_shortdramas(),
    }
