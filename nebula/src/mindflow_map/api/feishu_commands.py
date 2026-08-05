"""飞书指令路由器 — 解析用户指令并路由到对应能力

复用已有代码，不重写：
  文案  → DS /api/ai/channel-copy（闲鱼+小红书文案）
  视频  → Gateway /v1/content/video/generate（MoneyPrinterTurbo）
  抖音  → nebula DouyinAutomation.publish（Playwright 自动化）
  短剧  → nebula shortdramas_submit（短剧预审）
  帮助  → 显示指令列表
  其他  → 返回 None，由调用方走 /v1/chat 闲聊

指令格式（直觉化，用户友好）：
  文案 商品=XX 卖点=XX 价格=XX 成色=XX
  视频 主题=XX
  抖音 标题=XX 内容=XX
  短剧 标题=XX 内容=XX
  帮助
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, Optional, Tuple

from mindflow_map.config import settings
from mindflow_map.api.feishu_sender import FeishuSender

logger = logging.getLogger(__name__)

# ── 指令前缀 → 处理器映射 ──
# 用前缀匹配，容忍用户输入"生成文案""做视频"等自然表达
_COMMAND_PREFIXES: Dict[str, Tuple[str, Any]] = {}


def _register(prefix: str):
    """注册指令前缀"""
    def deco(fn):
        _COMMAND_PREFIXES[prefix] = (prefix, fn)
        return fn
    return deco


def _parse_kv_args(text: str, after_prefix: str) -> Dict[str, str]:
    """解析 key=value 参数

    支持空格或逗号分隔，值可含空格（用引号或直到下一个 key=）
    示例：标题=hello world 内容=foo bar → {标题: "hello world", 内容: "foo bar"}
    """
    args: Dict[str, str] = {}
    # 匹配 key=value，value 可以含空格直到下一个 key= 或字符串末尾
    pattern = re.compile(r"(\S+?)=([^=]*?)(?=\s+\S+=|$)")
    for m in pattern.finditer(after_prefix):
        key = m.group(1).strip()
        val = m.group(2).strip().strip("'\"")
        if key:
            args[key] = val
    return args


async def route_command(text: str) -> Optional[str]:
    """路由指令，返回回复文本。返回 None 表示不是指令，应走闲聊。

    Args:
        text: 用户发送的原始文本

    Returns:
        回复文本，或 None（非指令）
    """
    stripped = text.strip()
    if not stripped:
        return None

    # 帮助指令（特殊处理，不解析参数）
    if stripped in ("帮助", "help", "?", "？", "指令"):
        return _help_text()

    # 按前缀匹配
    for prefix, (_p, fn) in _COMMAND_PREFIXES.items():
        if stripped.startswith(prefix):
            after = stripped[len(prefix):].strip()
            args = _parse_kv_args(stripped, after)
            try:
                return await fn(args, after)
            except Exception as e:
                logger.error("指令 %s 执行失败: %s", prefix, e, exc_info=True)
                return f"❌ 指令执行失败：{e}\n\n发送「帮助」查看指令列表。"

    return None  # 非指令，走闲聊


# ════════════════════════════════════════════════════════════════════
# 指令实现
# ════════════════════════════════════════════════════════════════════


@_register("文案")
async def _cmd_copy(args: Dict[str, str], after: str) -> str:
    """文案指令 — 生成闲鱼+小红书两套文案

    格式：文案 商品=XX 卖点=XX 价格=XX 成色=XX
    若无 key=value，则把 after 整体当作商品名
    """
    product = args.get("商品") or args.get("product") or after
    if not product:
        return "❌ 请提供商品名\n格式：文案 商品=北欧风香薰 卖点=大豆蜡留香8小时 价格=59 成色=全新"

    description = args.get("卖点") or args.get("description") or ""
    price = args.get("价格") or args.get("price") or ""
    condition = args.get("成色") or args.get("condition") or "全新未拆"

    client = FeishuSender._get_shared_client()
    ds_url = settings.ds_url.rstrip("/")

    # 同时请求闲鱼和小红书
    import asyncio
    tasks = [
        client.post(
            f"{ds_url}/api/ai/channel-copy",
            json={
                "platform": platform,
                "product": product,
                "description": description or None,
                "price": price or None,
                "condition": condition or None,
                "tone": "casual",
            },
        )
        for platform in ("xianyu", "xiaohongshu")
    ]
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    sections = []
    platform_names = {"xianyu": "🐟 闲鱼", "xiaohongshu": "📕 小红书"}

    for platform, resp in zip(("xianyu", "xiaohongshu"), responses):
        name = platform_names[platform]
        if isinstance(resp, Exception):
            sections.append(f"{name}\n❌ 生成失败：{resp}")
            continue
        try:
            data = resp.json()
            if not resp.is_success:
                sections.append(f"{name}\n❌ {data.get('error', '未知错误')}")
                continue
            r = data.get("result", {})
            title = r.get("title", "")
            body = r.get("body", "")
            tags = " ".join(r.get("tags", []))
            sections.append(f"{name}\n【标题】{title}\n【正文】\n{body}\n【标签】{tags}")
        except Exception as e:
            sections.append(f"{name}\n❌ 解析失败：{e}")

    return "\n\n──────────\n\n".join(sections)


@_register("视频")
async def _cmd_video(args: Dict[str, str], after: str) -> str:
    """视频指令 — 生成种草视频

    格式：视频 主题=XX
    """
    subject = args.get("主题") or args.get("subject") or after
    if not subject:
        return "❌ 请提供视频主题\n格式：视频 主题=北欧风香薰蜡烛种草"

    client = FeishuSender._get_shared_client()
    gateway_url = settings.gateway_url.rstrip("/")

    try:
        resp = await client.post(
            f"{gateway_url}/v1/content/video/generate",
            json={
                "video_subject": subject,
                "video_aspect": "9:16",  # 竖屏，适合抖音/小红书
                "video_language": "zh",
                "video_concat_mode": "random",
                "paragraph_number": 2,
                "n_threads": 2,
            },
            timeout=30,
        )
        data = resp.json()
        if not resp.is_success:
            err = data.get("error") or data.get("detail") or f"HTTP {resp.status_code}"
            return f"❌ 视频生成请求失败：{err}"

        # Gateway 包装：{success, data: {task_id, status}}
        task_id = (
            data.get("data", {}).get("task_id")
            if isinstance(data.get("data"), dict)
            else data.get("task_id")
        )
        if not task_id:
            return f"✅ 已提交，但未返回任务 ID\n返回：{json.dumps(data, ensure_ascii=False)[:200]}"

        return (
            f"✅ 视频生成已提交\n"
            f"主题：{subject}\n"
            f"任务 ID：{task_id}\n"
            f"比例：9:16（竖屏）\n\n"
            f"💡 5-10 分钟后发送：查询视频 {task_id}"
        )
    except Exception as e:
        return f"❌ 视频生成请求异常：{e}"


@_register("查询视频")
async def _cmd_video_status(args: Dict[str, str], after: str) -> str:
    """查询视频生成状态

    格式：查询视频 <task_id>
    """
    task_id = after.strip().split()[0] if after.strip() else ""
    if not task_id:
        return "❌ 请提供任务 ID\n格式：查询视频 abc123"

    client = FeishuSender._get_shared_client()
    gateway_url = settings.gateway_url.rstrip("/")

    try:
        resp = await client.get(
            f"{gateway_url}/v1/content/video/status/{task_id}",
            timeout=15,
        )
        data = resp.json()
        if not resp.is_success:
            return f"❌ 查询失败：{data.get('error', f'HTTP {resp.status_code}')}"

        task = data.get("data", {}) if isinstance(data.get("data"), dict) else data
        state = task.get("state", task.get("status", "unknown"))
        progress = task.get("progress", 0)

        # MoneyPrinterTurbo state: 0=pending, 1=success, 2=failed, 4=processing
        state_text = {
            0: "⏳ 排队中",
            1: "✅ 已完成",
            2: "❌ 失败",
            4: "🔄 生成中",
        }.get(state, str(state))

        msg = f"任务 {task_id}\n状态：{state_text}\n进度：{progress}%"

        # 如果完成，附上视频链接
        videos = task.get("videos", [])
        if state == 1 and videos:
            msg += f"\n\n视频链接：\n" + "\n".join(videos[:2])
            msg += "\n\n💡 可发送：发布视频 <task_id> 标题=XX 平台=tiktok"

        return msg
    except Exception as e:
        return f"❌ 查询异常：{e}"


@_register("发布视频")
async def _cmd_publish(args: Dict[str, str], after: str) -> str:
    """发布视频到 TikTok/YouTube/Instagram

    格式：发布视频 <task_id> 标题=XX 平台=tiktok
    """
    parts = after.strip().split(None, 1)
    if not parts or not parts[0]:
        return "❌ 请提供任务 ID\n格式：发布视频 abc123 标题=我的视频 平台=tiktok"

    task_id = parts[0]
    title = args.get("标题") or args.get("title") or "AI 生成视频"
    platforms_raw = args.get("平台") or args.get("platforms") or "tiktok"
    platforms = [p.strip() for p in platforms_raw.split(",") if p.strip()]

    client = FeishuSender._get_shared_client()
    gateway_url = settings.gateway_url.rstrip("/")

    try:
        resp = await client.post(
            f"{gateway_url}/v1/content/video/publish",
            json={
                "task_id": task_id,
                "title": title,
                "platforms": platforms,
            },
            timeout=300,  # 发布可能较慢
        )
        data = resp.json()
        if not resp.is_success:
            err = data.get("error") or data.get("detail") or f"HTTP {resp.status_code}"
            return f"❌ 发布失败：{err}"

        d = data.get("data", {}) if isinstance(data.get("data"), dict) else data
        if d.get("published"):
            req_id = d.get("request_id", "")
            return (
                f"✅ 发布已提交\n"
                f"任务：{task_id}\n"
                f"标题：{title}\n"
                f"平台：{', '.join(platforms)}\n"
                f"Request ID：{req_id}\n\n"
                f"💡 发布为异步处理，可在 Upload-Post 后台查看结果。"
            )
        return f"发布响应：{json.dumps(data, ensure_ascii=False)[:300]}"
    except Exception as e:
        return f"❌ 发布异常：{e}"


@_register("抖音")
async def _cmd_douyin(args: Dict[str, str], after: str) -> str:
    """抖音指令 — 发布图文到抖音创作者中心

    格式：抖音 标题=XX 内容=XX
    需要 nebula DouyinAutomation 已登录（cookie 注入）
    """
    title = args.get("标题") or args.get("title")
    content = args.get("内容") or args.get("content") or ""
    if not title:
        return "❌ 请提供标题\n格式：抖音 标题=我的短剧 内容=简介文字"

    # 延迟导入，避免未安装 playwright 时影响其他指令
    try:
        from mindflow_map.automation.douyin import DouyinAutomation
    except ImportError:
        return "❌ 抖音自动化未安装（需要 playwright）\n配置：pip install playwright && playwright install chromium"

    auto = DouyinAutomation()
    try:
        # 检查登录态
        if auto.state != "LOGGED_IN":
            return (
                "❌ 抖音未登录\n"
                "请先在 nebula 配置 DOUYIN_COOKIE_JSON 环境变量，\n"
                "或调用 DouyinAutomation.login() 完成登录。"
            )

        result = await auto.publish(title=title, content=content)
        if result.get("success"):
            return (
                f"✅ 抖音发布已提交\n"
                f"标题：{title}\n"
                f"URL：{result.get('url', '')}\n"
                f"{result.get('note', '')}"
            )
        return f"❌ 抖音发布失败：{result.get('error', '未知错误')}"
    finally:
        await auto.close()


@_register("短剧")
async def _cmd_shortdrama(args: Dict[str, str], after: str) -> str:
    """短剧指令 — 提交短剧内容预审

    格式：短剧 标题=XX 内容=XX
    """
    title = args.get("标题") or args.get("title")
    content = args.get("内容") or args.get("content") or ""
    if not title:
        return "❌ 请提供标题\n格式：短剧 标题=我的短剧 内容=剧情简介"

    # 延迟导入
    try:
        from mindflow_map.api.shortdramas import ShortDramasSubmitRequest, shortdramas_submit
    except ImportError:
        return "❌ 短剧模块未启用"

    try:
        req = ShortDramasSubmitRequest(title=title, content=content, content_type="video")
        result = await shortdramas_submit(req)
        if result.get("success"):
            demo = "（演示模式）" if result.get("demo") else ""
            return (
                f"✅ 短剧预审已提交{demo}\n"
                f"标题：{title}\n"
                f"Job ID：{result.get('job_id', '')}\n"
                f"状态：{result.get('status', 'pending')}\n\n"
                f"💡 发送：查询短剧 {result.get('job_id', '')} 查看进度"
            )
        return f"❌ 提交失败：{result}"
    except Exception as e:
        return f"❌ 短剧提交异常：{e}"


@_register("查询短剧")
async def _cmd_shortdrama_query(args: Dict[str, str], after: str) -> str:
    """查询短剧预审状态

    格式：查询短剧 <job_id>
    """
    job_id = after.strip().split()[0] if after.strip() else ""
    if not job_id:
        return "❌ 请提供 Job ID\n格式：查询短剧 abc123"

    try:
        from mindflow_map.api.shortdramas import ShortDramasQueryRequest, shortdramas_query
    except ImportError:
        return "❌ 短剧模块未启用"

    try:
        req = ShortDramasQueryRequest(job_id=job_id)
        result = await shortdramas_query(req)
        if result.get("success"):
            demo = "（演示模式）" if result.get("demo") else ""
            return f"短剧预审{demo}\nJob ID：{job_id}\n状态：{result.get('status', 'unknown')}"
        return f"❌ 查询失败：{result}"
    except Exception as e:
        return f"❌ 查询异常：{e}"


# ════════════════════════════════════════════════════════════════════
# 帮助文本
# ════════════════════════════════════════════════════════════════════


def _help_text() -> str:
    return """🎬 Ghost 渠道助手 · 飞书指令

【内容生成】
文案 商品=XX 卖点=XX 价格=XX 成色=XX
  → 生成闲鱼+小红书两套文案

视频 主题=XX
  → 生成竖屏种草视频

查询视频 <任务ID>
  → 查询视频生成进度

发布视频 <任务ID> 标题=XX 平台=tiktok
  → 发布到 TikTok/YouTube/Instagram

【渠道发布】
抖音 标题=XX 内容=XX
  → 发布到抖音创作者中心（需先登录）

短剧 标题=XX 内容=XX
  → 提交短剧内容预审

查询短剧 <JobID>
  → 查询短剧预审状态

【其他】
帮助 / ?
  → 显示本帮助

💡 不带指令前缀的消息会进入 AI 闲聊
💡 国内闭环：小红书种草 → 闲鱼成交
💡 出海闭环：视频生成 → TikTok/YouTube 发布
"""


# 注册顺序说明：
# 各指令前缀首字不同（文/视/查/发/抖/短），不会互相冲突，注册顺序无关紧要。
