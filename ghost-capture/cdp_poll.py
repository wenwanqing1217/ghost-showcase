"""
CDP Poll Capture — runs singleshot every 3 seconds via subprocess.
More reliable than persistent WebSocket connection.
"""
import sys, time, hashlib, json, subprocess, requests, os

GATEWAY = "http://localhost:18080/v1/doubao/capture"
SCRIPT = os.path.join(os.path.dirname(__file__), "cdp_singleshot.py")
SEEN_FILE = os.path.join(os.path.dirname(__file__), "cdp_seen.json")

seen = set()
last = ""

# Load previously seen texts
if os.path.exists(SEEN_FILE):
    try:
        seen = set(json.load(open(SEEN_FILE, "r", encoding="utf-8")))
        print(f"[CDP-Poll] Loaded {len(seen)} seen texts")
    except:
        pass

def save_seen():
    try:
        with open(SEEN_FILE, "w", encoding="utf-8") as f:
            json.dump(list(seen)[-5000:], f, ensure_ascii=False)
    except:
        pass

def log(m):
    sys.stderr.write(m + "\n")
    sys.stderr.flush()

while True:
    try:
        # Run singleshot and capture output
        result = subprocess.run(
            ["python", SCRIPT],
            capture_output=True, text=True, timeout=10,
            cwd=os.path.dirname(SCRIPT)
        )
        text = result.stdout.strip()
        
        if not text or len(text) < 50:
            time.sleep(3)
            continue
        
        if not last:
            last = text
            log(f"Init: {len(text)} chars")
            time.sleep(3)
            continue
        
        if text == last:
            time.sleep(3)
            continue
        
        # Text changed!
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
                role = "user" if len(t) < 80 else "assistant"
                msgs.append({"role": role, "content": t, "timestamp": int(time.time()*1000)})
        
        if msgs:
            log(f"Change detected! {len(msgs)} new items")
            try:
                r = requests.post(GATEWAY, json={
                    "session_id": "cdp-poll-" + str(int(time.time())),
                    "bot_id": "doubao_web_cdp",
                    "captured_at": int(time.time()),
                    "messages": msgs
                }, timeout=5)
                log(f"Gateway: {r.status_code}")
            except Exception as e:
                log(f"GW err: {e}")
            save_seen()
        
        last = text
    except subprocess.TimeoutExpired:
        log("Timeout")
    except Exception as e:
        log(f"Error: {e}")
    
    time.sleep(3)
