"""
Doubao CDP Capture — connects via DevTools Protocol to capture conversations.
Runs as background daemon, captures text diffs from doubao chat page.
"""
import asyncio, json, time, hashlib, websockets, urllib.request, requests

GATEWAY = "http://localhost:18080/v1/doubao/capture"
SESSION = "cdp-" + str(int(time.time()))
BROWSER_WS = "ws://127.0.0.1:9229/devtools/browser/9456fd66-0cfa-4522-a52c-20f9d0306ef5"

seen_texts = set()
last_text = ""
call_id = 0

def next_id():
    global call_id
    call_id += 1
    return call_id

def find_conv_area(text):
    """Find the main conversation area in the page text."""
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        t = line.strip()
        if len(t) > 3:
            cleaned.append(t)
    return cleaned

async def send_to_gateway(messages):
    if not messages:
        return
    try:
        r = requests.post(GATEWAY, json={
            "session_id": SESSION,
            "bot_id": "doubao_web_cdp",
            "captured_at": int(time.time()),
            "messages": messages
        }, timeout=3)
        print(f"[CDP] Sent {len(messages)} msgs ({r.status_code})")
    except Exception as e:
        print(f"[CDP] GW error: {e}")

async def get_page_text(ws, sid):
    """Evaluate JS in the doubao page to get text content."""
    cid = next_id()
    await ws.send(json.dumps({"id": cid, "sessionId": sid, "method": "Runtime.evaluate", "params": {
        "expression": "document.body ? document.body.innerText : ''",
        "returnByValue": True,
        "timeout": 5000
    }}))
    
    for _ in range(20):
        try:
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=3))
        except:
            return ""
        if msg.get("id") == cid:
            result = msg.get("result", {})
            if result.get("result"):
                return result["result"].get("value", "")
            return ""
        # Skip events

async def capture_loop(ws, sid):
    global last_text
    
    print("[CDP] Starting capture loop...")
    while True:
        try:
            text = await get_page_text(ws, sid)
            if not text or len(text) < 50:
                await asyncio.sleep(2)
                continue
            
            if not last_text:
                last_text = text
                print(f"[CDP] Initial: {len(text)} chars")
                await asyncio.sleep(2)
                continue
            
            if text == last_text:
                await asyncio.sleep(2)
                continue
            
            # Find new content
            old_chunks = set()
            for line in last_text.split("\n"):
                t = line.strip()
                if 5 < len(t) < 500:
                    old_chunks.add(hashlib.md5(t.encode()).hexdigest())
            
            new_msgs = []
            for line in text.split("\n"):
                t = line.strip()
                if len(t) < 5 or len(t) > 2000:
                    continue
                h = hashlib.md5(t.encode()).hexdigest()
                if h not in old_chunks and t not in seen_texts:
                    seen_texts.add(t)
                    is_user = len(t) < 80
                    new_msgs.append({
                        "role": "user" if is_user else "assistant",
                        "content": t,
                        "timestamp": int(time.time() * 1000)
                    })
            
            if new_msgs:
                await send_to_gateway(new_msgs)
            
            last_text = text
            
        except Exception as e:
            print(f"[CDP] Error: {e}")
        
        await asyncio.sleep(2)

async def main():
    print("[CDP] Finding doubao tab...")
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9229/json").read())
    
    target_id = None
    for t in tabs:
        u = t.get("url", "")
        if "doubao.com" in u and "/chat" in u:
            target_id = t["id"]
            print(f"Found: {t.get('title', '?')}")
            break
    
    if not target_id:
        print("[CDP] Doubao tab not found!")
        return
    
    print("[CDP] Connecting via browser websocket...")
    async with websockets.connect(BROWSER_WS) as ws:
        # Attach to target with flatten
        await ws.send(json.dumps({"id": 1, "method": "Target.attachToTarget", "params": {"targetId": target_id, "flatten": True}}))
        attach = json.loads(await ws.recv())
        sid = attach["params"]["sessionId"]
        print(f"[CDP] Session: {sid}")
        
        # Enable Runtime
        await ws.send(json.dumps({"id": 2, "sessionId": sid, "method": "Runtime.enable"}))
        
        # Wait for page to be ready
        print("[CDP] Waiting for page...")
        await asyncio.sleep(3)
        
        # Start capture
        await capture_loop(ws, sid)

if __name__ == "__main__":
    asyncio.run(main())
