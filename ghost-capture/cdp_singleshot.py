"""One-shot CDP test - read page text and print it."""
import sys, os, asyncio, json, websockets, urllib.request

CDP_PORT = os.environ.get("CDP_PORT", "9229")

async def main():
    base = f"http://127.0.0.1:{CDP_PORT}"
    # 动态获取浏览器 WebSocket URL（避免硬编码每次启动变化的 UUID）
    try:
        ver = json.loads(urllib.request.urlopen(f"{base}/json/version").read())
        browser_ws = ver.get("webSocketDebuggerUrl", "")
    except Exception:
        browser_ws = ""
    if not browser_ws:
        sys.stderr.write("CDP not available\n")
        return

    tabs = json.loads(urllib.request.urlopen(f"{base}/json").read())
    tid = None
    for t in tabs:
        u = t.get("url", "")
        if "doubao.com" in u and "/chat" in u and "worker" not in u:
            tid = t["id"]
            break
    if not tid:
        sys.stderr.write("Not found\n"); return

    async with websockets.connect(browser_ws) as ws:
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
