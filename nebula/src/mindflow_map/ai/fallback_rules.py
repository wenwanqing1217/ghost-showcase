"""规则引擎：纯函数意图解析，零外部依赖，供 IntentParser LLM 失败时回退使用。"""

from __future__ import annotations

import re
from typing import Any, Dict


def parse_by_rules(text: str) -> Dict[str, Any]:
    """基于关键词和正则的轻量意图解析。"""
    # 地点搜索意图（优先于导航，避免“查一下”被导航抢走）
    search_keywords = ["查一下", "搜一下", "找一下", "有没有", "附近的"]
    if any(kw in text for kw in search_keywords):
        match = re.search(r"(?:查一下|搜一下|找一下|有没有|附近的)\s*([\u4e00-\u9fa5]+)", text)
        query = match.group(1) if match else text

        return {
            "type": "map",
            "action": "search",
            "query": query,
            "description": f"搜索{query}",
            "confidence": 0.85,
        }

    # 地图导航意图
    map_keywords = ["怎么去", "路线", "导航", "地址", "在哪", "位置", "距离", "多远"]
    if any(kw in text for kw in map_keywords) or re.search(r"(?:去|到|在)[\u4e00-\u9fa5]{2,20}?(?:怎么|路线|导航|地址|$)", text):
        destination = ""
        match = re.search(r"(?:去|到|在)([\u4e00-\u9fa5]{2,20}?)(?:怎么|路线|导航|地址|$)", text)
        if match:
            destination = match.group(1)

        return {
            "type": "map",
            "action": "navigate",
            "destination": destination,
            "description": f"导航到{destination}" if destination else "地图查询",
            "confidence": 0.9,
        }

    # 短剧内容预审意图（先于发布判断，避免"预审短剧"被发布抢走）
    precheck_keywords = ["预审", "审核", "查重", "合规", "能不能发", "能不能过", "内容检查"]
    if any(kw in text for kw in precheck_keywords):
        title_match = re.search(r"《(.+?)》", text)
        title = title_match.group(1) if title_match else ""

        return {
            "type": "shortdramas",
            "action": "precheck",
            "title": title,
            "description": f"预审短剧《{title}》" if title else "内容预审",
            "confidence": 0.85,
        }

    # 短剧发布意图
    douyin_keywords = ["发短剧", "发布", "生成剧本", "写剧本", "短剧"]
    if any(kw in text for kw in douyin_keywords):
        title_match = re.search(r"《(.+?)》", text)
        title = title_match.group(1) if title_match else "未命名短剧"

        return {
            "type": "douyin",
            "action": "publish",
            "title": title,
            "description": f"发布短剧《{title}》",
            "confidence": 0.8,
        }

    # 电商优化意图
    shopify_keywords = ["店铺", "电商", "Shopify", "商品", "产品", "文案"]
    if any(kw in text for kw in shopify_keywords):
        return {
            "type": "shopify",
            "action": "optimize",
            "description": "优化店铺",
            "confidence": 0.75,
        }

    # 默认：对话
    return {
        "type": "chat",
        "action": "reply",
        "description": "普通对话",
        "confidence": 0.5,
    }
