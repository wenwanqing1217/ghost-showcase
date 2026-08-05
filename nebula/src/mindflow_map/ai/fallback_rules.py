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
    shopify_keywords = ["店铺", "电商", "Shopify", "商品", "产品"]
    if any(kw in text for kw in shopify_keywords):
        return {
            "type": "shopify",
            "action": "optimize",
            "description": "优化店铺",
            "confidence": 0.75,
        }

    # 渠道文案意图（闲鱼/小红书种草文案）
    copy_keywords = ["闲鱼文案", "小红书文案", "种草笔记", "写个文案", "帮我写文案", "挂单文案"]
    if any(kw in text for kw in copy_keywords):
        # 尝试提取商品名
        import re as _re
        product = ""
        # "卖XX" 或 "XX的文案"
        m = _re.search(r"卖(.+?)(?:的|文案|$)", text)
        if m:
            product = m.group(1).strip()
        else:
            m = _re.search(r"(.+?)(?:种草|文案|笔记)", text)
            if m:
                product = m.group(1).strip()
        if not product:
            product = text.replace("帮我写", "").replace("文案", "").strip()

        return {
            "type": "channel_copy",
            "action": "generate",
            "title": product,
            "product": product,
            "description": f"生成{product}文案",
            "confidence": 0.85,
        }

    # 视频生成意图
    video_keywords = ["做个视频", "生成视频", "做个种草视频", "帮我做视频", "生成一个视频"]
    if any(kw in text for kw in video_keywords):
        import re as _re
        subject = ""
        m = _re.search(r"(?:视频|种草视频)(?:[:：])?\s*(.+)", text)
        if m:
            subject = m.group(1).strip()
        if not subject:
            m = _re.search(r"(.+?)(?:的)?(?:种草)?视频", text)
            if m:
                subject = m.group(1).strip()
        if not subject:
            subject = text.replace("帮我做", "").replace("生成", "").replace("视频", "").strip()

        return {
            "type": "video_generate",
            "action": "create",
            "title": subject,
            "subject": subject,
            "description": f"生成视频：{subject}",
            "confidence": 0.85,
        }

    # 视频发布意图
    publish_keywords = ["发布视频", "发到tiktok", "发到TikTok", "上传视频", "发到抖音"]
    if any(kw in text for kw in publish_keywords):
        import re as _re
        task_id = ""
        m = _re.search(r"([a-f0-9]{8,})", text, _re.IGNORECASE)
        if m:
            task_id = m.group(1)
        platforms = "tiktok"
        if "youtube" in text.lower():
            platforms = "youtube"
        elif "instagram" in text.lower():
            platforms = "instagram"

        return {
            "type": "video_publish",
            "action": "upload",
            "task_id": task_id,
            "platforms": platforms,
            "description": f"发布视频到 {platforms}",
            "confidence": 0.8,
        }

    # 默认：对话
    return {
        "type": "chat",
        "action": "reply",
        "description": "普通对话",
        "confidence": 0.5,
    }
