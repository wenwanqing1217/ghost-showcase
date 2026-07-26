#!/usr/bin/env python3
"""
Net-Client — Local Background Agent
=====================================
Runs on the user's home computer. Maintains a persistent connection
to the Net-Agent server and executes router commands locally.

Lifecycle:
  1. Load config (router credentials, server URL)
  2. Connect to server (long-polling / task queue)
  3. Loop: claim task -> execute on local router -> report result
  4. Periodically: scan network -> upload metrics to server

Run:
    python main.py
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

# ── sys.path fix ────────────────────────────────────────────
# __file__ = ghost-main/net_client/main.py
# net_agent_common/ lives in ghost-main/ (parent dir)
_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)  # ghost-main/
sys.path.insert(0, _PARENT)

# ── config ──────────────────────────────────────────────────
CONFIG_PATH = Path(__file__).parent / "config.yaml"
SERVER_URL = os.getenv("NET_AGENT_SERVER", "http://localhost:18180")
POLL_INTERVAL = int(os.getenv("NET_CLIENT_POLL", "10"))
UPLOAD_INTERVAL = int(os.getenv("NET_CLIENT_UPLOAD", "3600"))
USER_ID = os.getenv("NET_AGENT_USER_ID", "")
JWT_TOKEN = os.getenv("NET_AGENT_JWT", "")


# ── helpers ─────────────────────────────────────────────────

def load_config() -> dict:
    """Load local config.yaml."""
    if CONFIG_PATH.exists():
        import yaml
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def get_router_adapter(config: dict):
    """
    Instantiate the correct router adapter from net_agent_common.
    Credentials are decrypted locally.
    """
    from net_agent_common.adapters.base import BaseRouterAdapter
    from net_agent_common.adapter_meta.vendor_registry import get_adapter
    from net_agent_common.auth.crypto import decrypt_credential

    vendor = config.get("vendor", "")
    salt = config.get("salt", "")
    enc_user = config.get("encrypted_username", {})
    enc_pass = config.get("encrypted_password", {})

    # Decrypt locally — server never sees plaintext
    # TODO 🟠: use bytearray + secure-zero for plaintext credentials (currently stays in str)
    username = decrypt_credential(enc_user, salt) if enc_user else "admin"
    password = decrypt_credential(enc_pass, salt) if enc_pass else ""

    adapter_cls = get_adapter(vendor)
    return adapter_cls(
        host=config.get("lan_address", "192.168.1.1"),
        username=username,
        password=password,
    )


# ── main loop ───────────────────────────────────────────────

async def run_client():
    """Main loop: poll for tasks, execute, report."""
    import httpx

    config = load_config()
    if not config:
        print("[ERROR] No config found. Run setup first.")
        sys.exit(1)

    adapter = get_router_adapter(config)
    print(f"[Net-Client] Router: {config.get('vendor')} @ {config.get('lan_address')}")
    print(f"[Net-Client] Server: {SERVER_URL}")
    print(f"[Net-Client] Poll every {POLL_INTERVAL}s, upload every {UPLOAD_INTERVAL}s")

    # Persistent connection: connect once, reuse for all operations
    await adapter._connect()
    print("[Net-Client] Router connected (persistent)")

    try:
        async with httpx.AsyncClient(base_url=SERVER_URL, timeout=30) as http:
            headers = {"Authorization": f"Bearer {JWT_TOKEN}"}
            last_upload = 0

            while True:
                try:
                    # 1. Poll for pending tasks
                    resp = await http.get("/v1/net/tasks/pending", headers=headers)
                    if resp.status_code == 200:
                        tasks = resp.json().get("tasks", [])
                        for task in tasks:
                            await execute_task(http, headers, adapter, task)

                    # 2. Periodic metric upload
                    now = time.time()
                    if now - last_upload >= UPLOAD_INTERVAL:
                        await upload_metrics(http, headers, adapter)
                        last_upload = now

                except httpx.ConnectError:
                    print("[WARN] Cannot reach server, retrying in 30s...")
                    await asyncio.sleep(30)
                    continue
                except Exception as e:
                    print(f"[ERROR] {e}")

                await asyncio.sleep(POLL_INTERVAL)
    finally:
        await adapter._disconnect()
        print("[Net-Client] Router disconnected")


async def execute_task(http, headers, adapter, task: dict):
    """Execute a single task from the queue."""
    task_id = task["id"]
    task_type = task["task_type"]
    body = task.get("task_body", {})

    print(f"[TASK] Executing {task_type} (id={task_id})")

    try:
        # No `async with adapter:` — connection is persistent in run_client
        if task_type == "reboot":
            result = await adapter.reboot()
        elif task_type == "scan_devices":
            devices = await adapter.get_lan_devices()
            result = {"devices": [{"mac": d.mac, "ip": d.ip, "name": d.hostname} for d in devices]}
        elif task_type == "refresh_status":
            wan = await adapter.get_wan_info()
            quality = await adapter.get_network_quality()
            result = {
                "wan": {"is_connected": wan.is_connected, "external_ip": wan.external_ip},
                "quality": {"latency_ms": quality.latency_ms, "score": quality.score},
            }
        elif task_type == "set_channel":
            band = body.get("band", "2.4G")
            channel = int(body.get("channel", 6))
            result = await adapter.set_wifi_channel(band, channel)
        elif task_type == "ban_mac":
            mac = body.get("mac", "")
            result = await adapter.ban_mac(mac)
        else:
            result = False

        # Report success
        await http.post(
            f"/v1/net/tasks/{task_id}/complete",
            headers=headers,
            params={"success": True, "detail": json.dumps(result) if isinstance(result, dict) else ""},
        )
        print(f"[TASK] {task_type} completed")

    except Exception as e:
        await http.post(
            f"/v1/net/tasks/{task_id}/complete",
            headers=headers,
            params={"success": False, "detail": str(e)},
        )
        print(f"[TASK] {task_type} failed: {e}")


async def upload_metrics(http, headers, adapter):
    """Collect network metrics and upload to server."""
    try:
        # No `async with adapter:` — connection is persistent
        wan = await adapter.get_wan_info()
        quality = await adapter.get_network_quality()
        devices = await adapter.get_lan_devices()

        payload = {
            "timestamp": int(time.time()),
            "latency_ms": quality.latency_ms,
            "packet_loss_pct": quality.packet_loss_pct,
            "jitter_ms": quality.jitter_ms,
            "online_devices_count": len(devices),
            "network_score": quality.score,
            "wan_connected": wan.is_connected,
            "external_ip": wan.external_ip,
        }

        # Store via server API (server writes to DB)
        resp = await http.post("/v1/net/metrics/upload", headers=headers, json=payload)
        if resp.status_code == 200:
            print(f"[UPLOAD] Metrics uploaded (score={quality.score}, devices={len(devices)})")
        elif resp.status_code == 404:
            print("[UPLOAD] Server endpoint /v1/net/metrics/upload not found")
    except Exception as e:
        print(f"[UPLOAD] Failed: {e}")


# ── entry ───────────────────────────────────────────────────

if __name__ == "__main__":
    print()
    print("=" * 50)
    print("   Net-Client v1.0.0")
    print("   Ghost Network Local Agent")
    print("=" * 50)
    print()
    asyncio.run(run_client())
