"""抖音短剧平台自动化"""

import asyncio
import json
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Page, BrowserContext


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
                cookies = json.loads(cookie_json)
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
            except Exception:
                return {
                    "ok": False,
                    "error": "登录超时，请在浏览器中手动登录后重试",
                    "url": page.url,
                }

        except Exception as e:
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
                except Exception:
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
                except Exception:
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
                try:
                    upload_btn = await page.query_selector("input[type='file']")
                    if upload_btn:
                        await upload_btn.set_input_files(cover_image)
                        await page.wait_for_timeout(2000)
                except Exception:
                    pass  # 封面上传失败不影响主流程

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
                except Exception:
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
            except Exception:
                # 即使没看到成功提示，也返回当前状态
                await self._set_state("LOGGED_IN")
                return {
                    "success": True,
                    "title": title,
                    "platform": "抖音短剧",
                    "url": page.url,
                    "note": "已提交发布，请手动确认结果",
                }

        except Exception as e:
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
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def set_cookies(self, cookie_json: str) -> Dict[str, Any]:
        """注入 cookie JSON（用于无头环境保持登录态）"""
        try:
            cookies = json.loads(cookie_json)
            self._cookie_json = cookie_json
            if self.context:
                await self.context.add_cookies(cookies)
                await self._set_state("LOGGED_IN")
                return {"ok": True, "message": "Cookie 已注入"}
            return {"ok": True, "message": "Cookie 已缓存，下次启动时注入"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

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
        except Exception:
            pass
        finally:
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None
            await self._set_state("IDLE")
