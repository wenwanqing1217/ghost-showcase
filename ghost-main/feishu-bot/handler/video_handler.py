"""视频生成处理 — /video 命令 + 任务轮询"""

import asyncio
import logging
import os
import uuid

import httpx

from auth.token_manager import TokenManager

logger = logging.getLogger("feishu-bot")


async def handle_video_command(handler, text: str, chat_id: str, msg_id: str) -> None:
    """Handle /video command — trigger AI video generation via Gateway.

    Usage:
      /video <topic>           — generate video about a topic
      /video <topic> 9:16      — portrait mode (default)
      /video <topic> 16:9      — landscape mode
      /video <topic> 1:1       — square mode
    """
    parts = text.strip().split(maxsplit=2)
    if len(parts) < 2:
        await handler._reply_text(chat_id, msg_id,
            "用法: /video <主题> [比例]\n"
            "示例: /video 深海探索\n"
            "  /video 赛博朋克城市 16:9\n"
            "  /video 日本樱花 9:16\n"
            "支持的参数:\n"
            "  比例: 9:16（竖屏，默认）, 16:9（横屏）, 1:1（方形）\n"
            "  语言: zh（中文，默认）, en（英文）\n"
            "  拼接: random（随机，默认）, sequential（顺序）"
        )
        return

    topic = parts[1].strip()
    aspect = "9:16"
    language = "zh"
    concat_mode = "random"

    if len(parts) >= 3:
        extra = parts[2].strip()
        if ":" in extra:
            aspect = extra
        elif extra in ("zh", "en"):
            language = extra
        elif extra in ("random", "sequential"):
            concat_mode = extra

    if len(topic) > 200:
        await handler._reply_text(chat_id, msg_id, "❌ 主题过长，请控制在 200 字以内")
        return

    from config import GATEWAY_URL
    gateway_url = GATEWAY_URL
    tenant_id = getattr(handler._app, "tenant_id", "feishu-bot") if handler._app else "feishu-bot"

    # Step 1: Trigger video generation
    await handler._reply_text(chat_id, msg_id, f"🎬 正在生成视频「{topic[:50]}」...\n⏳ 预计需要 2-5 分钟，请稍候")

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{gateway_url}/v1/content/video/generate",
                headers={
                    "Content-Type": "application/json",
                    "X-Tenant-ID": tenant_id,
                    "X-Request-ID": str(uuid.uuid4()),
                },
                json={
                    "video_subject": topic,
                    "video_language": language,
                    "video_aspect": aspect,
                    "video_concat_mode": concat_mode,
                    "paragraph_number": 1,
                    "n_threads": 2,
                    "video_source": "local",
                },
            )
            data = resp.json()

        if not data.get("success"):
            error_msg = data.get("error", "unknown error")
            await handler._reply_text(chat_id, msg_id, f"❌ 视频生成请求失败: {error_msg}")
            return

        task_id = data.get("data", {}).get("task_id")
        if not task_id:
            await handler._reply_text(chat_id, msg_id, "❌ 未获取到任务 ID，请稍后重试")
            return

        # Step 2: Poll for completion
        await _poll_video_task(handler, task_id, chat_id, msg_id, gateway_url, tenant_id)

    except Exception as e:
        logger.exception("Video generation error")
        await handler._reply_text(chat_id, msg_id, f"❌ 视频生成出错: {str(e)[:200]}")


async def _poll_video_task(handler, task_id: str, chat_id: str, msg_id: str,
                           gateway_url: str, tenant_id: str):
    """Poll video generation task and send video card when ready."""
    max_polls = 60  # 60 polls * 10s = 10 minutes max
    poll_interval = 10

    for i in range(max_polls):
        try:
            await asyncio.sleep(poll_interval)
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{gateway_url}/v1/content/video/status/{task_id}",
                    headers={
                        "X-Tenant-ID": tenant_id,
                        "X-Request-ID": str(uuid.uuid4()),
                    },
                )
                data = resp.json()

            if not data.get("success"):
                await handler._reply_text(chat_id, msg_id, f"❌ 查询任务状态失败: {data.get('error', 'unknown')}")
                return

            task_data = data.get("data", {})
            # Handle nested response from proxy
            if isinstance(task_data, dict) and "data" in task_data:
                task_data = task_data["data"]

            state = task_data.get("state", -1)
            progress = task_data.get("progress", 0)
            error = task_data.get("error")
            failed_stage = task_data.get("failed_stage")

            logger.info(f"Video task {task_id}: state={state}, progress={progress}")

            # State: 0=pending, 1=success, 2=failed, 4=processing
            if state == 1:
                # Success! Send video card
                videos = task_data.get("videos", [])
                if videos:
                    video_url = videos[0]
                    if video_url.startswith("/"):
                        gw_host = gateway_url.replace("http://", "").replace("https://", "")
                        video_url = f"{gw_host}{video_url}"
                    script = task_data.get("script", "")
                    description = script[:200] + "..." if len(script) > 200 else script

                    from feishu_service import get_feishu_service
                    card = get_feishu_service()._build_video_card(
                        title=task_data.get("video_subject") or (script[:50] + ("..." if len(script) > 50 else "")) or "生成的视频",
                        video_url=video_url,
                        description=f"📝 {description}\n\n✅ 生成完成",
                    )
                    await handler._reply_card(chat_id, msg_id, card)
                else:
                    await handler._reply_text(chat_id, msg_id,
                        f"✅ 视频生成完成，但未获取到视频链接\n"
                        f"任务 ID: {task_id}\n"
                        f"请稍后在平台查看")
                return

            elif state == 2 or error:
                error_detail = error or failed_stage or "unknown error"
                await handler._reply_text(chat_id, msg_id,
                    f"❌ 视频生成失败\n"
                    f"错误: {error_detail}\n"
                    f"任务 ID: {task_id}")
                return

            # Still processing — send progress update every 6 polls
            if i > 0 and i % 6 == 0 and progress > 0:
                await handler._reply_text(chat_id, msg_id,
                    f"⏳ 视频生成中... {progress}%")

        except Exception as e:
            logger.warning(f"Poll error for task {task_id}: {e}")

    # Timeout
    await handler._reply_text(chat_id, msg_id,
        f"⏰ 视频生成超时（10分钟）\n"
        f"任务 ID: {task_id}\n"
        f"请稍后在平台查看或重新生成")
