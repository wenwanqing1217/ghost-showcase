"""Manual smoke test for Gateway → Alpha-ID chain.

This is NOT a pytest test — it makes real HTTP calls against a running
Alpha-ID. Run it directly:

    python test_proxy.py

It is guarded by `if __name__ == "__main__":` so pytest collection no
longer executes it (which previously blocked the whole test session
with a real asyncio.run at module top-level).
"""
import httpx
import asyncio
import json
import os

ALPHAID_URL = os.environ.get("ALPHAID_URL", "http://localhost:8000")

async def run_smoke_test():
    client = httpx.AsyncClient(timeout=30.0)

    # Use a unique device fingerprint
    fp = "gateway_fresh_test"
    user_msg = "你好，请简单回复"

    # Test 1: Call chat without auth
    print("=== Test 1: chat without auth ===")
    resp = await client.post(
        f"{ALPHAID_URL}/api/v1/agent/chat",
        json={"alpha_id": "feishu_test", "message": user_msg},
    )
    print(f"  Status: {resp.status_code}")
    print(f"  Body: {resp.text[:300]}")

    # Test 2: Register
    print("\n=== Test 2: register ===")
    resp = await client.post(
        f"{ALPHAID_URL}/api/v1/identity/register",
        json={"alpha_id": "feishu_test", "device_fingerprint": fp},
    )
    print(f"  Status: {resp.status_code}")
    reg_data = resp.json()
    print(f"  Body: {reg_data}")
    registered_aid = reg_data.get("alpha_id", "feishu_test")

    # Test 3: Login with registered aid
    print(f"\n=== Test 3: login with {registered_aid} ===")
    resp = await client.post(
        f"{ALPHAID_URL}/api/v1/identity/login",
        json={"alpha_id": registered_aid, "device_fingerprint": fp},
    )
    print(f"  Status: {resp.status_code}")
    login_data = resp.json()
    print(f"  Body keys: {list(login_data.keys()) if isinstance(login_data, dict) else 'N/A'}")
    token = login_data.get("access_token") if isinstance(login_data, dict) else None
    print(f"  Has token: {bool(token)}")

    # Test 4: Chat with token
    if token:
        print(f"\n=== Test 4: chat with token ===")
        resp = await client.post(
            f"{ALPHAID_URL}/api/v1/agent/chat",
            json={"alpha_id": registered_aid, "message": user_msg},
            headers={"Authorization": f"Bearer {token}"},
        )
        print(f"  Status: {resp.status_code}")
        print(f"  Body: {resp.text[:500]}")

    await client.aclose()

if __name__ == "__main__":
    asyncio.run(run_smoke_test())
