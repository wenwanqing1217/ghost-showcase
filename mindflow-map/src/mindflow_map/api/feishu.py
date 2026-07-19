"""飞书机器人 - 长连接模式"""

import asyncio
import json
from threading import Lock
from typing import Any, Dict

from lark_oapi.ws.client import Client
from lark_oapi.event.dispatcher_handler import EventDispatcherHandlerBuilder
from lark_oapi.core.enum import LogLevel
from lark_oapi.api.im.v1 import P2ImMessageReceiveV1

from mindflow_map.config import settings
from mindflow_map.workflows.engine import WorkflowEngine


class FeishuLongPollingClient:
    """飞书长连接客户端"""

    def __init__(self):
        self.app_id = settings.feishu_app_id
        self.app_secret = settings.feishu_app_secret
        self.verification_token = getattr(settings, "feishu_verification_token", None)
        self.encrypt_key = getattr(settings, "feishu_encrypt_key", None)
        self.workflow_engine = WorkflowEngine()
        self._ws_client = None
        self._loop = asyncio.new_event_loop()
        self._loop_lock = Lock()

    def _run_async(self, coro):
        """线程安全地运行异步任务"""
        with self._loop_lock:
            return self._loop.run_until_complete(coro)

    def _build_event_handler(self):
        """构建事件处理器"""
        handler_builder = EventDispatcherHandlerBuilder(
            encrypt_key=self.encrypt_key or "",
            verification_token=self.verification_token or "",
        )

        def handle_message(data: P2ImMessageReceiveV1) -> None:
            """接收消息事件（同步入口，内部转异步执行）"""
            try:
                message = data.event.message
                if message.message_type != "text":
                    return

                content_text = ""
                if isinstance(message.content, str):
                    try:
                        content_data = json.loads(message.content)
                        content_text = content_data.get("text", "")
                    except json.JSONDecodeError:
                        content_text = message.content
                elif isinstance(message.content, dict):
                    content_text = message.content.get("text", "")
                else:
                    content_text = str(message.content)

                user_id = data.event.sender.sender_id.user_id
                print(f"[Feishu] 收到消息 from {user_id}: {content_text}")

                result = self._run_async(
                    self.workflow_engine.execute(content_text, user_id=user_id)
                )

                response_text = result.get("response", str(result)) if isinstance(result, dict) else str(result)
                self._run_async(self._reply_message(message.message_id, response_text))
            except Exception as e:
                print(f"[Feishu] 处理消息失败: {e}")

        handler_builder.register_p2_customized_event("im.message.receive_v1", handle_message)

        return handler_builder.build()

    def start(self) -> None:
        """启动长连接"""
        if not self.app_id or not self.app_secret:
            print("[Feishu] 未配置 App ID 或 App Secret，跳过飞书长连接")
            return

        print("[Feishu] 正在启动长连接...")
        try:
            event_handler = self._build_event_handler()
            self._ws_client = Client(
                app_id=self.app_id,
                app_secret=self.app_secret,
                log_level=LogLevel.INFO,
                event_handler=event_handler,
            )
            self._ws_client.start()
            print("[Feishu] 长连接已启动")
        except Exception as e:
            print(f"[Feishu] 启动长连接失败: {e}")

    async def _reply_message(self, message_id: str, content: str) -> None:
        """回复消息"""
        try:
            from lark_oapi.api.im.v1 import (
                ReplyMessageRequest,
                ReplyMessageRequestBody,
            )
            body = ReplyMessageRequestBody.builder() \
                .receive_id(message_id) \
                .msg_type("text") \
                .content(json.dumps({"text": content}, ensure_ascii=False)) \
                .build()
            request = ReplyMessageRequest.builder() \
                .receive_id(message_id) \
                .request_body(body) \
                .build()

            api_client = (
                Client.builder()
                .app_id(self.app_id)
                .app_secret(self.app_secret)
                .log_level(LogLevel.INFO)
                .build()
            )
            response = api_client.im.v1.message.reply(request)
            if not response.success():
                print(f"[Feishu] 回复消息失败: {response.msg}")
            else:
                print(f"[Feishu] 回复消息成功")
        except Exception as e:
            print(f"[Feishu] 回复消息异常: {e}")


# 全局客户端实例
feishu_client = FeishuLongPollingClient()


def start_feishu_long_polling() -> None:
    """启动飞书长连接"""
    feishu_client.start()
