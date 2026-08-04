# Ghost Platform — 项目管理地图

> **版本**: 1.0 | **2026-08-04**
> **性质**: 项目唯一权威参考 (Single Source of Truth)
> **所有其他文档必须引用本文档，不得重复定义其中已定义的概念**

---

## 0. 术语表（GLOSSARY）

> 每个术语只有一个定义。代码和文档中出现的任何变体都指向这里。

| 术语 | 权威定义 | 类型 | 所在 |
|:-----|:---------|:----|:-----|
| **Ghost Platform** | 整个项目的统称，包含所有服务、代码、文档 | 项目名 | 本表 |
| **Ghost AtoA** | Ghost Platform 的终极定位：Web4.0 Agent-to-Anything 全域自主智能体操作系统 | 定位 | 2.md.md |
| **Alpha-ID** | 个人终身 DID 身份系统，Git 子模块 `alphaid/projects`，端口 8000 | 服务 | alphaid/projects |
| **Gateway** | 统一 API 网关，端口 18080，所有外部请求的唯一入口 | 服务 | ghost-main/gateway |
| **Nebula** | 工作流引擎，端口 2002，FastAPI + 7层中间件 | 服务 | nebula |
| **Ghost DS** | 电商数据看板，Next.js 14，端口 3001(外部)→3000(内部) | 服务 | DS/ |
| **Orchestrator** | ⚠️ **三个不同的事物，见下方"Orchestrator 歧义"** | 歧义 | — |
| **Feishu Bot** | 飞书双通道机器人，4合1 (Chat/Execute/Notify/Approve) | 服务 | ghost-main/feishu-bot/ |
| **Feishu Consumer** | Redis Streams 消费者，异步推送飞书通知 | 服务 | ghost-main/feishu-bot/feishu_consumer.py |
| **Net-Agent** | 路由器远程管理服务，端口 18180 | 服务 | ghost-main/net_agent_server/ |
| **NURO** | 桌面精灵，纯本地 AI，不依赖 Gateway | 组件 | alphaid/projects/src/entrypoints/ |
| **Doubao Reader** | 豆包对话 LevelDB 解析器，**不是独立服务**，是库 | 库 | ghost-main/doubao_reader/ |
| **Flow** | MindFlow 前端门户，Fastify，端口 3036 | 服务 | flow/ |
| **EventBus (Python)** | Alpha-ID 进程内 pub/sub，基于 blinker | 组件 | alphaid/projects/src/core/event_bus.py |
| **EventBus (TS)** | DS 跨服务事件总线，基于 Redis Streams | 组件 | DS/src/lib/eventbus.ts |
| **Redis Streams** | Redis 7 流式数据结构，用于跨服务事件分发 | 技术 | docker-compose.yml |
| **AgentLoop** | Agent 主执行循环：LLM + Tools + Loop，类名 `AgentLoop` | 类 | alphaid/projects/src/core/agent.py:1012 |
| **Agent** | Alpha-ID Agent SDK 入口，类名 `Agent` | 类 | alphaid/projects/src/alpha_id/agent.py:19 |
| **A2A** | Agent-to-Agent 协议，HTTP REST，Ed25519 签名 | 协议 | alphaid/projects/src/core/a2a.py |
| **A2A Agent Graph** | 从注册表+审计日志动态计算的网络拓扑图，**不是持久化图** | 端点 | alphaid/projects/src/api/a2a.py:447 |
| **Memory Graph** | 从记忆条目按标签关联构建的知识图谱，**跟 Agent 无关** | 端点 | ghost-main/gateway/services/memory_graph.py |
| **TwinBrain** | 双脑状态机：sleep/awake/idle/error，管理 AgentLoop | 类 | alphaid/projects/src/core/twin_brain.py |
| **Dual-Chain Memory** | 显式记忆(知链/明文) + 隐式记忆(私链/AES-256-GCM) | 系统 | alphaid/projects/src/core/dual_chain.py |
| **DID** | 去中心化身份标识，Ed25519 密钥对 | 概念 | alphaid/projects/src/alpha_id/did.py |
| **JWT** | JSON Web Token，HS256 + HKDF-SHA256 密钥派生 | 技术 | alphaid/projects/src/auth/ |
| **tenantId** | 多租户隔离标识，所有业务数据按 tenantId 隔离 | 概念 | DS/prisma/schema.prisma |
| **storeMode** | 店铺模式：marketplace(集市) 或 independent(独立站) | 概念 | DS/prisma/schema.prisma |
| **Orchestrator 歧义** | 三个同名不同物的实现，见下方专用节 | 歧义 | — |
| **三层堆栈** | 理念层(Denny) → 系统中枢(AlphaID) → 底层网络(Ghost AtoA) | 架构 | 2.md.md |
| **七层架构** | L1感知→L2身份→L3工作流→L4调度→L5网关→L6业务→L7知识 | 架构 | 1.md.md |

### Orchestrator 歧义（必须显式区分）

| 全名 | 简称 | 在哪 | 干什么 | 端口 |
|:-----|:-----|:-----|:-------|:-----|
| `alpha_id/orchestrator.py` `MasterOrchestrator` | **进程内调度器** | alphaid/projects/src/alpha_id/orchestrator.py | Alpha-ID 内部后台循环（Feed/Capture/Obsidian/NURO/Evolution） | 无（进程内线程） |
| `core/orchestrator.py` `MasterOrchestrator` | **中枢调度器** | alphaid/projects/src/core/orchestrator.py | 管理 TwinBrain 生命周期 + 通道适配器 | 无（进程内线程） |
| `orchestrator/main.py` `TaskManager` | **任务编排器** | orchestrator/main.py | 协调 ToolA/ToolB 执行编码任务（⚠️ stub） | 19090 |

> **规则**：提到 "Orchestrator" 时必须显式说明指哪一个。文档中不得单独使用 "Orchestrator" 一词。

---

## 1. 项目全景（实际状态，非 aspirational）

### 1.1 三层终极堆栈

```
┌─────────────────────────────────────────────────────────────────┐
│  理念层 (外置大脑)                                                │
│  Denny AI ── 人机共生哲学、智能体行为规范、商业伦理               │
├─────────────────────────────────────────────────────────────────┤
│  系统中枢 (Alpha-ID)                                             │
│  ~35K+ 行 Python / 150+ 文件 / DID + 双链记忆 + AgentLoop + A2A  │
├─────────────────────────────────────────────────────────────────┤
│  底层网络 (Ghost AtoA)                                           │
│  Gateway + Nebula + Orchestrator(任务编排) + Net-Agent           │
│  + Ghost DS + Feishu Bot + Feishu Consumer + Flow               │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 七层系统架构（实际部署状态）

| 层 | 名称 | 服务 | 端口 | 功能度 | 说明 |
|:--:|:-----|:-----|:-----|:------:|:-----|
| L7 | 知识协同层 | Obsidian + 飞书多维表格 + Ghost DS 看板 | — | 60% | Obsidian 已接，飞书表格未接 |
| L6 | 业务展现层 | Ghost DS + Feishu Bot | 3001/8080 | 85% | DS 电商全功能；Bot 4合1 但 Docker unhealthy |
| L5 | 统一网关层 | Gateway | 18080 | 95% | 9 路由，生产就绪 |
| L4 | 智能调度层 | Orchestrator(任务编排) | 19090 | 20% | ⚠️ 骨架，ToolA/ToolB 为 stub |
| L3 | 工作流引擎层 | Nebula | 2002 | 85% | 7 层中间件，货源适配器 mock |
| L2 | 身份与权限层 | Alpha-ID + Net-Agent | 8000/18180 | 95% | DID + JWT + 双链记忆 + 路由器管理 |
| L1 | 感知与接入层 | Docker Compose + 数据采集 | — | 90% | 豆包 LevelDB + 飞书 WS + 路由器 HTTP |

### 1.3 服务清单（13 个可运行实体）

| # | 名称 | 类型 | 端口 | 框架 | 状态 | 功能度 | 测试 |
|:--:|:-----|:-----|:-----|:-----|:-----|:------:|:-----|
| 1 | PostgreSQL | 数据库 | 5432 | postgres:16 | ✅ healthy | — | — |
| 2 | Redis | 缓存/事件 | 6379 | redis:7 | ✅ healthy | — | — |
| 3 | Alpha-ID | FastAPI | 8000 | FastAPI | ✅ healthy | 95% | 839+ |
| 4 | Nebula | FastAPI | 2002 | FastAPI | ✅ healthy | 85% | 153 |
| 5 | Gateway | FastAPI | 18080 | FastAPI | ✅ healthy | 95% | 22 |
| 6 | Net-Agent | FastAPI | 18180 | FastAPI | ✅ healthy | 60% | 0 |
| 7 | Ghost DS | Next.js | 3001→3000 | Next.js 14 | ✅ healthy | 90% | 0 |
| 8 | Orchestrator | FastAPI | 19090 | FastAPI | ✅ healthy | 20% | 0 |
| 9 | Flow | Fastify | 3036 | Fastify | ✅ healthy | 70% | 5 |
| 10 | Feishu Bot | Python | 无(WS) | 自定义 | ⚠️ unhealthy | 80% | 1 |
| 11 | Feishu Consumer | Python | 无 | 自定义 | ⚠️ unhealthy | 70% | 0 |
| 12 | Prometheus | 监控 | 9090 | prom/prometheus | ✅ up | — | — |
| 13 | Grafana | 监控 | 3005→3000 | grafana/grafana | ✅ up | — | — |

> **注意**：Doubao Reader 不是独立服务，是库，打包进 Gateway Docker 镜像。

---

## 2. 调用链地图（实际代码路径）

> 每条链标注真实状态和具体断点位置。

### 链 1：用户浏览商品

```
浏览器 → Ghost DS 前端
  → GET /api/products
    → Prisma → PostgreSQL (SELECT * FROM products WHERE tenantId = ?)
      → JSON 响应
        → 渲染产品卡片
```
**状态**: ✅ 通 | **绕过 Gateway**: 是（部分前端组件直连 DS）

### 链 2：同步店铺数据

```
用户 → Ghost DS Settings
  → POST /api/sync
    → OneBound Client (DS/src/lib/onebound.ts)
      → GET /shoplazza/products → 远程 API
      → GET /shoplazza/orders → 远程 API
    → Prisma 批量 upsert (Product + Order)
    → SyncLog 记录
```
**状态**: ✅ 通 | **关键事实**: **不走 Nebula**。DS 直连 OneBound。Nebula 的 1688/CJ 适配器是 mock。

### 链 3：订单履约

```
用户 → FulfillModal
  → POST /api/orders/[id]/fulfill (直连 DS，绕过 Gateway)
    → OneBound Client.createFulfillmentOrder()
      → POST /orders → 远程 API
    → Prisma update Order (status = 'fulfilled')
```
**状态**: ✅ 通 | **绕过 Gateway**: 是

### 链 4：AI 文案生成

```
用户 → ProductAiDialog
  → POST /api/ai/copy (直连 DS，绕过 Gateway)
    → 如果有 AI_API_KEY → 外部 LLM (Groq/DeepSeek)
    → 如果没有 → 本地 demo 模板
```
**状态**: ⚠️ 部分通 | **关键事实**: **不走 Alpha-ID**。DS 直连外部 LLM 或用本地模板。Gateway 有 `/v1/ecom/ai/copy` 代理到 DS，但前端不使用。

### 链 5：飞书消息处理（两条路径，一条断裂）

**路径 A（✅ 通）**:
```
飞书用户 → Feishu Bot (WebSocket)
  → BackendRunner → 本地 CLI (AtomCode/ZCode/Codex)
    → 回复 → 飞书
```

**路径 B（❌ 断裂）**:
```
飞书用户 → Nebula feishu.py (WS长轮询)
  → POST {gateway}/v1/chat  ← ❌ 此端点不存在！
    → 应为 /v1/human/chat
```

### 链 6：豆包知识采集

```
豆包桌面 LevelDB
  → reader_daemon.py (60秒轮询)
    → POST /v1/doubao/capture (仅 localhost)
      → Alpha-ID 登录/注册
        → DualChainManager.save() → PostgreSQL
      → ObsidianWriter → Markdown 文件
```
**状态**: ✅ 通

### 链 7：NURO 桌面精灵

```
NURO → FairyBrain
  → 优先: POST /v1/human/chat → Gateway → Alpha-ID
  → 降级: POST /api/chat → 本地 Ollama
```
**状态**: ✅ 通 | Gateway 故障时自动降级

### 链 8：Redis 事件总线

```
DS webhook → XADD Redis Stream
  → feishu-consumer (XREADGROUP) ← ⚠️ 从未被调用
    → FeishuService.notify() → 飞书卡片
```
**状态**: ⚠️ 部分通 | `startConsuming()` 从未被任何服务调用。总线架构已定义，**实际休眠**。

### 链 9：Gateway 代理链

```
任何 Gateway 路由
  → _proxy_request() → httpx.AsyncClient
    → 目标服务 (Alpha-ID/Nebula/DS/Net-Agent/Orchestrator/Flow)
      → 重试 2 次 (502/503/504)
      → 统一信封 {success, data, ts, request_id}
```
**状态**: ✅ 通

---

## 3. 概念冲突清单

> 每个冲突是什么、在哪、怎么解决。

| # | 冲突 | 涉及位置 | 严重度 | 建议 |
|:--:|:-----|:---------|:------:|:-----|
| C1 | **"Orchestrator" 指三个不同事物** | 3 个文件 | 🔴 | 强制使用全名，不得简称 |
| C2 | **"EventBus" 有两套实现** | 2 个文件 | 🔴 | 明确 Python(blinker) 和 TS(Redis Streams) 是不同系统 |
| C3 | **Redis Streams 决策 vs 实际代码** | DECISIONS.md vs core/event_bus.py | 🔴 | 决策正确但 Python 未执行，需统一 |
| C4 | **"Agent Graph" 指三件事** | a2a.py vs memory_graph.py vs 不存在 | 🔴 | 明确 A2A Agent Graph = 网络拓扑端点；Memory Graph = 知识图谱 |
| C5 | **"Agent" 有 5 个不同类定义** | 5 个文件 | 🟡 | 明确每个类的职责边界 |
| C6 | **端口号不一致** | 4 个文档 vs docker-compose.yml | 🟡 | 以 docker-compose.yml 为权威 |
| C7 | **DS 端口说 3004，实际 3001→3000** | ARCHITECTURE.md vs docker-compose | 🟡 | 统一为 3001(外部)/3000(内部) |
| C8 | **Grafana 端口说 3000/3005，实际 3005→3000** | 多个文档 | 🟡 | 统一为 3005(外部)/3000(内部) |
| C9 | **Duplicate memory_graph 路由** | gateway/routes/human.py L230+L253 | 🟡 | 删掉一个 |
| C10 | **DS 前端绕过 Gateway** | FulfillModal + ProductAiDialog | 🟡 | 决定：直连 DS 还是统一走 Gateway |
| C11 | **飞书 webhook 调不存在的端点** | nebula/feishu_webhook.py:103 | 🔴 | 改为 /v1/human/chat |
| C12 | **DS doubao 路由调不存在的端点** | DS/api/doubao/route.ts:52 | 🔴 | 同上 |
| C13 | **Feishu Consumer Docker unhealthy** | docker-compose | 🟡 | 排查健康检查配置 |
| C14 | **EventBus 重复文件** | eventbus-init.ts + eventbus-server.ts | 🟢 | 删掉一个 |
| C15 | **微信适配器写了没接** | action_engine/adapters/wechat.py | 🟢 | 决定：接还是删 |

---

## 4. 端口权威表

> **唯一权威来源**。所有文档必须引用此表，不得自行定义端口。

| 服务 | 容器内端口 | 外部端口 | 协议 | docker-compose 位置 |
|:-----|:-----------|:---------|:-----|:-------------------|
| PostgreSQL | 5432 | 5432 | TCP | db |
| Redis | 6379 | 6379 | TCP | redis |
| Alpha-ID | 8000 | 8000 | HTTP | alphaid |
| Nebula | 2002 | 2002 | HTTP | nebula |
| Gateway | 18080 | 18080 | HTTP | gateway |
| Net-Agent | 18180 | 18180 | HTTP | netagent |
| Orchestrator | 19090 | 19090 | HTTP | orchestrator |
| Ghost DS | 3000 | 3001 | HTTP | ghost-ds |
| Flow | 3036 | 3036 | HTTP | flow |
| Feishu Bot | — | — | WebSocket | feishu-bot |
| Feishu Consumer | — | — | Redis Streams | feishu-consumer |
| Prometheus | 9090 | 9090 | HTTP | 仅 override |
| Grafana | 3000 | 3005 | HTTP | 仅 override |
| Caddy | 80/443 | 80/443 | HTTP/3 | 仅 prod |

---

## 5. 修复优先级（P0/P1/P2）

### P0 — 必须立即修复（阻断性问题）

| # | 问题 | 位置 | 影响 |
|:--:|:-----|:-----|:-----|
| P0-1 | 飞书 webhook 调用不存在的 `/v1/chat` | nebula/feishu_webhook.py:103 | 飞书消息处理断裂 |
| P0-2 | DS doubao 路由调用不存在的 `/v1/chat` | DS/api/doubao/route.ts:52 | 豆包采集断裂 |
| P0-3 | Gateway human.py 有重复路由定义 | gateway/routes/human.py L230+L253 | FastAPI 启动报错 |
| P0-4 | Feishu Bot + Consumer Docker unhealthy | docker-compose | 飞书通知不可用 |
| P0-5 | EventBus 重复文件 | DS/src/lib/eventbus-init.ts + eventbus-server.ts | 潜在双注册 |

### P1 — 本周修复（连通性问题）

| # | 问题 | 位置 | 影响 |
|:--:|:-----|:-----|:-----|
| P1-1 | 调用 Redis Streams startConsuming() | DS/feishu-consumer | 事件总线休眠 |
| P1-2 | 飞书凭证硬编码 → 环境变量 | feishu-bot/.env | 安全风险 |
| P1-3 | DS 前端绕过 Gateway 的一致性 | FulfillModal + ProductAiDialog | 租户隔离绕过 |
| P1-4 | Orchestrator 实际状态 vs 文档描述 | orchestrator/main.py | 误导开发 |

### P2 — 两周内（加固 + 完善）

| # | 问题 | 位置 | 影响 |
|:--:|:-----|:-----|:-----|
| P2-1 | Ghost DS 测试覆盖 | DS/ | 0 测试用例 |
| P2-2 | Orchestrator 核心调度实现 | orchestrator/main.py | ToolA/ToolB 为 stub |
| P2-3 | Net-Agent 补充依赖 | net_agent_server/requirements.txt | 缺 cryptography 等 |
| P2-4 | 内容审核中间件 | Gateway | P2 规划 |
| P2-5 | 多租户隔离完善 | 全局 | 单用户先跑通 |

---

## 6. 项目结构（实际代码布局）

```
D:\MW/
├── alphaid/projects/          # Alpha-ID 身份层 (~35K+ 行 Python)
│   └── src/
│       ├── core/              # AgentLoop/TwinBrain/双链记忆/A2A/EventBus(blinker)
│       ├── alpha_id/          # DID/signer/Agent/AgentNetwork/Orchestrator(进程内)
│       ├── auth/              # JWT/CSRF/中间件
│       ├── api/               # REST 路由 (identity/agent/a2a/dual_chain)
│       ├── entrypoints/       # API/MCP/NURO 入口
│       └── tools/             # MCP 工具集
├── ghost-main/                # Gateway + Net-Agent + Feishu Bot
│   ├── gateway/               # 统一API网关 (9路由 + 代理 + 中间件)
│   ├── net_agent_server/      # 路由器管理
│   ├── feishu-bot/            # 飞书机器人 + Redis消费者
│   └── doubao_reader/         # 豆包LevelDB解析器（库，非服务）
├── nebula/                    # 工作流引擎 (7层中间件 + 货源适配器)
├── orchestrator/              # 任务编排服务 (⚠️ 骨架)
├── DS/                        # Ghost DS 电商看板 (Next.js 14 + Prisma)
├── flow/                      # MindFlow 前端门户 (Fastify)
├── docker-compose.yml         # 基础编排 (11 服务)
├── docker-compose.override.yml # 开发环境 (+ Prometheus/Grafana)
├── docker-compose.prod.yml    # 生产环境 (+ Caddy)
└── sql/init/                  # PostgreSQL 初始化脚本
```

---

## 7. 数据流权威定义

### 7.1 认证流

```
用户 → Gateway (:18080)
  → X-Tenant-ID header 或 Authorization: Bearer <JWT>
    → TenantMiddleware 提取 tenant_id
      → 转发到后端 (注入 X-Tenant-ID header)
        → 后端 Prisma/SQLAlchemy 按 tenantId 隔离
```

### 7.2 电商数据流

```
Ghost DS (:3001→3000)
  ├── Prisma → PostgreSQL (业务数据)
  ├── OneBound API → 远程货源 (产品/订单同步)
  ├── Redis Streams → 事件总线 (webhook)
  └── → Gateway (:18080) → Alpha-ID (:8000) (身份/AI)
```

### 7.3 飞书消息流

```
飞书用户 → 飞书开放平台
  ├── 路径A: WebSocket → Feishu Bot → 本地CLI → 回复飞书
  ├── 路径B: WS长轮询 → Nebula → Gateway → Alpha-ID → 回复飞书
  └── 路径C: HTTP回调 → Gateway /webhook → Feishu Bot处理
```

### 7.4 知识流

```
豆包桌面 → Doubao Reader (LevelDB解析)
  → Gateway /v1/doubao/capture
    → Alpha-ID 双链记忆 (PostgreSQL)
    → Obsidian Vault (Markdown文件)
```

---

## 8. 配置权威表

> 唯一权威来源。所有 .env 文件必须与此表一致。

| 服务 | 变量 | 当前值 | 应为值 | 状态 |
|:-----|:-----|:-------|:-------|:-----|
| Gateway | ALPHAID_URL | http://alphaid:8000 | ✅ 正确 | ✅ |
| Gateway | NEBULA_URL | http://nebula:2002 | ✅ 正确 | ✅ |
| Gateway | DS_URL | http://ghost-ds:3000 | ✅ 正确 | ✅ |
| Gateway | NETAGENT_URL | http://netagent:18180 | ✅ 正确 | ✅ |
| Gateway | FLOW_URL | http://flow:3036 | ✅ 正确 | ✅ |
| Gateway | REDIS_URL | redis://redis:6379 | ⚠️ 代码未使用 | ⚠️ |
| DS | DATABASE_URL | postgresql://... | ✅ 正确 | ✅ |
| DS | REDIS_URL | redis://redis:6379 | ✅ 正确 | ✅ |
| DS | PLATFORM_URL | (需检查) | http://localhost:3001 | ⚠️ 待验证 |
| Orchestrator | REDIS_URL | redis://redis:6379 | ⚠️ 代码未使用 | ⚠️ |
| Orchestrator | Dockerfile EXPOSE | (需检查) | 19090 | ⚠️ 待验证 |
| Feishu Bot | 凭证 | .env 硬编码 | 应使用环境变量 | 🔴 |

---

## 9. 死代码/冗余清单

| 项 | 位置 | 大小 | 建议 |
|:--|:-----|:----:|:-----|
| eventbus-server.ts | DS/src/lib/eventbus-server.ts | ~200L | 删（与 eventbus-init.ts 重复） |
| 微信适配器 | alphaid/.../adapters/wechat.py | ~500L | 决定：接还是删 |
| Shoplazta 客户端 | DS/src/lib/shoplazza.ts | ~500L | 用 OneBound 替代，可删 |
| 短剧服务 | (已删) | — | ✅ 已清理 |
| feishu_bot 旧目录 | alphaid/feishu_bot/ | — | ✅ 已清理 |
| flow 双链记忆 TS 版 | flow/.../dual-chain.ts | ~5K | ✅ 已清理 |

---

## 10. 文档权威层级

| 层级 | 文档 | 职责 | 不得做什么 |
|:-----|:-----|:-----|:----------|
| **L1 宪法** | GHOST.md | 项目基调、战略定位、决策、任务清单 | 不得重复架构细节 |
| **L1 宪法** | 1.md.md | 战略来源（七层架构、商业模式） | — |
| **L1 宪法** | 2.md.md | 战略来源（三层堆栈、AtoA 定位） | — |
| **L2 架构** | ARCHITECTURE.md | 七层架构详细设计、服务详解、数据流、认证链 | 不得重复项目基调 |
| **L2 架构** | SYSTEM_MAP.md | 调用链地图、事件流、配置审计、优化路线 | 不得重复架构设计 |
| **L3 状态** | PROJECT_STATUS_REPORT.md | Docker 状态、服务功能度、已知 bug | 不得重复架构/战略 |
| **L3 状态** | WORK_LOG.md | 会话日志、审计发现 | — |
| **L3 状态** | DECISIONS.md | 已确认决策（D-YYYYMMDD-N 格式） | — |
| **L4 参考** | 本文档 (PROJECT_MAP.md) | 术语表、冲突清单、端口表、优先级 | 不得重复以上任何内容 |

> **规则**：L1 引用 L2，L2 引用 L3，L3 引用 L4。不得反向引用。  
> **规则**：修改架构必须改 ARCHITECTURE.md + SYSTEM_MAP.md，不得只改 GHOST.md。  
> **规则**：新术语必须先加入本表 (PROJECT_MAP.md)，才能在其他文档中使用。

---

*本文档是项目唯一权威参考。所有代码、文档、决策必须与此一致。如有冲突，以此为准。*
