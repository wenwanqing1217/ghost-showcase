import sys, asyncio, json, websockets, urllib.request

async def t():
    sys.stderr.write("1. loading tabs...\n")
    sys.stderr.flush()
    
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9229/json").read())
    sys.stderr.write(f"2. got {len(tabs)} tabs\n")
    sys.stderr.flush()
    
    tid = None
    for t in tabs:
        u = t.get("url", "")
        if "doubao.com" in u and "/chat" in u and "worker" not in u:
            tid = t["id"]
            sys.stderr.write(f"3. found: {t.get('title','?')[:30]}\n")
            sys.stderr.flush()
            break
    
    if not tid:
        sys.stderr.write("4. NOT FOUND\n")
        return
    
    sys.stderr.write("5. connecting to browser ws...\n")
    sys.stderr.flush()
    
    try:
        async with websockets.connect("ws://127.0.0.1:9229/devtools/browser/9456fd66-0cfa-4522-a52c-20f9d0306ef5") as ws:
            sys.stderr.write("6. connected! attaching to target...\n")
            sys.stderr.flush()
            
            await ws.send(json.dumps({"id": 1, "method": "Target.attachToTarget", "params": {"targetId": tid, "flatten": True}}))
            resp = await asyncio.wait_for(ws.recv(), timeout=5)
            sys.stderr.write(f"7. attach resp: {resp[:60]}\n")
            sys.stderr.flush()
            
            sid = json.loads(resp)["params"]["sessionId"]
            sys.stderr.write(f"8. session: {sid[:20]}\n")
            sys.stderr.flush()
            
            sys.stderr.write("9. DONE\n")
    except Exception as e:
        sys.stderr.write(f"ERROR: {e}\n")

asyncio.run(t())
