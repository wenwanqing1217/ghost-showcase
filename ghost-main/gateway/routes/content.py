"""Content Generation Routes — /v1/content/*
============================================
Proxies AI content generation requests to MoneyPrinterTurbo (video) and
GameEngine service (game).

All requests here require tenant authentication (enforced by TenantMiddleware).

Routes:
  POST   /v1/content/video/generate   → MoneyPrinterTurbo POST /api/v1/videos
  GET    /v1/content/video/status/{task_id} → MoneyPrinterTurbo GET /api/v1/tasks/{task_id}
  GET    /v1/content/video/list      → MoneyPrinterTurbo GET /api/v1/tasks
  POST   /v1/content/game/generate   → GameEngine (template-based HTML5 games)
  GET    /v1/content/game/status/{task_id} → GameEngine status check
  GET    /v1/content/game/list       → GameEngine list recent games
"""

import logging
from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

import config
from middleware.rate_limit import client_ip, rate_limit_check
from services.game_engine import generate_game, get_game_status, list_generated_games
from services.proxy import fail, has_error, ok, proxy_get, proxy_post

logger = logging.getLogger("ghost-gateway")

# MoneyPrinterTurbo backend URL
MP_URL = config.MONEYPRINTER_URL

router = APIRouter(prefix="/v1/content", tags=["content"])


# ── Request Models ─────────────────────────────────────────────────────────


class VideoGenerateRequest(BaseModel):
    """Request body for video generation."""
    video_subject: str
    video_language: Optional[str] = "zh"
    video_aspect: Optional[str] = "9:16"
    video_concat_mode: Optional[str] = "random"
    paragraph_number: Optional[int] = 1
    n_threads: Optional[int] = 2
    # Optional: pass pre-uploaded local materials
    video_source: Optional[str] = "local"
    video_materials: Optional[list[dict]] = None


class GameGenerateRequest(BaseModel):
    """Request body for game generation (Phase 2 placeholder)."""
    game_type: str  # e.g. "space_shooter", "platformer"
    theme: str      # e.g. "cyberpunk", "japanese_anime"
    description: Optional[str] = ""


# ── Video Generation ───────────────────────────────────────────────────────


@router.post("/video/generate")
async def generate_video(request: Request, body: VideoGenerateRequest):
    """Trigger AI video generation via MoneyPrinterTurbo.

    Body:
      - video_subject: topic/subject of the video (required)
      - video_language: language code, e.g. "zh", "en" (default: "zh")
      - video_aspect: "9:16" (portrait), "16:9" (landscape), "1:1" (square)
      - video_concat_mode: "random" or "sequential"
      - paragraph_number: number of script paragraphs (1-10)
      - n_threads: processing threads
      - video_source: "local" or "pexels" etc.
      - video_materials: list of {provider, url} for local source

    Returns: {task_id, status, progress}
    """
    ip = client_ip(request)
    if not rate_limit_check(f"content:video:{ip}", max_requests=3, window=120):
        return fail("Video generation rate limit exceeded, please wait 2 minutes", 429, request)

    tenant_id = getattr(request.state, "tenant_id", "anonymous")

    # Forward tenant info as headers for tracking
    headers = {
        "X-Tenant-ID": tenant_id,
        "X-Request-ID": getattr(request.state, "request_id", ""),
    }

    # Convert to MoneyPrinterTurbo API format
    mp_body = body.model_dump(exclude_none=True)

    data = await proxy_post(
        "/api/v1/videos",
        MP_URL,
        body=mp_body,
        headers=headers,
        timeout=30,
    )

    if has_error(data):
        return fail(f"MoneyPrinterTurbo error: {data.get('_error', 'unknown')}", 502, request)

    # Normalize response: wrap task_id in Ghost envelope
    task_id = data.get("data", {}).get("task_id") if isinstance(data.get("data"), dict) else data.get("task_id")
    return ok({
        "task_id": task_id,
        "status": "queued",
        "backend": "moneyprinter",
    }, request)


@router.get("/video/status/{task_id}")
async def get_video_status(task_id: str, request: Request):
    """Poll video generation task status.

    Returns full task data including:
      - state: 0=pending, 1=success, 2=failed
      - progress: 0-100
      - videos: list of generated video paths
      - script, terms, audio_file, subtitle_path
      - error: error message if failed
    """
    ip = client_ip(request)
    if not rate_limit_check(f"content:video:status:{ip}", max_requests=30, window=60):
        return fail("Too many requests, please slow down", 429, request)

    tenant_id = getattr(request.state, "tenant_id", "anonymous")
    headers = {
        "X-Tenant-ID": tenant_id,
        "X-Request-ID": getattr(request.state, "request_id", ""),
    }

    data = await proxy_get(
        f"/api/v1/tasks/{task_id}",
        MP_URL,
        headers=headers,
        timeout=15,
    )

    if has_error(data):
        return fail(f"MoneyPrinterTurbo error: {data.get('_error', 'unknown')}", 502, request)

    # MoneyPrinterTurbo wraps task data in {"status":200,"message":"success","data":{...}}
    # We need to normalize video URLs inside the nested data
    mp_task_data = None
    if isinstance(data, dict):
        if "data" in data and isinstance(data["data"], dict):
            # This is the MoneyPrinterTurbo wrapper — dig into inner data
            mp_task_data = data["data"].get("data", data["data"])
        else:
            mp_task_data = data

    # ── Recovery: MoneyPrinterTurbo sometimes gets stuck at state=4, progress=75%
    # even though the final video has been written. Detect this by probing the
    # download endpoint for the expected final-1.mp4 file.
    if (
        isinstance(mp_task_data, dict)
        and mp_task_data.get("state") == 4
        and mp_task_data.get("progress", 0) >= 75
    ):
        expected_path = f"/api/v1/download/{task_id}/final-1.mp4"
        try:
            import httpx
            async with httpx.AsyncClient(timeout=8) as probe_client:
                probe_resp = await probe_client.get(
                    f"{MP_URL.rstrip('/')}{expected_path}",
                    headers=headers,
                    follow_redirects=True,
                )
            if probe_resp.status_code == 200:
                # File is accessible — override to completed
                mp_task_data["state"] = 1
                mp_task_data["progress"] = 100
                mp_public_base = config.MONEYPRINTER_PUBLIC_URL.rstrip("/")
                mp_task_data["videos"] = [f"{mp_public_base}/tasks/{task_id}/final-1.mp4"]
                mp_task_data.setdefault("combined_videos", [])
        except Exception:
            pass  # Leave state as-is if probe fails

    # Normalize relative video paths to public URLs
    if isinstance(mp_task_data, dict) and mp_task_data.get("videos"):
        public_videos = []
        for v in mp_task_data["videos"]:
            if isinstance(v, str) and v.startswith("/tasks/"):
                # Use public-facing URL for clients (Feishu, browser)
                mp_public_base = config.MONEYPRINTER_PUBLIC_URL.rstrip("/")
                public_videos.append(f"{mp_public_base}{v}")
            else:
                public_videos.append(v)
        mp_task_data["videos"] = public_videos

        # Also normalize combined_videos if present
        if mp_task_data.get("combined_videos"):
            public_combined = []
            for v in mp_task_data["combined_videos"]:
                if isinstance(v, str) and v.startswith("/tasks/"):
                    mp_public_base = config.MONEYPRINTER_PUBLIC_URL.rstrip("/")
                    public_combined.append(f"{mp_public_base}{v}")
                else:
                    public_combined.append(v)
            mp_task_data["combined_videos"] = public_combined

    # Return the inner task data directly (unwrapped from MoneyPrinterTurbo envelope)
    return ok(mp_task_data, request)


@router.get("/video/list")
async def list_videos(request: Request):
    """List all video generation tasks.

    Query params: ?page=1&limit=20
    """
    ip = client_ip(request)
    if not rate_limit_check(f"content:video:list:{ip}", max_requests=10, window=60):
        return fail("Too many requests, please slow down", 429, request)

    tenant_id = getattr(request.state, "tenant_id", "anonymous")
    headers = {
        "X-Tenant-ID": tenant_id,
        "X-Request-ID": getattr(request.state, "request_id", ""),
    }

    # Forward query params
    query_string = str(request.url.query)
    path = f"/api/v1/tasks{('?' + query_string) if query_string else ''}"

    data = await proxy_get(path, MP_URL, headers=headers, timeout=15)

    if has_error(data):
        return fail(f"MoneyPrinterTurbo error: {data.get('_error', 'unknown')}", 502, request)

    return ok(data, request)


# ── Video Publishing (跨平台发布：TikTok / Instagram / YouTube) ───────────


class VideoPublishRequest(BaseModel):
    """Request body for cross-platform video publishing."""
    task_id: str
    title: str
    platforms: list[str] = ["tiktok"]  # tiktok / instagram / youtube
    youtube_description: Optional[str] = None
    youtube_tags: Optional[list[str]] = None
    youtube_privacy_status: Optional[str] = "public"  # public / unlisted / private


@router.post("/video/publish")
async def publish_video(request: Request, body: VideoPublishRequest):
    """将已生成的视频发布到 TikTok / Instagram / YouTube。

    流程：
    1. 从 MoneyPrinterTurbo 查询 task 状态，获取视频 URL
    2. 下载视频到内存
    3. 通过 Upload-Post API 跨平台发布

    需要 Gateway 配置 UPLOAD_POST_API_KEY + UPLOAD_POST_USERNAME。
    """

    import httpx

    # ── 1. 检查 Upload-Post 配置 ──
    if not config.UPLOAD_POST_API_KEY or not config.UPLOAD_POST_USERNAME:
        return fail(
            "Upload-Post 未配置。请在 Gateway 设置 UPLOAD_POST_API_KEY 和 UPLOAD_POST_USERNAME 环境变量（在 upload-post.com 注册获取）。",
            503,
            request,
        )

    ip = client_ip(request)
    if not rate_limit_check(f"content:publish:{ip}", max_requests=2, window=300):
        return fail("发布频率限制：每 5 分钟最多 2 次，请稍后再试", 429, request)

    tenant_id = getattr(request.state, "tenant_id", "anonymous")
    headers = {
        "X-Tenant-ID": tenant_id,
        "X-Request-ID": getattr(request.state, "request_id", ""),
    }

    # ── 2. 从 MoneyPrinterTurbo 获取视频 URL ──
    task_data = await proxy_get(
        f"/api/v1/tasks/{body.task_id}",
        MP_URL,
        headers=headers,
        timeout=15,
    )

    if has_error(task_data):
        return fail(f"查询视频任务失败: {task_data.get('_error', 'unknown')}", 502, request)

    # 解析 MoneyPrinterTurbo 嵌套结构 {status, data: {data: {...}}}
    mp_task = task_data
    if isinstance(mp_task, dict) and "data" in mp_task:
        inner = mp_task["data"]
        if isinstance(inner, dict) and "data" in inner:
            mp_task = inner["data"]
        else:
            mp_task = inner

    # 检查任务是否完成
    state = mp_task.get("state", 0)
    if state != 1:
        return fail(f"视频尚未生成完成（当前状态: {state}），请等待生成完成后再发布", 400, request)

    videos = mp_task.get("videos", [])
    combined_videos = mp_task.get("combined_videos", [])

    # 优先使用 combined_videos（合并版），否则用 videos[0]
    video_urls = combined_videos if combined_videos else videos
    if not video_urls:
        return fail("视频任务完成但未找到视频文件", 404, request)

    # 获取第一个视频 URL
    video_url = video_urls[0] if isinstance(video_urls[0], str) else str(video_urls[0])

    # 如果是相对路径，拼接 MoneyPrinterTurbo 公开 URL
    if video_url.startswith("/tasks/"):
        video_url = f"{config.MONEYPRINTER_PUBLIC_URL.rstrip('/')}{video_url}"

    logger.info(f"Publishing video task={body.task_id} url={video_url} platforms={body.platforms}")

    # ── 3. 下载视频到临时文件 ──
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            video_resp = await client.get(video_url, headers=headers, follow_redirects=True)
            if video_resp.status_code != 200:
                return fail(f"下载视频失败: HTTP {video_resp.status_code}", 502, request)

            video_bytes = video_resp.content

        if len(video_bytes) < 1000:
            return fail("下载的视频文件过小，可能无效", 502, request)

    except Exception as e:
        logger.error(f"下载视频失败: {e}")
        return fail(f"下载视频异常: {e!s}", 502, request)

    # ── 4. 调用 Upload-Post API 发布 ──
    try:
        # 准备 multipart form data
        files = {"video": (f"{body.task_id}.mp4", video_bytes, "video/mp4")}
        data = [
            ("user", config.UPLOAD_POST_USERNAME),
            ("title", body.title[:2200]),
            ("privacy_level", "PUBLIC_TO_EVERYONE"),
        ]
        for platform in body.platforms:
            data.append(("platform[]", platform))

        # YouTube 额外参数
        if "youtube" in body.platforms:
            if body.youtube_description:
                data.append(("youtube_description", body.youtube_description))
            if body.youtube_tags:
                for tag in body.youtube_tags:
                    data.append(("tags[]", tag))
            data.append(("privacyStatus", body.youtube_privacy_status or "public"))
            data.append(("containsSyntheticMedia", "true"))

        upload_headers = {"Authorization": f"Apikey {config.UPLOAD_POST_API_KEY}"}

        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(
                f"{config.UPLOAD_POST_API_BASE}/api/upload",
                headers=upload_headers,
                data=data,
                files=files,
            )

        if resp.status_code != 200:
            error_text = resp.text[:500]
            logger.error(f"Upload-Post API 返回 {resp.status_code}: {error_text}")
            return fail(f"发布失败: Upload-Post API 返回 {resp.status_code}", 502, request)

        result = resp.json()

        if result.get("success"):
            return ok({
                "published": True,
                "request_id": result.get("request_id"),
                "platforms": body.platforms,
                "title": body.title,
                "video_url": video_url,
            }, request)
        else:
            return fail(f"发布失败: {result.get('message', '未知错误')}", 502, request)

    except Exception as e:
        logger.error(f"Upload-Post API 调用异常: {e}")
        return fail(f"发布异常: {e!s}", 500, request)


@router.get("/video/publish/status/{request_id}")
async def get_publish_status(request_id: str, request: Request):
    """查询发布状态。"""
    import httpx

    if not config.UPLOAD_POST_API_KEY:
        return fail("Upload-Post 未配置", 503, request)

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{config.UPLOAD_POST_API_BASE}/api/uploadposts/status",
                params={"request_id": request_id},
                headers={"Authorization": f"Apikey {config.UPLOAD_POST_API_KEY}"},
            )

        if resp.status_code != 200:
            return fail(f"查询失败: HTTP {resp.status_code}", 502, request)

        return ok(resp.json(), request)
    except Exception as e:
        return fail(f"查询异常: {e!s}", 500, request)


# ── Game Generation (Phase 2 Placeholder) ──────────────────────────────────


@router.post("/game/generate")
async def generate_game_route(request: Request, body: GameGenerateRequest):
    """Trigger AI game generation via GameEngine service.

    Generates a playable HTML5 game based on the requested type and theme.
    Games are stored as standalone HTML files and served at a public URL.

    Body:
      - game_type: type of game (e.g. "space_shooter", "platformer", "puzzle", "racing", "rpg")
      - theme: visual theme (e.g. "cyberpunk", "japanese_anime", "pixel_art", "low_poly", "realistic")
      - description: optional detailed description for game customization

    Returns: {game_id, game_type, theme, game_url, status}
    """
    ip = client_ip(request)
    if not rate_limit_check(f"content:game:{ip}", max_requests=5, window=120):
        return fail("Game generation rate limit exceeded, please wait 2 minutes", 429, request)

    tenant_id = getattr(request.state, "tenant_id", "anonymous")
    logger.info(f"Game generation request: type={body.game_type}, theme={body.theme}, tenant={tenant_id}")

    try:
        result = await generate_game(
            game_type=body.game_type,
            theme=body.theme,
            description=body.description or "",
        )
        # Add tenant tracking
        result["tenant_id"] = tenant_id
        return ok(result, request)
    except ValueError as e:
        return fail(str(e), 400, request)
    except RuntimeError as e:
        return fail(str(e), 500, request)
    except Exception as e:
        logger.error(f"Game generation failed: {e}", exc_info=True)
        return fail(f"Game generation failed: {e!s}", 500, request)


@router.get("/game/status/{task_id}")
async def get_game_status_route(task_id: str, request: Request):
    """Poll game generation task status.

    Since game generation is synchronous (template-based), the status
    will typically return 'completed' with the game URL.
    """
    ip = client_ip(request)
    if not rate_limit_check(f"content:game:status:{ip}", max_requests=30, window=60):
        return fail("Too many requests, please slow down", 429, request)

    try:
        result = get_game_status(task_id)
        return ok(result, request)
    except Exception as e:
        logger.error(f"Game status check failed: {e}")
        return fail(f"Status check failed: {e!s}", 500, request)


@router.get("/game/list")
async def list_games(request: Request):
    """List recently generated games.

    Query params: ?limit=50
    """
    ip = client_ip(request)
    if not rate_limit_check(f"content:game:list:{ip}", max_requests=10, window=60):
        return fail("Too many requests, please slow down", 429, request)

    try:
        limit = int(request.query_params.get("limit", 50))
        games = list_generated_games(limit=min(limit, 100))
        return ok({"games": games, "total": len(games)}, request)
    except Exception as e:
        logger.error(f"Game list failed: {e}")
        return fail(f"List failed: {e!s}", 500, request)
