"""CDP capture daemon - reads doubao page via DevTools Protocol."""
import asyncio, json, time, hashlib, websockets, urllib.request, requests

GATEWAY = "http://localhost:18080/v1/doubao/capture"
SESSION = "cdp-" + str(int(time.time()))
BROWSER_WS = "ws://127.0.0.1:9229/devtools/browser/9456fd66-0cfa-4522-a52c-20f9d0306ef5"

seen = set()
last = ""
cid = 0

async def send_msgs(msgs):
    if not msgs: return
    try:
        r = requests.post(GATEWAY, json={
            "session_id": SESSION, "bot_id": "doubao_web_cdp",
            "captured_at": int(time.time()), "messages": msgs
        }, timeout=3)
        print(f"[CDP] Sent {len(msgs)} ({r.status_code})")
    except Exception as e:
        print(f"[CDP] GW err: {e}")

async def get_text(ws, sid):
    global cid
    cid += 1
    await ws.send(json.dumps({"id": cid, "sessionId": sid, "method": "Runtime.evaluate", "params": {
        "expression": "document.body ? document.body.innerText : ''",
        "returnByValue": True, "timeout": 5000
    }}))
    for _ in range(30):
        try:
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=2))
        except:
            return ""
        if msg.get("id") == cid:
            r = msg.get("result", {})
            if r.get("result"):
                return r["result"].get("value", "")
            return ""

async def loop(ws, sid):
    global last
    while True:
        text = await get_text(ws, sid)
        if text and len(text) > 50:
            if not last:
                last = text
                print(f"[CDP] Init: {len(text)} chars")
            elif text != last:
                old = set()
                for l in last.split("\n"):
                    t = l.strip()
                    if 4 < len(t) < 2000:
                        old.add(hashlib.md5(t.encode()).hexdigest())
                msgs = []
                for l in text.split("\n"):
                    t = l.strip()
                    if len(t) < 5 or len(t) > 2000: continue
                    h = hashlib.md5(t.encode()).hexdigest()
                    if h not in old and t not in seen:
                        seen.add(t)
                        msgs.append({"role": "user" if len(t) < 80 else "assistant", "content": t, "timestamp": int(time.time()*1000)})
                if msgs:
                    await send_msgs(msgs)
                last = text
        await asyncio.sleep(2)

async def main():
    print("[CDP] Starting...")
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9229/json").read())
    tid = None
    for t in tabs:
        u = t.get("url", "")
        if "doubao.com" in u and "/chat" in u and "worker" not in u:
            tid = t["id"]
            print(f"Target: {t.get('title','?')}")
            break
    if not tid:
        print("[CDP] Not found"); return
    
    async with websockets.connect(BROWSER_WS) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Target.attachToTarget", "params": {"targetId": tid, "flatten": True}}))
        sid = json.loads(await ws.recv())["params"]["sessionId"]
        print(f"[CDP] Session: {sid}")
        await ws.send(json.dumps({"id": 2, "sessionId": sid, "method": "Runtime.enable"}))
        await asyncio.sleep(3)
        print("[CDP] Starting capture loop...")
        await loop(ws, sid)

asyncio.run(main())
