const WebSocket = require("ws");
const http = require("http");

const GATEWAY = "http://localhost:18080/v1/doubao/capture";
const SESSION = "cdp-" + Date.now();

let seenTexts = new Set();
let lastFullText = "";

function sendToGateway(messages) {
  if (!messages || messages.length === 0) return;
  const payload = JSON.stringify({
    session_id: SESSION,
    bot_id: "doubao_web_cdp",
    captured_at: Math.floor(Date.now() / 1000),
    messages: messages
  });
  const buf = Buffer.from(payload);
  const req = http.request(GATEWAY, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Content-Length": buf.length }
  }, (res) => {
    let data = "";
    res.on("data", c => data += c);
    res.on("end", () => console.log("[CDP] Sent", messages.length, "msgs:", res.statusCode));
  });
  req.on("error", e => console.log("[CDP] GW error:", e.message));
  req.write(buf);
  req.end();
}

async function getPageText(ws) {
  return new Promise((resolve) => {
    const id = Date.now();
    const cmd = JSON.stringify({
      id: id,
      method: "Runtime.evaluate",
      params: {
        expression: "document.body ? document.body.innerText : ''",
        returnByValue: true,
        timeout: 3000
      }
    });
    
    const handler = (data) => {
      try {
        const msg = JSON.parse(data.toString());
        if (msg.id === id) {
          ws.removeListener("message", handler);
          resolve(msg.result && msg.result.result ? msg.result.result.value : "");
        }
      } catch(e) {}
    };
    
    ws.on("message", handler);
    ws.send(cmd);
    setTimeout(() => { ws.removeListener("message", handler); resolve(""); }, 4000);
  });
}

async function poll(ws) {
  const text = await getPageText(ws);
  if (!text || text.length < 50) return;
  
  if (!lastFullText) {
    lastFullText = text;
    console.log("[CDP] Initial text captured,", text.length, "chars");
    return;
  }
  
  if (text === lastFullText) return;
  
  const oldLines = new Set();
  for (const line of lastFullText.split("\n")) {
    const t = line.trim();
    if (t.length > 5) oldLines.add(t.slice(0, 80));
  }
  
  const newMsgs = [];
  for (const line of text.split("\n")) {
    const t = line.trim();
    if (t.length < 5) continue;
    const key = t.slice(0, 80);
    if (!oldLines.has(key) && !seenTexts.has(key)) {
      seenTexts.add(key);
      newMsgs.push({
        role: t.length < 100 ? "user" : "assistant",
        content: t,
        timestamp: Date.now()
      });
    }
  }
  
  if (newMsgs.length > 0) {
    console.log("[CDP] +" + newMsgs.length + " new msgs");
    sendToGateway(newMsgs);
  }
  
  lastFullText = text;
}

async function main() {
  console.log("[CDP] Starting...");
  
  // Find doubao tab
  const tabsRes = await new Promise((resolve) => {
    http.get("http://127.0.0.1:9229/json", (res) => {
      let data = "";
      res.on("data", c => data += c);
      res.on("end", () => resolve(data));
    });
  });
  
  const tabs = JSON.parse(tabsRes);
  const tab = tabs.find(t => t.url && t.url.includes("doubao.com") && t.url.includes("/chat"));
  if (!tab) {
    console.log("[CDP] Doubao tab not found!");
    console.log("Tabs:", tabs.map(t => t.title).join(" | "));
    process.exit(1);
  }
  
  console.log("[CDP] Found:", tab.title);
  const wsUrl = tab.webSocketDebuggerUrl;
  
  const ws = new WebSocket(wsUrl);
  ws.on("open", () => {
    console.log("[CDP] Connected, starting capture in 2s...");
    setTimeout(() => {
      poll(ws).then(() => {
        setInterval(() => poll(ws), 2000);
      });
    }, 2000);
  });
  ws.on("error", e => console.log("[CDP] WS error:", e.message));
  ws.on("close", () => console.log("[CDP] Disconnected"));
}

main().catch(e => console.error("[CDP] Fatal:", e.message));
