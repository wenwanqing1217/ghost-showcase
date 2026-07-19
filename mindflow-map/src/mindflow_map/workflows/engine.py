"""工作流引擎 - MindFlow 的核心大脑"""

import asyncio
import logging
import re
import json
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from mindflow_map.tools.baidu_map import BaiduMapTool
from mindflow_map.identity.aid_client import AlphaIDClient
from mindflow_map.ai.intent import IntentParser

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
            )
        elif query:
            result = await self.baidu_map.search_location(query=query)
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


class WorkflowEngine:
    """MindFlow 工作流引擎"""

    def __init__(self):
        self.tools: Dict[str, Tool] = {
            "map": MapNavigationTool(),
            "douyin": DouyinPublishTool(),
            "shopify": ShopifyOptimizeTool(),
        }
        self.alpha_id_client = AlphaIDClient()
        self.intent_parser = IntentParser()
        self._executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="mindflow-worker")

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
        """并发执行多个工具请求（多线程核心优化）。"""
        if not requests:
            return []

        # 先在主线程并行解析所有意图
        intent_tasks = [self.intent_parser.parse(req.get("text", "")) for req in requests]
        intents = await asyncio.gather(*intent_tasks)

        # 收集需要执行的工具
        tool_calls: List[tuple[str, Tool, Dict[str, Any]]] = []
        for req, intent in zip(requests, intents):
            tool_name = self._select_tool(intent)
            tool = self.tools.get(tool_name)
            if tool:
                params = self._build_params(intent, req.get("text", ""), req.get("context", {}))
                tool_calls.append((tool_name, tool, params))

        if not tool_calls:
            return []

        # 使用线程池并发执行所有工具
        results: List[Dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=min(len(tool_calls), self._executor._max_workers)) as pool:
            futures = {
                pool.submit(self._run_tool_sync, tool, params): tool_name
                for tool_name, tool, params in tool_calls
            }
            for future in as_completed(futures):
                tool_name = futures[future]
                try:
                    results.append(future.result())
                except Exception as exc:
                    logger.error("Tool %s failed in parallel execution: %s", tool_name, exc)
                    results.append({"type": tool_name, "data": {"error": str(exc)}})

        return results

    def _run_tool_sync(self, tool: Tool, params: Dict[str, Any]) -> Dict[str, Any]:
        """同步运行异步工具（用于线程池并发执行）。"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 在已有事件循环的线程中，使用 nest_asyncio 或创建新线程
                # 这里采用最简单的方式：在独立线程中运行
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as inner_pool:
                    future = inner_pool.submit(asyncio.run, tool.execute(params))
                    return future.result(timeout=30)
            else:
                return loop.run_until_complete(tool.execute(params))
        except Exception:
            # 最终回退：直接在新线程中运行
            return asyncio.run(tool.execute(params))

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
        return self.tools.get(intent_type)

    def _build_params(self, intent: Dict[str, Any], text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """构建工具参数"""
        params = dict(intent)
        params["text"] = text
        params["context"] = context

        if intent.get("type") == "map" and intent.get("action") == "navigate":
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
                api_result = data.get("result", {})
                answer_type = api_result.get("answer_type", "")

                if answer_type == "gptmodel_navigate":
                    nav = api_result.get("navigation_data", {})
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
                else:
                    return "该路线暂时无法规划，请尝试其他出行方式或地址。"

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

        return "我已收到你的消息，正在处理中。"

    def _save_memory_sync(self, user_id: str, text: str, result: Dict[str, Any]):
        """同步保存记忆（在线程池中运行，避免 asyncio.run 反模式）。"""
        try:
            # 在线程池中创建新的事件循环来运行异步代码
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    self.alpha_id_client.save_memory(
                        user_id=user_id,
                        content=text,
                        metadata={"result": result},
                    )
                )
            finally:
                loop.close()
        except Exception as exc:
            logger.debug("Memory save skipped for %s: %s", user_id, exc)

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
