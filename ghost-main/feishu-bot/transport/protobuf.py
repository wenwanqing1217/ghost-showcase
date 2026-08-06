"""Protobuf 帧工具 — 飞书 WebSocket 协议帧解析"""

import json
import logging

from lark_oapi.ws.pb.pbbp2_pb2 import Frame

logger = logging.getLogger("feishu-bot")


def extract_payload(data: bytes) -> bytes:
    """从 pbbp2.Frame protobuf 原始字节中提取 payload 字段（field 8）。
    兼容服务端省略 SeqID/LogID 等必填字段导致 Frame.ParseFromString 失败的情况。
    """
    i = 0
    while i < len(data):
        tag = data[i]
        i += 1
        if i > len(data):
            break
        field_number = tag >> 3
        wire_type = tag & 0x07

        if wire_type == 0:  # VARINT
            while i < len(data) and data[i] & 0x80:
                i += 1
            i += 1
        elif wire_type == 1:  # 64-bit
            i += 8
        elif wire_type == 2:  # Length-delimited
            length = 0
            shift = 0
            while i < len(data):
                b = data[i]
                i += 1
                length |= (b & 0x7F) << shift
                shift += 7
                if not (b & 0x80):
                    break
            if field_number == 8:  # payload
                return data[i : i + length]
            i += length
        elif wire_type == 5:  # 32-bit
            i += 4
        else:
            break
    return b""


def parse_ws_message(raw_msg) -> dict | None:
    """解析 WS 消息，返回事件 dict 或 None"""
    event_data = None

    if isinstance(raw_msg, bytes):
        # 第一尝试：标准 protobuf 解析
        try:
            frame = Frame()
            frame.ParseFromString(raw_msg)
            event_text = frame.payload.decode("utf-8", errors="replace")
            if event_text:
                event_data = json.loads(event_text)
        except Exception:
            pass

        # Fallback：手动提取 protobuf payload（field 8）
        if event_data is None:
            payload_bytes = extract_payload(raw_msg)
            if payload_bytes:
                try:
                    event_data = json.loads(
                        payload_bytes.decode("utf-8", errors="replace")
                    )
                except json.JSONDecodeError:
                    pass

        # 最后尝试：原始字节中搜索 JSON
        if event_data is None:
            try:
                text = raw_msg.decode("utf-8", errors="replace")
                for marker in ['"type":"im.message.receive_v1"', '"event"']:
                    idx = text.find(marker)
                    if idx >= 0:
                        start = text.rfind("{", 0, idx)
                        if start >= 0:
                            candidate = text[start : start + 2000]
                            depth = 0
                            for i, c in enumerate(candidate):
                                if c == "{":
                                    depth += 1
                                elif c == "}":
                                    depth -= 1
                                    if depth == 0:
                                        event_data = json.loads(candidate[: i + 1])
                                        break
                            break
            except Exception:
                pass

        if event_data is None:
            try:
                text_preview = raw_msg[:200].decode("utf-8", errors="replace")
                if text_preview:
                    logger.warning(
                        "WS 消息无法解析: raw_preview=%s", text_preview[:200]
                    )
                else:
                    logger.warning("WS 消息无法解析: raw_hex=%s", raw_msg[:120].hex())
            except Exception:
                logger.warning("WS 消息无法解析: raw_hex=%s", raw_msg[:120].hex())

    elif isinstance(raw_msg, str):
        try:
            data = json.loads(raw_msg)
            if "event" in data or "type" in data:
                event_data = data
        except json.JSONDecodeError:
            pass

    return event_data


async def send_ack(raw_msg, ws) -> None:
    """发送 ACK 响应给飞书服务器"""
    try:
        frame = Frame()
        frame.ParseFromString(raw_msg if isinstance(raw_msg, bytes) else raw_msg.encode())
        from lark_oapi.ws.const import HEADER_BIZ_RT

        ack = Frame()
        for h in frame.headers:
            nh = ack.headers.add()
            nh.key = h.key
            nh.value = h.value
        rt = ack.headers.add()
        rt.key = HEADER_BIZ_RT
        rt.value = "0"
        ack.method = frame.method
        ack.service = frame.service
        ack.payload = b'{"msg":"success"}'
        await ws.send(ack.SerializeToString())
    except Exception as e:
        logger.debug("ACK 发送失败: %s", e)
