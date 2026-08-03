"""飞书机器人 - 长连接模式（基于 lark-oapi，含 PING/PONG 协议修复）"""

import asyncio
import json
import logging
from threading import Thread
from typing import Any, Dict, Optional

from mindflow_map.config import settings
from mindflow_map.api.feishu_sender import FeishuSender


logger = logging.getLogger(__name__)

# lark-oapi PING/PONG 补丁状态（幂等，只补丁一次）
_patched = False


class FeishuLongPollingClient:
    """飞书长连接客户端（后台线程 + 独立事件循环 + PONG 自动回复）"""

    def __init__(self, workflow_engine=None) -> None:
        self.app_id = settings.feishu_app_id
        self.app_secret = settings.feishu_app_secret
        self.verification_token = getattr(settings, "feishu_verification_token", None)
        self.encrypt_key = getattr(settings, "feishu_encrypt_key", None)
        self.gateway_url = "http://localhost:18080"
        self._ws_client = None
        self._sender = FeishuSender()
        self._thread: Optional[Thread] = None
        self._running = False

    def set_gateway_url(self, url: str) -> None:
        self.gateway_url = url

    def _build_event_handler(self):
        """构建事件处理器（延迟导入，避免主线程 event loop 污染）"""
        from lark_oapi.event.dispatcher_handler import EventDispatcherHandlerBuilder

        handler_builder = EventDispatcherHandlerBuilder(
            encrypt_key=self.encrypt_key or "",
            verification_token=self.verification_token or "",
        )

        async def _process_message(user_id: str, content_text: str) -> None:
            """异步处理消息并回复（在 WS 事件循环中运行）"""
            try:
                # 复用共享 httpx 客户端，避免每请求创建连接池
                client = FeishuSender._get_shared_client()
                try:
                    resp = await client.post(
                        f"{self.gateway_url}/v1/human/chat",
                        json={"alpha_id": user_id or "feishu_user", "message": content_text},
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    reply_text = data.get("data", {}).get("reply", "") or str(data)
                except Exception as e:
                    logger.error("Gateway 调用失败: %s", e)
                    reply_text = "抱歉我暂时无法处理你的消息（系统错误）"

                if user_id:
                    await self._sender.send_text(user_id, reply_text)
                    logger.info("已回复飞书消息 to=%s: %s", user_id, reply_text[:200])

            except Exception as e:
                logger.error("处理/回复飞书消息失败: %s", e, exc_info=True)

        def _event_to_dict(obj: Any) -> Any:
            """递归转换 Pydantic 模型为 dict（兼容 register_p2_im_message_receive_v1 传入的对象）"""
            if isinstance(obj, dict):
                return {k: _event_to_dict(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple)):
                return [_event_to_dict(v) for v in obj]
            # Pydantic BaseModel
            if hasattr(obj, "dict") and callable(obj.dict):
                try:
                    return _event_to_dict(obj.dict())
                except Exception:
                    pass
            # 有 __dict__ 但不是 dict 的对象
            if hasattr(obj, "__dict__") and not isinstance(obj, type):
                try:
                    return _event_to_dict(vars(obj))
                except Exception:
                    pass
            return obj

        def handle_message(data: Any) -> None:
            """同步回调：收到飞书 im.message.receive_v1 事件，调度异步处理"""
            logger.info("⚡ handle_message 被调用! data_type=%s", type(data).__name__)
            try:
                raw_event = data.event if hasattr(data, "event") else {}
                event_data = _event_to_dict(raw_event)
                if not isinstance(event_data, dict):
                    logger.warning("飞书事件数据无法解析为 dict: %r", type(raw_event))
                    return

                message_info = event_data.get("message", {})
                if not isinstance(message_info, dict):
                    return

                msg_type = message_info.get("message_type", "")
                if msg_type != "text":
                    # 非文本消息（语音、图片等），友善告知
                    sender = event_data.get("sender", {})
                    sender_id = sender.get("sender_id", {})
                    user_id = sender_id.get("user_id", "") or sender_id.get("open_id", "")
                    type_names = {"audio": "语音", "image": "图片", "file": "文件", "sticker": "表情"}
                    friendly = type_names.get(msg_type, msg_type)
                    logger.info("收到非文本消息 type=%s from=%s", msg_type, user_id)
                    if user_id:
                        loop = asyncio.get_running_loop()
                        loop.create_task(self._sender.send_text(
                            user_id, f"抱歉，我现在还看不懂{friendly}消息，可以给我发文字吗？😊"
                        ))
                    return

                raw_content = message_info.get("content", "")
                content_text = str(raw_content) if raw_content else ""
                if raw_content and isinstance(raw_content, str):
                    try:
                        parsed = json.loads(raw_content)
                        if isinstance(parsed, dict):
                            content_text = parsed.get("text", content_text)
                    except (json.JSONDecodeError, TypeError):
                        content_text = str(raw_content)

                if not content_text:
                    return

                sender = event_data.get("sender", {})
                sender_id = sender.get("sender_id", {})
                user_id = sender_id.get("user_id", "") or sender_id.get("open_id", "")
                chat_id = message_info.get("chat_id", "")

                logger.info("收到飞书消息 from=%s: %s", user_id, content_text)

                # 用 create_task 调度到当前事件循环中执行
                # 不需要创建新 loop — 已在 WS 线程的事件循环上下文中
                loop = asyncio.get_running_loop()
                loop.create_task(_process_message(user_id, content_text))

            except Exception as e:
                logger.error("处理飞书消息失败: %s", e, exc_info=True)

        # 注册消息接收事件
        handler_builder.register_p2_im_message_receive_v1(handle_message)

        # 注册已读回执事件（避免报错"processor not found"）
        def handle_message_read(data: Any) -> None:
            """处理消息已读事件（仅记录日志，不做回复）"""
            logger.debug("消息已读事件: %r", type(data).__name__)
        handler_builder.register_p2_im_message_message_read_v1(handle_message_read)

        return handler_builder.build()

    def start(self) -> None:
        """启动飞书长连接（后台守护线程）"""
        if not self.app_id or not self.app_secret:
            logger.warning("未配置飞书 App ID/Secret，跳过")
            return
        if self._running:
            logger.warning("飞书长连接已在运行")
            return

        logger.info("准备启动飞书长连接, App ID: %s", self.app_id)
        self._running = True
        self._thread = Thread(target=self._run_ws, daemon=True, name="feishu-ws")
        self._thread.start()
        logger.info("飞书长连接后台线程已启动")

    def _run_ws(self) -> None:
        """在后台线程中运行 WS 长连接（延迟导入 lark_oapi，避免 event loop 冲突）"""
        # 第一步：创建独立事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # 延迟导入 lark_oapi.ws.client——此时 asyncio.get_event_loop()
            # 会返回我们刚创建的 loop，不会捕获主线程的 uvicorn loop
            import lark_oapi.ws.client as _ws_mod
            from lark_oapi.ws.client import Client as WSClient
            from lark_oapi.core.enum import LogLevel
            from lark_oapi.ws.enum import FrameType, MessageType
            from lark_oapi.ws.const import HEADER_TYPE

            # ---- PING/PONG 协议修复 ----
            # lark-oapi v1.7.1 收到服务端 PING 后只 return 不发 PONG，
            # 导致飞书服务端认为连接已死 -> 控制台显示"连接失败"
            # 使用子类化替代直接 monkey-patch，避免污染全局类
            _orig_hcf = _ws_mod.Client._handle_control_frame

            async def _patched_hcf(self_frame, frame):
                """劫持版本：收到 PING 后回复 PONG"""
                type_val = None
                for h in frame.headers:
                    if h.key == HEADER_TYPE:
                        type_val = h.value
                        break
                if type_val is None:
                    await _orig_hcf(self_frame, frame)
                    return

                mt = MessageType(type_val)
                if mt == MessageType.PING:
                    # 构造 PONG 帧（与 _new_ping_frame 对称）
                    pong = _ws_mod.Frame()
                    ph = pong.headers.add()
                    ph.key = HEADER_TYPE
                    ph.value = MessageType.PONG.value
                    pong.service = getattr(self_frame, "_service_id", 0)
                    pong.method = FrameType.CONTROL.value
                    pong.SeqID = 0
                    pong.LogID = 0
                    await self_frame._write_message(pong.SerializeToString())
                    logger.debug("已回复飞书 PONG")
                    return  # 不调用原 handler（原 handler 对 PING 只 return）

                # PONG 或其他控制帧交给原逻辑
                await _orig_hcf(self_frame, frame)

            # 幂等补丁：只补丁一次，避免重复包装
            global _patched
            if not _patched:
                _ws_mod.Client._handle_control_frame = _patched_hcf
                _patched = True
                logger.info("已应用 lark-oapi PING/PONG 协议修复")

            # ---- 构建事件 handler ----
            event_handler = self._build_event_handler()

            # ---- 创建 WS 客户端并启动 ----
            self._ws_client = WSClient(
                app_id=self.app_id,
                app_secret=self.app_secret,
                log_level=LogLevel.INFO,
                event_handler=event_handler,
            )
            logger.info("飞书长连接正在连接...")

            # start() 内部会 loop.run_until_complete(_select())
            # _select() 是一个 while True: await sleep(3600)
            # 所以这个调用会阻塞线程直到连接断开
            self._ws_client.start()

        except KeyboardInterrupt:
            logger.info("飞书长连接收到中断信号")

        except Exception as e:
            logger.error("飞书长连接异常: %s", e, exc_info=True)

        finally:
            self._running = False
            try:
                if loop.is_running():
                    loop.stop()
                loop.close()
            except Exception:
                pass
            logger.info("飞书长连接已断开")

    def stop(self) -> None:
        """停止飞书长连接"""
        self._running = False
        if self._ws_client:
            try:
                self._ws_client.stop()
            except Exception:
                pass
        logger.info("飞书长连接已停止")


feishu_client = FeishuLongPollingClient()


def start_feishu_long_polling() -> None:
    feishu_client.start()
