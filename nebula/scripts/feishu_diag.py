"""飞书连接诊断工具"""

import asyncio
import json
import os
import sys
import time
import requests
import websockets

# 从环境变量读取飞书应用凭据，避免硬编码 secret
FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID", "cli_aad59b68b879dbe7")
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")


def test_get_token():
    """测试获取 tenant_access_token"""
    if not FEISHU_APP_SECRET:
        print("[SKIP] 未设置 FEISHU_APP_SECRET 环境变量，跳过测试")
        return "test_token"
    r = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET},
        timeout=10,
    )
    data = r.json()
    assert data.get("code") == 0, f"Token failed: {data}"
    print(f"[OK] tenant_access_token 获取成功, expire={data['expire']}s")
    return data["tenant_access_token"]


def test_ws_endpoint():
    """测试获取 WS 端点 URL"""
    if not FEISHU_APP_SECRET:
        print("[SKIP] 未设置 FEISHU_APP_SECRET 环境变量，跳过测试")
        return "wss://test.example.com/ws"
    r = requests.post(
        "https://open.feishu.cn/callback/ws/endpoint",
        headers={"locale": "zh"},
        json={"AppID": FEISHU_APP_ID, "AppSecret": FEISHU_APP_SECRET},
        timeout=10,
    )
    data = r.json()
    assert data.get("code") == 0, f"Endpoint failed: {data}"
    url = data["data"]["URL"]
    print(f"[OK] WS 端点获取成功: {url[:60]}...")
    return url


async def test_ws_connect_send_recv(ws_url):
    """连接 WS 并等待事件（10秒超时）"""
    print("[*] 连接 WS...")
    async with websockets.connect(ws_url, max_size=2**20, ping_interval=None) as ws:
        print("[OK] WS 已连接")
        print("[*] 等待事件（10秒内给飞书 Bot 发条消息）...")
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=10)
            print(f"[!!!] 收到消息! 大小={len(msg)} bytes")
            print(f"[!!!] 内容前200字: {str(msg)[:200]}")
        except asyncio.TimeoutError:
            print("[FAIL] 10秒内未收到任何消息")
            print("[?] 可能原因: 飞书应用未配置 im.message.receive_v1 事件订阅")
            print("[?] 或 Bot 未发布/未添加为好友")


async def test_send_message(token, user_id="test"):
    """测试发送消息"""
    import httpx
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            "https://open.feishu.cn/open-apis/im/v1/messages",
            params={"receive_id_type": "open_id"},
            headers={"Authorization": f"Bearer {token}"},
            json={
                "receive_id": user_id,
                "msg_type": "text",
                "content": json.dumps({"text": "诊断消息：如果你看到这条，说明 API 正常"}),
            },
        )
        data = r.json()
        if data.get("code") == 0:
            print(f"[OK] 消息发送成功, message_id={data['data']['message_id']}")
        else:
            print(f"[FAIL] 发送失败: {data}")


if __name__ == "__main__":
    print("=" * 50)
    print("飞书连接诊断工具")
    print("=" * 50)

    # 1. Test token
    try:
        token = test_get_token()
    except Exception as e:
        print(f"[FATAL] Token 获取失败: {e}")
        sys.exit(1)

    # 2. Test WS endpoint
    try:
        ws_url = test_ws_endpoint()
    except Exception as e:
        print(f"[FATAL] WS 端点获取失败: {e}")
        sys.exit(1)

    # 3. Test WS connect
    asyncio.run(test_ws_connect_send_recv(ws_url))

    print("=" * 50)
    print("诊断完成")
