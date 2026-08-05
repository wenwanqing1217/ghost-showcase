"""NURO 反向通道 — 云端→本地桌宠的推送桥

TERM: NUROBridge — 桌宠桥接器（云端→本地反向通道）

解决"本地 NURO 没打通"的核心断点：
  - 本地 NURO → 云端 已通（FairyBrain 调 /v1/human/chat）
  - 云端 → 本地 NURO 之前完全断（没有 push 路由）

本模块提供：
  1. WebSocket /v1/nuro/ws — 本地 NURO 连接后接收云端推送
  2. POST /v1/nuro/push — 云端调用，推送消息到已连接的本地 NURO
  3. GET /v1/nuro/status — 查看当前连接的 NURO 客户端

推送场景：
  - _loop_nuro 的 proactive_check() 提醒
  - SelfEvolution 的知识沉淀完成通知
  - 成长进化事件（精灵升级）
  - 飞书指令执行结果（如果用户想从桌宠看）
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Dict

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

logger = logging.getLogger("ghost-gateway")

router = APIRouter(prefix="/v1/nuro", tags=["nuro"])


# ── NURO 客户端连接管理 ──────────────────────────────────────

class NuroConnectionManager:
    """管理本地 NURO 桌宠的 WebSocket 连接"""

    def __init__(self) -> None:
        # alpha_id → WebSocket 连接
        self._connections: Dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()

    async def connect(self, alpha_id: str, websocket: WebSocket) -> bool:
        """本地 NURO 连接"""
        await websocket.accept()
        async with self._lock:
            # 断开旧连接（同一 alpha_id 重新连接）
            old = self._connections.get(alpha_id)
            if old:
                try:
                    await old.close()
                except Exception:
                    pass
            self._connections[alpha_id] = websocket
        logger.info("NURO 已连接: %s (共 %d 个)", alpha_id, len(self._connections))
        return True

    async def disconnect(self, alpha_id: str) -> None:
        """本地 NURO 断开"""
        async with self._lock:
            self._connections.pop(alpha_id, None)
        logger.info("NURO 已断开: %s (剩 %d 个)", alpha_id, len(self._connections))

    async def push(self, alpha_id: str, message: dict) -> bool:
        """推送消息到指定用户的本地 NURO

        Returns:
            True 如果推送成功，False 如果用户未连接
        """
        ws = self._connections.get(alpha_id)
        if not ws:
            logger.debug("NURO push 失败: %s 未连接", alpha_id)
            return False
        try:
            await ws.send_json(message)
            return True
        except Exception as e:
            logger.warning("NURO push 异常: %s", e)
            await self.disconnect(alpha_id)
            return False

    async def broadcast(self, message: dict) -> int:
        """广播到所有已连接的 NURO"""
        count = 0
        for alpha_id, ws in list(self._connections.items()):
            try:
                await ws.send_json(message)
                count += 1
            except Exception:
                await self.disconnect(alpha_id)
        return count

    def list_connected(self) -> list:
        """列出已连接的 NURO"""
        return list(self._connections.keys())

    def is_online(self, alpha_id: str) -> bool:
        return alpha_id in self._connections


# 全局单例
_manager = NuroConnectionManager()


def get_nuro_manager() -> NuroConnectionManager:
    """获取 NURO 连接管理器（供其他模块推送消息）"""
    return _manager


# ── WebSocket 端点（本地 NURO 连接）──────────────────────────


@router.websocket("/ws")
async def nuro_websocket(websocket: WebSocket, alpha_id: str = "default"):
    """本地 NURO 桌宠通过 WebSocket 连接，接收云端推送

    连接方式：ws://gateway:18080/v1/nuro/ws?alpha_id=XXX

    推送消息格式：
      {
        "type": "reminder" | "evolution" | "task_result" | "notification",
        "title": "标题",
        "body": "内容",
        "data": {...},
        "timestamp": 1234567890
      }
    """
    await _manager.connect(alpha_id, websocket)
    try:
        while True:
            # 保持连接，接收本地 NURO 的心跳/响应
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                # 处理本地 NURO 的消息（如心跳、观察数据）
                if msg.get("type") == "heartbeat":
                    await websocket.send_json({"type": "heartbeat_ack", "timestamp": time.time()})
                elif msg.get("type") == "observe":
                    # 本地 NURO 上报观察数据，转发到 Alpha-ID
                    logger.debug("NURO observe from %s: %s", alpha_id, msg.get("data", ""))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        await _manager.disconnect(alpha_id)
    except Exception as e:
        logger.error("NURO WebSocket 异常: %s", e)
        await _manager.disconnect(alpha_id)


# ── HTTP 端点（云端推送）─────────────────────────────────────


@router.post("/push")
async def nuro_push(request: Request):
    """云端调用此端点，推送消息到指定用户的本地 NURO

    Body:
        {
            "alpha_id": "user_id",
            "type": "reminder" | "evolution" | "task_result" | "notification",
            "title": "标题",
            "body": "内容",
            "data": {...}
        }

    Returns:
        { "success": true, "delivered": true/false }
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "body required"})

    alpha_id = body.get("alpha_id", "")
    if not alpha_id:
        return JSONResponse(status_code=400, content={"error": "alpha_id required"})

    message = {
        "type": body.get("type", "notification"),
        "title": body.get("title", ""),
        "body": body.get("body", ""),
        "data": body.get("data", {}),
        "timestamp": time.time(),
    }

    delivered = await _manager.push(alpha_id, message)
    return {
        "success": True,
        "delivered": delivered,
        "alpha_id": alpha_id,
        "online": _manager.is_online(alpha_id),
    }


@router.get("/status")
async def nuro_status():
    """查看当前连接的 NURO 客户端"""
    return {
        "success": True,
        "connected_clients": _manager.list_connected(),
        "total": len(_manager.list_connected()),
    }


@router.post("/broadcast")
async def nuro_broadcast(request: Request):
    """广播消息到所有已连接的 NURO（如系统通知）"""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "body required"})

    message = {
        "type": body.get("type", "notification"),
        "title": body.get("title", ""),
        "body": body.get("body", ""),
        "data": body.get("data", {}),
        "timestamp": time.time(),
    }

    count = await _manager.broadcast(message)
    return {"success": True, "delivered_to": count}
