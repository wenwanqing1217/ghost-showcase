"""CDP capture daemon - reads doubao page."""
import sys, asyncio, json, time, hashlib, websockets, urllib.request, requests

GATEWAY = "http://localhost:18080/v1/doubao/capture"
SESSION = "cdp-" + str(int(time.time()))
BROWSER_WS = "ws://127.0.0.1:9229/devtools/browser/9456fd66-0cfa-4522-a52c-20f9d0306ef5"

seen = set()
last = ""
cid = 0

def log(msg):
    sys.stderr.write(f"[CDP] {msg}\n")
    sys.stderr.flush()

async def send_msgs(msgs):
    if not msgs: return
    try:
        r = requests.post(GATEWAY, json={
            "session_id": SESSION, "bot_id": "doubao_web_cdp",
            "captured_at": int(time.time()), "messages": msgs
        }, timeout=3)
        log(f"Sent {len(msgs)} ({r.status_code})")
    except Exception as e:
        log(f"GW err: {e}")

async def drain_events(ws, timeout=1.0):
    """Drain pending CDP events."""
    try:
        while True:
            await asyncio.wait_for(ws.recv(), timeout=timeout)
    except:
        pass

async def evaluate(ws, sid, expr):
    global cid
    cid += 1
    await ws.send(json.dumps({"id": cid, "sessionId": sid, "method": "Runtime.evaluate", "params": {
        "expression": expr, "returnByValue": True, "timeout": 5000
    }}))
    while True:
        try:
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
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
        text = await evaluate(ws, sid, "document.body ? document.body.innerText : ''")
        if text and len(text) > 50:
            if not last:
                last = text
                log(f"Init: {len(text)} chars")
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
    log("Starting...")
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9229/json").read())
    tid = None
    for t in tabs:
        u = t.get("url", "")
        if "doubao.com" in u and "/chat" in u and "worker" not in u:
            tid = t["id"]
            log(f"Target: {t.get('title','?')[:30]}")
            break
    if not tid:
        log("Tab not found!"); return
    
    async with websockets.connect(BROWSER_WS) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Target.attachToTarget", "params": {"targetId": tid, "flatten": True}}))
        sid = json.loads(await ws.recv())["params"]["sessionId"]
        log(f"Session: {sid[:16]}")
        await ws.send(json.dumps({"id": 2, "sessionId": sid, "method": "Runtime.enable"}))
        await asyncio.sleep(2)
        await drain_events(ws)
        log("Starting capture loop...")
        await loop(ws, sid)

asyncio.run(main())
