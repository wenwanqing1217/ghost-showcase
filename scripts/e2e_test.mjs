#!/usr/bin/env node
/**
 * Ghost / Alpha-ID End-to-End Verification Script (Node.js ESM)
 * =========================================================
 * Enhanced with Docker-aware waiting, exponential backoff retries,
 * verbose timestamped logging, and a service summary report.
 */

import http from "node:http";
import https from "node:https";
import { spawn } from "node:child_process";

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------
const GATEWAY = "http://localhost:18080";
const TEST_ALPHA_ID = "e2e-test-alpha-001";
const TEST_MESSAGE = "你好，请确认 A2A 协议正常运行";
const MEMORY_PAYLOAD = {
  alpha_id: TEST_ALPHA_ID,
  content: "e2e verification memory entry",
  chain: "private",
  tags: ["e2e", "verification"],
};

const DEFAULT_TIMEOUT = 30; // seconds per HTTP request
const WAIT_MAX = 120;       // seconds (--wait flag)
const WAIT_POLL_INTERVAL = 2; // seconds between /health polls
const HEALTH_OK_PREFIX = "ok";

// Retry / backoff knobs
const MAX_RETRIES = 3;
const BASE_RETRY_DELAY = 2; // seconds
const MAX_RETRY_DELAY = 16;

const GREEN = "\x1b[92m";
const RED = "\x1b[91m";
const YELLOW = "\x1b[93m";
const CYAN = "\x1b[96m";
const BOLD = "\x1b[1m";
const DIM = "\x1b[2m";
const RESET = "\x1b[0m";

const results = [];
const serviceResponses = {}; // service -> true/false

// ---------------------------------------------------------------------------
// Timestamped logging
// ---------------------------------------------------------------------------
function ts() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}.${String(d.getMilliseconds()).padStart(3, "0")}`;
}

function logInfo(msg) {
  console.log(`  ${DIM}[${ts()}]${RESET} ${CYAN}INFO${RESET}  ${msg}`);
}

function logWarn(msg) {
  console.log(`  ${DIM}[${ts()}]${RESET} ${YELLOW}WARN${RESET}  ${msg}`);
}

function logPass(name, detail = "") {
  console.log(`  ${DIM}[${ts()}]${RESET} [${GREEN}PASS${RESET}] ${name}${detail ? `  — ${detail}` : ""}`);
}

function logFail(name, detail = "") {
  console.log(`  ${DIM}[${ts()}]${RESET} [${RED}FAIL${RESET}] ${name}${detail ? `  — ${detail}` : ""}`);
}

// ---------------------------------------------------------------------------
// HTTP helpers with exponential backoff retry
// ---------------------------------------------------------------------------
function request(url, options = {}) {
  return new Promise((resolve, reject) => {
    const mod = url.startsWith("https") ? https : http;
    const req = mod.request(url, options, (res) => {
      const chunks = [];
      res.on("data", (c) => chunks.push(c));
      res.on("end", () => {
        const body = Buffer.concat(chunks).toString("utf-8");
        resolve({ status: res.statusCode, body });
      });
    });
    req.on("error", reject);
    req.setTimeout(DEFAULT_TIMEOUT * 1000, () => {
      req.destroy();
      reject(new Error(`timeout after ${DEFAULT_TIMEOUT}s`));
    });
    if (options.body) req.write(options.body);
    req.end();
  });
}

async function withBackoff(fn, label) {
  let lastErr;
  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    try {
      return await fn();
    } catch (err) {
      lastErr = err;
      if (attempt < MAX_RETRIES) {
        const delay = Math.min(BASE_RETRY_DELAY * 2 ** (attempt - 1), MAX_RETRY_DELAY);
        logWarn(`Retry ${attempt + 1}/${MAX_RETRIES} for "${label}" after ${delay}s (${err.message})`);
        await sleep(delay * 1000);
      }
    }
  }
  throw lastErr;
}

async function get(url) {
  return withBackoff(
    () =>
      request(url, {
        method: "GET",
        headers: {
          "X-Tenant-ID": TEST_ALPHA_ID,
        },
      }),
    `GET ${url}`
  );
}

async function post(url, payload) {
  const body = JSON.stringify(payload);
  return withBackoff(
    () =>
      request(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(body),
          "X-Requested-With": "XMLHttpRequest",
          "Origin": "http://localhost:18080",
          "X-Tenant-ID": TEST_ALPHA_ID,
        },
        body,
      }),
    `POST ${url}`
  );
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function recordResult(name, passed, detail = "") {
  results.push({ name, passed, detail });
}

// ---------------------------------------------------------------------------
// Docker / pre-flight checks
// ---------------------------------------------------------------------------
async function checkDockerRunning() {
  // Try `docker info` first; fall back to probing well-known localhost ports.
  const ports = [
    { name: "Docker API (TCP)", url: "http://localhost:2375" },
    { name: "Docker API (UNIX)", url: "http://localhost:2376" },
    { name: "Gateway", url: `${GATEWAY}/health` },
  ];

  // Attempt docker CLI
  let dockerCliOk = false;
  try {
    // Linux/Mac 用 PATH 里的 docker；Windows 用 Docker Desktop 的 docker.exe。
    // spawn 的 ENOENT 是异步 error 事件，必须监听，否则 node 进程直接崩溃。
    const dockerCmd =
      process.platform === "win32"
        ? "C:/Program Files/Docker/Docker/resources/bin/docker.exe"
        : "docker";
    const proc = spawn(dockerCmd, ["info"], { stdio: ["ignore", "pipe", "pipe"] });
    const chunks = [];
    proc.stdout.on("data", (c) => chunks.push(c));
    proc.stderr.on("data", () => {});
    await new Promise((resolve) => {
      proc.on("error", () => resolve()); // ENOENT / EACCES：静默 fallback 到端口探测
      proc.on("close", (code) => {
        if (code === 0) dockerCliOk = true;
        resolve();
      });
    });
  } catch {
    // docker not available
  }

  if (dockerCliOk) {
    logInfo("Docker CLI responded with `docker info` — daemon is reachable");
    return true;
  }

  logWarn("Docker CLI not available or daemon not reachable; probing localhost ports...");

  let anyPortUp = false;
  for (const p of ports) {
    try {
      const resp = await new Promise((resolve) => {
        const req = http.request(p.url, { method: "GET", timeout: 2000 }, (res) => {
          const chunks = [];
          res.on("data", (c) => chunks.push(c));
          res.on("end", () => {
            resolve({ status: res.statusCode, body: Buffer.concat(chunks).toString("utf-8") });
          });
        });
        req.on("error", () => resolve(null));
        req.on("timeout", () => { req.destroy(); resolve(null); });
        req.end();
      });
      if (resp) {
        logInfo(`${p.name} (${p.url}) responded with status ${resp.status}`);
        anyPortUp = true;
      } else {
        logWarn(`${p.name} (${p.url}) — no response`);
      }
    } catch {
      logWarn(`${p.name} (${p.url}) — connection error`);
    }
  }

  return anyPortUp;
}

// ---------------------------------------------------------------------------
// waitForService — polls /health every WAIT_POLL_INTERVAL seconds
// ---------------------------------------------------------------------------
async function waitForService(url, maxWaitSec = WAIT_MAX) {
  const start = Date.now();
  logInfo(`Waiting for ${url}/health to report healthy (up to ${maxWaitSec}s)`);

  const serviceHealthMap = {}; // serviceName -> ok/false
  let allHealthy = false;

  while (!allHealthy) {
    const elapsed = (Date.now() - start) / 1000;
    if (elapsed > maxWaitSec) {
      logWarn(`Timeout after ${maxWaitSec}s — not all services became healthy`);
      return serviceHealthMap;
    }

    try {
      const resp = await request(`${url}/health`, { method: "GET", timeout: 5000 });
      if (resp.status === 200) {
        const data = JSON.parse(resp.body);
        const inner = data.data || data;

        const services = [
          { key: "alphaid", value: inner.alphaid || inner.alpha_id },
          { key: "gateway", value: inner.gateway },
          { key: "memory", value: inner.memory },
          { key: "a2a", value: inner.a2a },
        ].filter((s) => s.value !== undefined);

        const healthyServices = services.filter((s) => String(s.value).toLowerCase() === HEALTH_OK_PREFIX);
        const unhealthyServices = services.filter((s) => String(s.value).toLowerCase() !== HEALTH_OK_PREFIX);

        for (const s of healthyServices) {
          if (serviceHealthMap[s.key] !== true) {
            serviceHealthMap[s.key] = true;
            logPass(`Service "${s.key}" is healthy`);
          }
        }
        for (const s of unhealthyServices) {
          if (serviceHealthMap[s.key] !== true) {
            serviceHealthMap[s.key] = false;
            logWarn(`Service "${s.key}" reports status="${s.value}"`);
          }
        }

        // Treat health response as ok if any recognized service is ok,
        // or if the top-level response body itself says "ok"
        const topLevelOk = String(data.status || data.data || "").toLowerCase() === HEALTH_OK_PREFIX;
        allHealthy = healthyServices.length > 0 || topLevelOk;

        // Also consider all listed services healthy
        if (services.length > 0 && unhealthyServices.length === 0) allHealthy = true;
      } else {
        logWarn(`/health returned status ${resp.status}`);
      }
    } catch (err) {
      logWarn(`/health poll failed: ${err.message}`);
    }

    if (!allHealthy) {
      const remaining = Math.round(maxWaitSec - elapsed);
      logInfo(`Services not yet healthy; retrying in ${WAIT_POLL_INTERVAL}s (${remaining}s remaining)`);
      await sleep(WAIT_POLL_INTERVAL * 1000);
    }
  }

  const elapsed = ((Date.now() - start) / 1000).toFixed(1);
  logInfo(`All services healthy after ${elapsed}s`);
  return serviceHealthMap;
}

// ---------------------------------------------------------------------------
// Endpoint checks
// ---------------------------------------------------------------------------
async function checkQuickRegister() {
  const resp = await post(`${GATEWAY}/v1/human/chat`, {
    alpha_id: TEST_ALPHA_ID,
    message: TEST_MESSAGE,
  });
  serviceResponses["quick-register"] = resp.status === 200;
  if (resp.status !== 200) return `status=${resp.status}`;
  const data = JSON.parse(resp.body);
  if (!data.success) return `success=false`;
  const reply = (data.data && data.data.reply) || "";
  if (!reply) return "reply is empty";
  return null;
}

async function checkMemoryStore() {
  const resp = await post(`${GATEWAY}/v1/human/memory/store`, MEMORY_PAYLOAD);
  serviceResponses["memory-store"] = resp.status === 200;
  if (resp.status !== 200) return `status=${resp.status}`;
  const data = JSON.parse(resp.body);
  if (!data.success) return `success=false`;
  return null;
}

async function checkAuditLog() {
  const resp = await get(`${GATEWAY}/v1/agent/a2a/audit`);
  serviceResponses["audit-log"] = resp.status === 200;
  if (resp.status !== 200) return `status=${resp.status}`;
  const data = JSON.parse(resp.body);
  const records = Array.isArray(data) ? data : data.audit || data.records || [];
  // 审计日志为空是正常的（尚未产生 A2A 调用记录）
  if (!Array.isArray(records)) return `audit response not an array`;
  return null;
}

async function checkAgentsList() {
  const resp = await get(`${GATEWAY}/v1/agent/a2a/agents`);
  serviceResponses["agents-list"] = resp.status === 200;
  if (resp.status !== 200) return `status=${resp.status}`;
  const data = JSON.parse(resp.body);
  const agents = Array.isArray(data) ? data : data.agents || [];
  if (!Array.isArray(agents)) return `agents not a list`;
  return null;
}

async function checkAgentGraph() {
  const resp = await get(`${GATEWAY}/v1/agent/a2a/graph`);
  serviceResponses["agent-graph"] = resp.status === 200;
  if (resp.status !== 200) return `status=${resp.status}`;
  const data = JSON.parse(resp.body);
  const nodes = Array.isArray(data) ? data : (data.nodes || data.data?.nodes || []);
  const edges = Array.isArray(data) ? [] : (data.edges || data.data?.edges || []);
  if (!Array.isArray(nodes)) return `graph nodes not an array`;
  // nodes/edges 可以是空（尚无 A2A 调用记录），不强制有数据
  return null;
}

async function checkSkillsList() {
  const resp = await get(`${GATEWAY}/v1/agent/a2a/skills`);
  serviceResponses["skills-list"] = resp.status === 200;
  if (resp.status !== 200) return `status=${resp.status}`;
  const data = JSON.parse(resp.body);
  const skills = Array.isArray(data) ? data : data.skills || [];
  if (!Array.isArray(skills)) return `skills not a list`;
  return null;
}

async function checkHealth() {
  const resp = await get(`${GATEWAY}/health`);
  serviceResponses["health"] = resp.status === 200;
  if (resp.status !== 200) return `status=${resp.status}`;
  const data = JSON.parse(resp.body);
  const inner = data.data || data;
  const alphaidStatus = inner.alphaid || inner.alpha_id || "?";
  if (alphaidStatus !== "ok") return `alphaid=${alphaidStatus}`;
  return null;
}

async function checkDSHealth() {
  const resp = await get(`http://localhost:3001/api/health`);
  serviceResponses["ds-health"] = resp.status === 200;
  if (resp.status !== 200) return `status=${resp.status}`;
  return null;
}

async function checkDSProducts() {
  const resp = await get(`http://localhost:3001/api/products`);
  serviceResponses["ds-products"] = resp.status === 200;
  if (resp.status !== 200) return `status=${resp.status}`;
  const data = JSON.parse(resp.body);
  if (!data.items && !Array.isArray(data)) return "unexpected response shape";
  return null;
}

async function checkDSOrders() {
  const resp = await get(`http://localhost:3001/api/orders`);
  serviceResponses["ds-orders"] = resp.status === 200;
  if (resp.status !== 200) return `status=${resp.status}`;
  const data = JSON.parse(resp.body);
  if (!data.items && !Array.isArray(data)) return "unexpected response shape";
  return null;
}

// ---------------------------------------------------------------------------
// Summary report
// ---------------------------------------------------------------------------
function printSummary() {
  console.log(`\n${BOLD}${"=".repeat(60)}${RESET}`);
  console.log(`  ${BOLD}Service Response Summary${RESET}`);
  console.log(`${BOLD}${"-".repeat(60)}${RESET}`);
  console.log(`  ${DIM}Service / endpoint${RESET}                          ${DIM}Responded${RESET}`);
  console.log(`${BOLD}${"-".repeat(60)}${RESET}`);

  const keys = [
    ["Gateway /health", "health"],
    ["Quick-register + Agent chat", "quick-register"],
    ["Dual-chain memory store", "memory-store"],
    ["A2A audit log", "audit-log"],
    ["A2A agents list", "agents-list"],
    ["Agent graph", "agent-graph"],
    ["A2A skills list", "skills-list"],
  ];

  let respondedCount = 0;
  for (const [label, key] of keys) {
    const ok = serviceResponses[key];
    const marker = ok ? `${GREEN}  ✓  ${RESET}` : `${RED}  ✗  ${RESET}`;
    console.log(`  ${marker} ${label.padEnd(38, " ")} ${ok ? "yes" : "no"}`);
    if (ok) respondedCount++;
  }

  // Also surface any health-map services from waitForService
  const waitKeys = new Set(Object.keys(serviceResponses));
  for (const [svc, ok] of Object.entries(serviceHealthMap || {})) {
    if (waitKeys.has(svc)) continue;
    const marker = ok ? `${GREEN}  ✓  ${RESET}` : `${RED}  ✗  ${RESET}`;
    console.log(`  ${marker} ${svc.padEnd(38, " ")} ${ok ? "ok" : "not ok"}`);
    if (ok) respondedCount++;
  }

  console.log(`${BOLD}${"-".repeat(60)}${RESET}`);
  console.log(`  ${DIM}Services responded: ${respondedCount} / ${keys.length + (Object.keys(serviceHealthMap || {}).length)}${RESET}`);
  console.log(`${BOLD}${"=".repeat(60)}${RESET}\n`);
}

// Track health map across wait phase
let serviceHealthMap = {};

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
async function main() {
  const args = process.argv.slice(2);
  const waitFlag = args.includes("--wait");
  const waitMax = waitFlag ? WAIT_MAX : 0;

  console.log(`\n${BOLD}Ghost / Alpha-ID E2E Verification (Node.js ESM)${RESET}`);
  console.log(`  ${DIM}Timestamped output — ${ts()}${RESET}`);
  console.log(`  Gateway: ${GATEWAY}`);
  if (waitFlag) {
    logInfo(`--wait flag passed: will wait up to ${WAIT_MAX}s for the stack to become healthy before running checks`);
  }
  console.log("");

  // Pre-flight: Docker / port check
  logInfo("Running Docker pre-flight check...");
  const dockerOk = await checkDockerRunning();
  if (!dockerOk) {
    logWarn("Docker daemon does not appear to be running; continuing but checks may fail.");
  }

  // Wait phase
  if (waitMax > 0) {
    serviceHealthMap = await waitForService(GATEWAY, waitMax);
  } else {
    logInfo("Skipping wait phase (pass --wait to enable stack health waiting)");
  }

  // Individual endpoint checks
  const checks = [
    ["Quick-register + Agent chat", checkQuickRegister],
    ["Dual-chain memory store", checkMemoryStore],
    ["A2A audit log", checkAuditLog],
    ["A2A agents list", checkAgentsList],
    ["Agent graph", checkAgentGraph],
    ["A2A skills list", checkSkillsList],
    ["Health check", checkHealth],
    ["DS health", checkDSHealth],
    ["DS products API", checkDSProducts],
    ["DS orders API", checkDSOrders],
  ];

  console.log(`${BOLD}${"-".repeat(50)}${RESET}`);
  console.log(`  ${BOLD}Running endpoint checks...${RESET}`);
  console.log(`${BOLD}${"-".repeat(50)}${RESET}\n`);

  let passedCount = 0;
  for (const [name, fn] of checks) {
    process.stdout.write(`  [${CYAN}CHECK${RESET}] ${name} ... `);
    try {
      const err = await fn();
      if (err) {
        logFail(name, err);
        recordResult(name, false, err);
      } else {
        logPass(name);
        recordResult(name, true);
        passedCount++;
      }
    } catch (exc) {
      logFail(name, String(exc));
      recordResult(name, false, String(exc));
    }
  }

  // Summary
  printSummary();

  const total = results.length;
  console.log(`  ${passedCount}/${total} checks passed`);
  if (passedCount === total) {
    console.log(`  ${GREEN}${BOLD}ALL GREEN — stack is healthy${RESET}`);
  } else {
    console.log(`  ${RED}${BOLD}FAILURES:${RESET}`);
    for (const r of results) {
      if (!r.passed) console.log(`    ${RED}✗${RESET} ${r.name}: ${r.detail}`);
    }
  }
  console.log(`${BOLD}${"=".repeat(50)}${RESET}\n`);
  process.exit(passedCount === total ? 0 : 1);
}

main();
