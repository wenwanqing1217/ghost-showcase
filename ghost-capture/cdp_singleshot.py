"""One-shot CDP test - read page text and print it."""
import sys, asyncio, json, websockets, urllib.request

async def main():
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9229/json").read())
    tid = None
    for t in tabs:
        u = t.get("url", "")
        if "doubao.com" in u and "/chat" in u and "worker" not in u:
            tid = t["id"]
            break
    if not tid:
        sys.stderr.write("Not found\n"); return
    
    async with websockets.connect("ws://127.0.0.1:9229/devtools/browser/9456fd66-0cfa-4522-a52c-20f9d0306ef5") as ws:
        await ws.send(json.dumps({"id":1, "method":"Target.attachToTarget", "params":{"targetId":tid, "flatten":True}}))
        sid = json.loads(await ws.recv())["params"]["sessionId"]
        await ws.send(json.dumps({"id":2, "sessionId":sid, "method":"Runtime.enable"}))
        
        # Drain
        for _ in range(10):
            try: await asyncio.wait_for(ws.recv(), timeout=0.3)
            except: break
        
        # Evaluate
        cid = 3
        await ws.send(json.dumps({"id":cid, "sessionId":sid, "method":"Runtime.evaluate", "params":{
            "expression": "(function(){var m=document.querySelector(\"main\");return m?m.innerText:document.body.innerText;})()",
            "returnByValue": True, "timeout": 5000
        }}))
        
        for _ in range(10):
            try:
                m = json.loads(await asyncio.wait_for(ws.recv(), timeout=3))
                if m.get("id") == cid:
                    val = m.get("result",{}).get("result",{}).get("value","ERR")
                    print(val)
                    return
            except:
                print("TIMEOUT")
                return

asyncio.run(main())
