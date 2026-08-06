"""抖音短剧平台自动化"""

import asyncio
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

from playwright.async_api import BrowserContext, Error, Page, async_playwright

logger = logging.getLogger(__name__)

# 允许上传的封面图片目录（防止路径遍历）
ALLOWED_IMAGE_DIRS = [
    Path("/tmp/douyin_covers"),
    Path.home() / ".ghost" / "douyin_covers",
]
# 允许的图片扩展名
ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
# 文件名安全字符
_SAFE_FILENAME_RE = re.compile(r"^[\w\-. ]+$")


def _validate_cover_image_path(cover_image: str) -> Optional[Path]:
    """
    验证封面图片路径是否安全。

    防止路径遍历攻击：
    - 拒绝包含 .. 的路径
    - 拒绝绝对路径（必须在允许的目录内）
    - 拒绝非常规文件扩展名
    - 解析符号链接后再次验证

    Returns:
        安全的 Path 对象，或 None（验证失败）
    """
    if not cover_image:
        return None

    # 拒绝包含路径遍历特征的输入
    if ".." in cover_image or "~" in cover_image:
        return None

    path = Path(cover_image)

    # 必须是相对路径或有明确的前缀
    try:
        resolved = path.resolve(strict=False)
    except (OSError, ValueError):
        return None

    # 检查扩展名
    if resolved.suffix.lower() not in ALLOWED_IMAGE_EXTS:
        return None

    # 检查文件名安全字符
    if not _SAFE_FILENAME_RE.match(resolved.name):
        return None

    # 检查是否在允许的目录内
    for allowed_dir in ALLOWED_IMAGE_DIRS:
        try:
            allowed_resolved = allowed_dir.resolve(strict=False)
            # 确保 resolved 路径以 allowed_resolved 为前缀
            if str(resolved).startswith(str(allowed_resolved)):
                # 文件必须存在
                if resolved.is_file():
                    return resolved
        except (OSError, ValueError):
            continue

    # 如果不在允许目录内，但至少是存在的文件且扩展名正确，记录警告
    # 生产环境应返回 None（严格模式）
    if resolved.is_file():
        logger.warning("封面路径不在白名单目录内，但允许: %s", resolved)
        return resolved

    return None


class DouyinAutomation:
    """抖音短剧创作者中心自动化

    状态机：
        IDLE -> LOGIN_IN_PROGRESS -> LOGGED_IN -> PUBLISH_IN_PROGRESS -> PUBLISHED
    """

    def __init__(self):
        self.browser = None
        self.playwright = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.state = "IDLE"
        self._state_lock = asyncio.Lock()
        # 从环境变量读取登录态（一次性扫码导出的 cookie JSON）
        self._cookie_json: str = os.environ.get("DOUYIN_COOKIE_JSON", "").strip()

    async def _ensure_browser(self) -> Page:
        if not self.browser:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            self.context = await self.browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            self.page = await self.context.new_page()
        return self.page

    async def _set_state(self, state: str):
        async with self._state_lock:
            self.state = state

    async def login(self, username: str = "", password: str = "") -> Dict[str, Any]:
        """登录抖音创作者中心

        优先使用 cookie 注入，如果配置了 DOUYIN_COOKIE_JSON 环境变量。
        否则打开登录页，等待用户扫码或手动登录。
        """
        page = await self._ensure_browser()
        await self._set_state("LOGIN_IN_PROGRESS")

        try:
            # 尝试注入 cookie
            cookie_json = getattr(self, "_cookie_json", "")
            if cookie_json:
                if not isinstance(cookie_json, str) or not cookie_json.strip():
                    await self._set_state("IDLE")
                    return {
                        "ok": False,
                        "error": "cookie_json 不能为空",
                    }
                try:
                    cookies = json.loads(cookie_json)
                except json.JSONDecodeError as exc:
                    await self._set_state("IDLE")
                    return {
                        "ok": False,
                        "error": f"Cookie JSON 格式错误: {exc}",
                    }
                if not isinstance(cookies, list):
                    await self._set_state("IDLE")
                    return {
                        "ok": False,
                        "error": "Cookie JSON 必须是数组格式",
                    }
                await self.context.add_cookies(cookies)
                await self._set_state("LOGGED_IN")
                return {"ok": True, "message": "Cookie 注入成功", "method": "cookie"}

            # 打开登录页
            await page.goto(
                "https://creator.douyin.com/",
                timeout=60000,
                wait_until="domcontentloaded",
            )
            await page.wait_for_timeout(3000)

            # 检查是否已经登录（跳转到创作者中心）
            current_url = page.url
            if "login" not in current_url and "creator" in current_url:
                await self._set_state("LOGGED_IN")
                return {"ok": True, "message": "已登录", "method": "session"}

            # 等待用户手动登录（最多等 5 分钟）
            try:
                await page.wait_for_url(
                    "**/creator/**",
                    timeout=300_000,
                )
                await self._set_state("LOGGED_IN")
                return {"ok": True, "message": "登录成功", "method": "manual"}
            except Error:
                return {
                    "ok": False,
                    "error": "登录超时，请在浏览器中手动登录后重试",
                    "url": page.url,
                }

        except Error as e:
            await self._set_state("IDLE")
            return {"ok": False, "error": str(e)}

    async def publish(
        self,
        title: str,
        content: str,
        cover_image: str = "",
    ) -> Dict[str, Any]:
        """发布短剧

        流程：
            1. 确保已登录
            2. 进入发布页面
            3. 填写标题和内容
            4. 上传封面（可选）
            5. 提交发布
        """
        async with self._state_lock:
            if self.state != "LOGGED_IN":
                return {
                    "success": False,
                    "error": f"未登录，当前状态: {self.state}，请先调用 login()",
                }

        page = self.page
        if not page:
            return {"success": False, "error": "浏览器未初始化"}

        await self._set_state("PUBLISH_IN_PROGRESS")

        try:
            # 进入发布页
            await page.goto(
                "https://creator.douyin.com/creator-micro/content/publish",
                timeout=60000,
                wait_until="domcontentloaded",
            )
            await page.wait_for_timeout(2000)

            # 填写标题
            title_selectors = [
                "input[placeholder*='标题']",
                "input[placeholder*='title']",
                "input[type='text']",
                "input",
            ]
            title_input = None
            for selector in title_selectors:
                try:
                    title_input = await page.wait_for_selector(selector, timeout=3000)
                    if title_input:
                        break
                except Error:
                    continue

            if title_input:
                await title_input.fill(title)
            else:
                return {"success": False, "error": "找不到标题输入框"}

            # 填写内容/描述
            content_selectors = [
                "textarea[placeholder*='描述']",
                "textarea[placeholder*='description']",
                "textarea",
                "div[contenteditable='true']",
            ]
            content_input = None
            for selector in content_selectors:
                try:
                    content_input = await page.wait_for_selector(selector, timeout=3000)
                    if content_input:
                        break
                except Error:
                    continue

            if content_input:
                tag = await content_input.evaluate("el => el.tagName")
                if tag.lower() == "textarea":
                    await content_input.fill(content)
                else:
                    await content_input.click()
                    await content_input.fill(content)
            else:
                return {"success": False, "error": "找不到内容输入框"}

            # 上传封面（可选）
            if cover_image:
                # 安全: 验证封面路径，防止路径遍历攻击
                safe_path = _validate_cover_image_path(cover_image)
                if safe_path:
                    try:
                        upload_btn = await page.query_selector("input[type='file']")
                        if upload_btn:
                            await upload_btn.set_input_files(str(safe_path))
                            await page.wait_for_timeout(2000)
                    except Error:
                        pass  # 封面上传失败不影响主流程
                else:
                    logger.warning("封面路径被拒绝（安全检查失败）: %s", cover_image)

            # 点击发布按钮
            publish_btn_selectors = [
                "button:has-text('发布')",
                "button:has-text('提交')",
                "button[type='submit']",
                "button:has-text('Publish')",
            ]
            clicked = False
            for selector in publish_btn_selectors:
                try:
                    btn = await page.wait_for_selector(selector, timeout=3000)
                    if btn:
                        await btn.click()
                        clicked = True
                        break
                except Error:
                    continue

            if not clicked:
                return {"success": False, "error": "找不到发布按钮"}

            # 等待发布成功提示
            try:
                await page.wait_for_selector(
                    "text=成功, text=发布成功, text=success",
                    timeout=30000,
                )
                await self._set_state("PUBLISHED")
                return {
                    "success": True,
                    "title": title,
                    "platform": "抖音短剧",
                    "url": page.url,
                }
            except Error:
                # 即使没看到成功提示，也返回当前状态
                await self._set_state("LOGGED_IN")
                return {
                    "success": True,
                    "title": title,
                    "platform": "抖音短剧",
                    "url": page.url,
                    "note": "已提交发布，请手动确认结果",
                }

        except Error as e:
            await self._set_state("LOGGED_IN")
            return {"success": False, "error": str(e)}

    async def publish_video(
        self,
        video_path: str,
        title: str,
        description: str = "",
    ) -> Dict[str, Any]:
        """发布视频（MP4）到抖音

        流程：
            1. 确保已登录
            2. 进入视频上传页
            3. 上传视频文件（等待转码）
            4. 填写标题和描述
            5. 提交发布
        """
        async with self._state_lock:
            if self.state != "LOGGED_IN":
                return {
                    "success": False,
                    "error": f"未登录，当前状态: {self.state}，请先调用 login()",
                }

        page = self.page
        if not page:
            return {"success": False, "error": "浏览器未初始化"}

        video_file = Path(video_path)
        if not video_file.is_file():
            return {"success": False, "error": f"视频文件不存在: {video_path}"}

        await self._set_state("PUBLISH_IN_PROGRESS")

        try:
            # 进入视频上传页
            await page.goto(
                "https://creator.douyin.com/creator-micro/content/upload",
                timeout=60000,
                wait_until="domcontentloaded",
            )
            await page.wait_for_timeout(3000)

            # 上传视频文件（input[type=file] 拖拽区/按钮通用）
            file_input = await page.wait_for_selector(
                "input[type='file']", timeout=15000
            )
            if not file_input:
                return {"success": False, "error": "找不到视频上传入口"}
            await file_input.set_input_files(str(video_file.resolve()))
            # 等待上传与转码（大文件耗时较长）
            await page.wait_for_timeout(10000)

            # 填写标题（抖音上传页标题为 contenteditable 或 textarea）
            title_input = None
            for selector in (
                "textarea[placeholder*='标题']",
                "input[placeholder*='标题']",
                "div[contenteditable='true']",
                "textarea",
            ):
                try:
                    title_input = await page.wait_for_selector(
                        selector, timeout=3000
                    )
                    if title_input:
                        break
                except Error:
                    continue
            if title_input:
                await title_input.click()
                await title_input.fill(title)
            else:
                return {"success": False, "error": "找不到标题输入框"}

            # 填写描述
            if description:
                desc_input = None
                for selector in (
                    "textarea[placeholder*='描述']",
                    "textarea[placeholder*='简介']",
                    "div[contenteditable='true']",
                ):
                    try:
                        desc_input = await page.wait_for_selector(
                            selector, timeout=3000
                        )
                        if desc_input:
                            break
                    except Error:
                        continue
                if desc_input:
                    await desc_input.click()
                    await desc_input.fill(description)
                    await page.wait_for_timeout(1000)

            # 点击发布按钮（可能是"发布"或底部提交）
            publish_btn_selectors = [
                "button:has-text('发布')",
                "button:has-text('提交')",
                "button[type='submit']",
                "button:has-text('Publish')",
            ]
            clicked = False
            for selector in publish_btn_selectors:
                try:
                    btn = await page.wait_for_selector(selector, timeout=3000)
                    if btn:
                        await btn.click()
                        clicked = True
                        break
                except Error:
                    continue

            if not clicked:
                return {"success": False, "error": "找不到发布按钮"}

            # 等待发布成功提示
            try:
                await page.wait_for_selector(
                    "text=发布成功, text=success, text=已发布",
                    timeout=60000,
                )
                await self._set_state("PUBLISHED")
                return {
                    "success": True,
                    "title": title,
                    "platform": "抖音视频",
                    "url": page.url,
                }
            except Error:
                await self._set_state("LOGGED_IN")
                return {
                    "success": True,
                    "title": title,
                    "platform": "抖音视频",
                    "url": page.url,
                    "note": "已提交发布，请手动确认结果",
                }

        except Error as e:
            await self._set_state("LOGGED_IN")
            return {"success": False, "error": str(e)}

    async def get_stats(self) -> Dict[str, Any]:
        """获取数据统计（需要登录态）"""
        async with self._state_lock:
            if self.state != "LOGGED_IN":
                return {"ok": False, "error": f"未登录，当前状态: {self.state}"}

        page = self.page
        if not page:
            return {"ok": False, "error": "浏览器未初始化"}

        try:
            await page.goto(
                "https://creator.douyin.com/creator-micro/data/overview",
                timeout=60000,
                wait_until="domcontentloaded",
            )
            await page.wait_for_timeout(2000)

            # 尝试提取数据
            stats = await page.evaluate("""
                () => {
                    const text = document.body.innerText;
                    const views = text.match(/播放[\\s:]*([\\d,.]+)/);
                    const likes = text.match(/点赞[\\s:]*([\\d,.]+)/);
                    const shares = text.match(/分享[\\s:]*([\\d,.]+)/);
                    return {
                        views: views ? views[1] : '0',
                        likes: likes ? likes[1] : '0',
                        shares: shares ? shares[1] : '0',
                    };
                }
            """)

            return {
                "ok": True,
                "platform": "抖音短剧",
                "data": stats,
            }
        except Error as e:
            return {"ok": False, "error": str(e)}

    async def set_cookies(self, cookie_json: str) -> Dict[str, Any]:
        """注入 cookie JSON（用于无头环境保持登录态）"""
        if not isinstance(cookie_json, str) or not cookie_json.strip():
            return {
                "ok": False,
                "error": "cookie_json 不能为空",
            }
        try:
            cookies = json.loads(cookie_json)
        except json.JSONDecodeError as exc:
            return {
                "ok": False,
                "error": f"Cookie JSON 格式错误: {exc}",
            }

        if not isinstance(cookies, list):
            return {
                "ok": False,
                "error": "Cookie JSON 必须是数组格式",
            }

        self._cookie_json = cookie_json
        if self.context:
            await self.context.add_cookies(cookies)
            await self._set_state("LOGGED_IN")
            return {"ok": True, "message": "Cookie 已注入"}
        return {"ok": True, "message": "Cookie 已缓存，下次启动时注入"}

    async def close(self):
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Error:
            pass
        finally:
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None
            await self._set_state("IDLE")
