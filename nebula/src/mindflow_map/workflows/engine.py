"""工作流引擎 - MindFlow 的核心大脑"""

import asyncio
import logging
import re
import json
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from mindflow_map.tools.baidu_map import BaiduMapTool
from mindflow_map.identity.aid_client import AlphaIDClient
from mindflow_map.ai.intent import IntentParser

if TYPE_CHECKING:
    from mindflow_map.plugins.registry import PluginRegistry

logger = logging.getLogger(__name__)


class Tool(ABC):
    """工具基类"""

    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        pass


class MapNavigationTool(Tool):
    """地图导航工具"""

    def __init__(self):
        self.baidu_map = BaiduMapTool()

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query = params.get("query", "")
        origin = params.get("origin", "")
        destination = params.get("destination", "")
        mode = params.get("mode", "driving")

        if destination:
            result = await self.baidu_map.plan_route(
                origin=origin,
                destination=destination,
                mode=mode,
                origin_lat=params.get("origin_lat"),
                origin_lng=params.get("origin_lng"),
                dest_lat=params.get("dest_lat"),
                dest_lng=params.get("dest_lng"),
            )
        elif query:
            result = await self.baidu_map.search_location(
                query=query,
                city=params.get("city"),
                latitude=params.get("latitude"),
                longitude=params.get("longitude"),
            )
        else:
            result = {"error": "缺少地点信息"}

        return {
            "type": "map",
            "data": result,
        }


class DouyinPublishTool(Tool):
    """抖音短剧自动发布工具"""

    def __init__(self):
        pass

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from mindflow_map.automation.douyin import DouyinAutomation
            douyin = DouyinAutomation()
            title = params.get("title", "")
            content = params.get("content", "")
            result = await douyin.publish(title=title, content=content)
        except Exception as e:
            result = {"success": False, "error": str(e)}

        return {
            "type": "douyin",
            "data": result,
        }


class ShopifyOptimizeTool(Tool):
    """Shopify 店铺优化工具"""

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        action = params.get("action", "analyze")

        return {
            "type": "shopify",
            "data": {
                "action": action,
                "status": "pending_implementation",
                "message": "Shopify 集成即将上线",
            },
        }


class ShortDramasPrecheckTool(Tool):
    """短剧平台内容预审工具"""

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from mindflow_map.integration.shortdramas import ShortDramasClient, AIContentScanner
            from mindflow_map.memory.store import MemoryStore
            from mindflow_map.config import settings

            title = params.get("title", "")
            content = params.get("content", "")
            user_id = params.get("user_id", "default")

            if not title and not content:
                return {
                    "type": "shortdramas",
                    "data": {
                        "success": False,
                        "error": "缺少标题或内容",
                    },
                }

            # 1. 本地 AI 预扫描
            scanner = AIContentScanner()
            ai_result = await scanner.scan(title=title, content=content)

            # 2. 如果本地扫描发现严重违规，直接拒绝
            if ai_result.get("risk_level") == "blocked":
                return {
                    "type": "shortdramas",
                    "data": {
                        "success": False,
                        "status": "rejected",
                        "rejected_by": "ai_local",
                        "ai_scan_result": ai_result,
                        "message": f"内容被 AI 预检拦截：{'; '.join(ai_result.get('violations', []))}",
                    },
                }

            # 3. 提交到短剧平台
            client = ShortDramasClient()
            callback_url = f"{settings.shortdramas_api_url.rstrip('/')}/api/v1/webhook/shortdramas/callback" if settings.shortdramas_api_url else None
            
            platform_result = await client.submit_precheck(
                title=title,
                content=content,
                content_type="video",
                callback_url=callback_url,
            )

            # 4. 持久化任务记录
            job_id = platform_result.get("job_id", "")
            if job_id:
                try:
                    db_url = settings.database_url or "sqlite+aiosqlite:///./mindflow_map.db"
                    store = MemoryStore(database_url=db_url)
                    await store.init()
                    await store.create_precheck_job(
                        job_id=job_id,
                        user_id=user_id,
                        title=title,
                        content_type="video",
                        callback_url=callback_url,
                    )
                    await store.update_precheck_job(
                        job_id,
                        ai_result=ai_result,
                        platform_status=platform_result.get("platform_status"),
                        platform_result=platform_result,
                    )
                except Exception as db_exc:
                    logger.warning("Precheck job persistence failed: %s", db_exc)

            return {
                "type": "shortdramas",
                "data": {
                    "success": platform_result.get("success", False),
                    "status": platform_result.get("status", "pending"),
                    "job_id": job_id,
                    "ai_scan_result": ai_result,
                    "platform_status": platform_result.get("platform_status"),
                    "platform_result": platform_result.get("platform_result"),
                    "message": platform_result.get("message", ""),
                    "demo": platform_result.get("demo", False),
                },
            }

        except Exception as e:
            logger.error("ShortDramas precheck failed: %s", e)
            return {
                "type": "shortdramas",
                "data": {
                    "success": False,
                    "error": str(e),
                },
            }




class ChatTool(Tool):
    """AI 对话工具 - 使用 LLM 进行自然对话"""

    def _get_llm(self):
        if not hasattr(self, "_llm_client") or self._llm_client is None:
            from mindflow_map.ai.llm import LLMClient
            self._llm_client = LLMClient()
        return self._llm_client

    async def execute(self, params):
        text = params.get("text", "")
        if not text:
            return {"type": "chat", "data": {"reply": "嗯？我没听到你说什么"}}

        try:
            llm = self._get_llm()
            reply = await llm.chat(
                messages=[
                    {"role": "system", "content": "你是一个友好的 AI 助手，名叫 MindFlow。请用中文自然回答。保持简洁友好。如果用户打招呼就热情回应，如果用户提问就认真回答。"},
                    {"role": "user", "content": text},
                ],
                temperature=0.7,
                max_tokens=512,
            )
            return {"type": "chat", "data": {"reply": reply}}
        except Exception as e:
            logger.error("ChatTool error: %s", e, exc_info=True)
            return {"type": "chat", "data": {"reply": "抱歉，我卡壳了，稍后再试试？"}}


class WorkflowEngine:
    """MindFlow 工作流引擎"""

    def __init__(self, plugin_registry: Optional["PluginRegistry"] = None) -> None:
        self.tools: Dict[str, Tool] = {
            "map": MapNavigationTool(),
            "douyin": DouyinPublishTool(),
            "shopify": ShopifyOptimizeTool(),
            "shortdramas": ShortDramasPrecheckTool(),
            "chat": ChatTool(),
        }
        self._plugin_registry = plugin_registry
        self._load_plugins()
        self.alpha_id_client = AlphaIDClient()
        self.intent_parser = IntentParser()
        self._max_workers = 8
        self._executor = ThreadPoolExecutor(max_workers=self._max_workers, thread_name_prefix="mindflow-worker")
        # 主线程 event loop，由 lifespan 注入；用于将后台任务安全地调度回主线程
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None

    def _load_plugins(self) -> None:
        """从插件注册表加载工具到引擎。"""
        registries = [self._plugin_registry]
        if self._plugin_registry is None:
            from mindflow_map.plugins.registry import get_global_registry
            registries = [get_global_registry()]
        for registry in registries:
            if registry is None:
                continue
            for definition in registry.list_tools():
                if definition.name in self.tools:
                    logger.warning("Plugin tool '%s' conflicts with built-in tool, skipping", definition.name)
                    continue
                tool_instance = registry.create_tool(definition.name)
                if tool_instance is not None:
                    self.tools[definition.name] = tool_instance
                    logger.info("Loaded plugin tool: %s v%s", definition.name, definition.version)

    def register_plugin_tool(self, tool_cls: type, name: str, description: str = "") -> None:
        """动态注册一个工具类到引擎。"""
        registry = getattr(tool_cls, "_registry", None)
        if registry is None:
            from mindflow_map.plugins.registry import get_global_registry
            registry = get_global_registry()
        definition = registry.register(tool_cls=tool_cls, name=name, description=description)
        if definition.name not in self.tools:
            tool_instance = definition.tool_cls()
            self.tools[definition.name] = tool_instance
            logger.info("Registered tool via plugin SDK: %s", definition.name)

    async def shutdown(self) -> None:
        """关闭线程池，释放资源。"""
        self._executor.shutdown(wait=True)
        logger.info("WorkflowEngine shutdown complete")

    async def execute(self, text: str, user_id: str = "default") -> Dict[str, Any]:
        """执行工作流"""
        # 并行获取用户上下文和解析意图
        user_context, intent = await asyncio.gather(
            self._get_user_context(user_id),
            self.intent_parser.parse(text),
        )

        tool_name = self._select_tool(intent)
        tool = self.tools.get(tool_name)

        if not tool:
            # 后台保存记忆，不阻塞回复（修复 asyncio.run 反模式）
            self._executor.submit(self._save_memory_sync, user_id, text, {"intent": intent})
            return {
                "text": f"我理解你想：{intent.get('description', '执行某个操作')}，但这个功能还在开发中。",
                "intent": intent,
            }

        params = self._build_params(intent, text, user_context)
        result = await tool.execute(params)
        reply = self._format_reply(result, intent)

        # 后台保存记忆，不阻塞回复
        self._executor.submit(self._save_memory_sync, user_id, text, result)

        return {
            "text": reply,
            "intent": intent,
            "result": result,
        }

    async def execute_parallel(
        self, requests: List[Dict[str, Any]], user_id: str = "default"
    ) -> List[Dict[str, Any]]:
        """并发执行多个工具请求（纯 asyncio 并发，避免线程池嵌套）。"""
        if not requests:
            return []

        # 先在主线程并行解析所有意图
        intent_tasks = [self.intent_parser.parse(req.get("text", "")) for req in requests]
        intents = await asyncio.gather(*intent_tasks)

        # 并发执行所有工具（纯 asyncio，无线程池）
        async def _run_tool(tool: Tool, params: Dict[str, Any]) -> Dict[str, Any]:
            try:
                return await tool.execute(params)
            except Exception as exc:
                logger.error("Tool failed in parallel execution: %s", exc)
                return {"error": str(exc)}

        tool_calls: List[tuple[Tool, Dict[str, Any]]] = []
        for req, intent in zip(requests, intents):
            tool_name = self._select_tool(intent)
            tool = self.tools.get(tool_name)
            if tool:
                params = self._build_params(intent, req.get("text", ""), req.get("context", {}))
                tool_calls.append((tool, params))

        if not tool_calls:
            return []

        results = await asyncio.gather(
            *(_run_tool(tool, params) for tool, params in tool_calls)
        )
        return list(results)

    def _run_tool_sync(self, tool: Tool, params: Dict[str, Any]) -> Dict[str, Any]:
        """同步运行异步工具（已弃用：execute_parallel 现在使用纯 asyncio）。"""
        raise NotImplementedError(
            "_run_tool_sync is deprecated. Use execute_parallel with async tools directly."
        )

    async def _get_user_context(self, user_id: str) -> Dict[str, Any]:
        """获取用户上下文"""
        try:
            return await self.alpha_id_client.get_user_context(user_id)
        except Exception:
            return {
                "user_id": user_id,
                "preferences": {},
                "history": [],
            }

    def _select_tool(self, intent: Dict[str, Any]) -> Optional[str]:
        """根据意图选择工具"""
        intent_type = intent.get("type", "")
        return intent_type if intent_type in self.tools else None

    def _build_params(self, intent: Dict[str, Any], text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """构建工具参数，将 entities 展开到顶层"""
        params = dict(intent)
        params["text"] = text
        params["context"] = context

        # 将 entities 中的字段提到顶层（intent parser 把参数放在 entities 里）
        entities = params.pop("entities", {}) or {}
        for k, v in entities.items():
            if v and k not in params:
                params[k] = v

        # 地图导航：尝试从上下文推断起点
        if intent.get("type") == "map" and intent.get("action") == "navigate":
            if not params.get("origin"):
                history = context.get("history", [])
                if history:
                    last_location = history[-1].get("location", "")
                    if last_location:
                        params["origin"] = last_location

        return params

    def _format_reply(self, result: Dict[str, Any], intent: Dict[str, Any]) -> str:
        """格式化回复"""
        result_type = result.get("type", "")

        if result_type == "map":
            data = result.get("data", {})
            message = data.get("message", "")

            if message and message != "ok":
                return f"地图查询暂时不可用：{message}"

            if intent.get("action") == "navigate":
                # Baidu Agent Plan API 扁平返回，不走 data.result
                info = data.get("info", {})
                tts = info.get("tts_tips", "")
                if tts:
                    return tts  # API 自带语音播报文案

                answer_type = data.get("answer_type", "")
                if answer_type == "gptmodel_navigate":
                    nav = data.get("navigation_data", {})
                    destination = nav.get("destination", {})
                    routes = nav.get("driving_routes", []) or nav.get("routes", [])

                    if routes:
                        route = routes[0]
                        distance = route.get("distance", "未知")
                        duration = route.get("duration", "未知")

                        if isinstance(duration, int):
                            minutes = duration // 60
                            seconds = duration % 60
                            duration_str = f"{minutes}分钟{seconds}秒" if seconds else f"{minutes}分钟"
                        else:
                            duration_str = str(duration)

                        dest_name = destination.get("name", "目的地")
                        reply = f"已为你规划到{dest_name}的路线：距离{distance}米，预计{duration_str}。"
                    else:
                        reply = "未找到路线，请检查地址是否正确。"

                    resource_key = data.get("resource_key")
                    if resource_key:
                        reply += f"\n\n点击查看地图：{BaiduMapTool.render_map_url(resource_key)}"

                    return reply

                # 兜底
                error_msg = data.get("message", "")
                if error_msg and error_msg != "ok":
                    return f"路线规划失败：{error_msg}"
                return "暂时无法规划该路线，请换个目的地试试。"
            elif intent.get("action") == "search":
                results = data.get("results", [])
                if results:
                    pois = results[:5]
                    lines = [f"找到 {len(results)} 个结果，显示前 {len(pois)} 个："]
                    for idx, poi in enumerate(pois, 1):
                        name = poi.get("name", "未知")
                        address = poi.get("address", "")
                        rating = poi.get("overall_rating", "")
                        line = f"{idx}. {name}"
                        if address:
                            line += f"（{address}）"
                        if rating:
                            line += f"，评分 {rating}"
                        lines.append(line)

                    resource_key = data.get("resource_key")
                    if resource_key:
                        lines.append(f"\n点击查看地图：{BaiduMapTool.render_map_url(resource_key)}")

                    return "\n".join(lines)
                else:
                    return "未找到相关地点，请换个关键词试试。"

        elif result_type == "douyin":
            data = result.get("data", {})
            if data.get("success"):
                return f"短剧《{data.get('title', '')}》已发布成功！"
            else:
                return f"发布失败：{data.get('error', '未知错误')}"

        elif result_type == "shopify":
            data = result.get("data", {})
            return data.get("message", "Shopify 集成即将上线")

        elif result_type == "shortdramas":
            data = result.get("data", {})
            success = data.get("success", False)
            demo = data.get("demo", False)
            status = data.get("status", "")
            job_id = data.get("job_id", "")
            message = data.get("message", "")
            
            if not success and data.get("rejected_by") == "ai_local":
                violations = "、".join(data.get("ai_scan_result", {}).get("violations", []))
                return f"内容未通过 AI 预检，已拦截：{violations}。请修改后重新提交。"
            
            if demo:
                return f"短剧预审服务未配置，演示模式：{message or '请先配置 SHORTDRAMAS_API_URL 和 SHORTDRAMAS_API_KEY'}"
            
            if not success:
                # 真实 API 调用失败（非演示、非 AI 拦截），明确标为错误
                return f"预审失败：{message or '平台返回错误，请稍后重试'}"
            
            if status == "rejected":
                return f"预审被拒绝：{message}"
            elif status == "approved":
                return f"预审通过！任务ID：{job_id}。可以继续发布流程。"
            elif status in ("pending", "scanning", "manual_review"):
                base = f"已提交预审，任务ID：{job_id}，当前状态：{status}"
                if message:
                    base += f"（{message}）"
                return base + "。请稍后查询结果。"
            else:
                return f"预审结果：{message or '处理中'}"

        elif result_type == "chat":
            data = result.get("data", {})
            return data.get("reply", "嗯？")

        return "我已收到你的消息，正在处理中。"

    def _save_memory_sync(self, user_id: str, text: str, result: Dict[str, Any]):
        """在后台线程中保存记忆，通过主线程 event loop 安全调度。"""
        logger.info("Memory save requested for user=%s text=%r", user_id, text[:50])
        try:
            loop = self._main_loop
            if loop is None or loop.is_closed():
                logger.warning("Memory save skipped for %s: main loop not available", user_id)
                return
            coro = self.alpha_id_client.save_memory(
                user_id=user_id,
                content=text,
                metadata={"result": result},
            )
            fut = asyncio.run_coroutine_threadsafe(coro, loop)
            fut.result(timeout=5)
            logger.info("Memory save completed for user=%s", user_id)
        except Exception as exc:
            logger.warning("Memory save skipped for %s: %s", user_id, exc)

    async def _save_memory(self, user_id: str, text: str, result: Dict[str, Any]):
        """保存到记忆（异步版本，供直接调用使用）"""
        try:
            await self.alpha_id_client.save_memory(
                user_id=user_id,
                content=text,
                metadata={"result": result},
            )
        except Exception as exc:
            logger.debug("Memory save failed for %s: %s", user_id, exc)

    def _parse_intent(self, text: str) -> Dict[str, Any]:
        """规则引擎：解析用户意图（作为 LLM fallback）"""
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
        if any(kw in text for kw in map_keywords) or re.search(r"(?:去|到|在)[\u4e00-\u9fa5]{2,10}(?:怎么|路线|导航|地址|$)", text):
            destination = ""
            match = re.search(r"(?:去|到|在)([\u4e00-\u9fa5]{2,10})(?:怎么|路线|导航|地址|$)", text)
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
