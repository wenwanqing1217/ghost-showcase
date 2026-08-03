import express from "express";
import { createProxyMiddleware } from "http-proxy-middleware";
import http from "http";

const app = express();

app.get("/health", (req, res) => {
  res.status(200).json({ ok: true, gateway: "node-fallback", alphaid: "http://localhost:8002", nebula: "http://localhost:2002" });
});

app.use("/v1/human", createProxyMiddleware({
  target: "http://localhost:8002",
  changeOrigin: true,
  ws: false,
  proxyErrorHandler: (err, req, res) => res.status(502).json({ success: false, error: "Alpha-ID unreachable", detail: String(err) })
}));

app.use("/v1/agent", createProxyMiddleware({
  target: "http://localhost:8002",
  changeOrigin: true,
  ws: false,
  proxyErrorHandler: (err, req, res) => res.status(502).json({ success: false, error: "Alpha-ID unreachable", detail: String(err) })
}));

app.use("/v1/internal", (req, res) => res.status(501).json({ success: false, message: "internal routes not available in local fallback gateway" }));

app.use("/v1/net", (req, res) => res.status(501).json({ success: false, message: "net-agent fallback not configured" }));

const server = http.createServer(app);

server.listen(18080, "0.0.0.0", () => {
  console.log("NODE_GATEWAY_LISTEN=18080");
});

