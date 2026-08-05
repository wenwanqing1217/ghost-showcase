import express from "express";
import { createProxyMiddleware } from "http-proxy-middleware";
import http from "http";

// ── Config (avoid hardcoding ports — read from env, AGENTS.md §6) ──
const ALPHAID_URL = process.env.ALPHAID_URL || "http://localhost:8000";
const NEBULA_URL = process.env.NEBULA_URL || "http://localhost:2002";
const GATEWAY_PORT = parseInt(process.env.GATEWAY_PORT || "18080", 10);

const app = express();

app.get("/health", (req, res) => {
  res.status(200).json({ ok: true, gateway: "node-fallback", alphaid: ALPHAID_URL, nebula: NEBULA_URL });
});

app.use("/v1/human", createProxyMiddleware({
  target: ALPHAID_URL,
  changeOrigin: true,
  ws: false,
  proxyErrorHandler: (err, req, res) => res.status(502).json({ success: false, error: "Alpha-ID unreachable", detail: String(err) })
}));

app.use("/v1/agent", createProxyMiddleware({
  target: ALPHAID_URL,
  changeOrigin: true,
  ws: false,
  proxyErrorHandler: (err, req, res) => res.status(502).json({ success: false, error: "Alpha-ID unreachable", detail: String(err) })
}));

app.use("/v1/internal", (req, res) => res.status(501).json({ success: false, message: "internal routes not available in local fallback gateway" }));

app.use("/v1/net", (req, res) => res.status(501).json({ success: false, message: "net-agent fallback not configured" }));

const server = http.createServer(app);

server.listen(GATEWAY_PORT, "0.0.0.0", () => {
  console.log(`NODE_GATEWAY_LISTEN=${GATEWAY_PORT}`);
});

