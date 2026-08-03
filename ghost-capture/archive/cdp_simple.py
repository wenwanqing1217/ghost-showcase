"""Simple CDP capture - connect directly via WebSocket, no Playwright."""
import asyncio
import json
import time
import hashlib
import requests
import websockets

GATEWAY = "http://localhost:18080/v1/doubao/capture"
SESSION = "cdp-" + str(int(time.time()))
BROWSER_WS = "ws://127.0.0.1:9229/devtools/browser/9456fd66-0cfa-4522-a52c-20f9d0306ef5"

seen = set()
last_text = ""
msg_id = 0

async def call_method(ws, method, params=None):
    global msg_id
    msg_id += 1
    cmd = {"id": msg_id, "method": method, "params": params or {}}
    await ws.send(json.dumps(cmd))
    # Wait for response with matching id
    while True:
        resp = await ws.recv()
        data = json.loads(resp)
        if data.get("id") == msg_id:
            return data

async def get_page_text(ws, target_id):
    result = await call_method(ws, "Runtime.evaluate", {
        "expression": "document.body ? document.body.innerText : ''",
        "returnByValue": True,
        "timeout": 3000
    })
    if result.get("result") and result["result"].get("result"):
        return result["result"]["result"]["value"]
    return ""

async def poll_target(ws, target_id):
    global last_text
    text = await get_page_text(ws, target_id)
    if not text or len(text) < 50:
        return
    
    if not last_text:
        last_text = text
        print(f"[CDP] Initial: {len(text)} chars")
        return
    
    if text == last_text:
        return
    
    old_lines = set()
    for line in last_text.split("\n"):
        t = line.strip()
        if len(t) > 5:
            old_lines.add(t[:80])
    
    new_msgs = []
    for line in text.split("\n"):
        t = line.strip()
        if len(t) < 5:
            continue
        key = t[:80]
        if key not in old_lines and key not in seen:
            seen.add(key)
            is_user = len(t) < 100
            new_msgs.append({
                "role": "user" if is_user else "assistant",
                "content": t,
                "timestamp": int(time.time() * 1000)
            })
    
    if new_msgs:
        print(f"[CDP] +{len(new_msgs)} new msgs")
        try:
            r = requests.post(GATEWAY, json={
                "session_id": SESSION,
                "bot_id": "doubao_web_cdp",
                "captured_at": int(time.time()),
                "messages": new_msgs
            }, timeout=3)
            print(f"[CDP] Sent: {r.status_code}")
        except Exception as e:
            print(f"[CDP] GW err: {e}")
    
    last_text = text

async def main():
    print("[CDP] Looking for doubao tab...")
    import urllib.request
    resp = urllib.request.urlopen("http://127.0.0.1:9229/json")
    tabs = json.loads(resp.read())
    
    doubao = None
    for t in tabs:
        url = t.get("url", "")
        if "doubao.com" in url and "/chat" in url:
            doubao = t
            break
    
    if not doubao:
        print("[CDP] Doubao tab not found!")
        available = [t.get("title", "?")[:30] for t in tabs]
        print(f"Tabs: {available}")
        return
    
    target_ws = doubao["webSocketDebuggerUrl"]
    print(f"[CDP] Found: {doubao['title']}")
    print(f"[CDP] Target WS: {target_ws[:60]}...")
    
    async with websockets.connect(target_ws, max_size=2**24) as ws:
        print("[CDP] Connected!")
        
        # Enable Runtime domain
        await call_method(ws, "Runtime.enable")
        
        # Wait for page to load
        await asyncio.sleep(2)
        
        # First capture
        await poll_target(ws, target_ws)
        
        # Poll loop
        print("[CDP] Starting capture loop...")
        while True:
            await poll_target(ws, target_ws)
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
