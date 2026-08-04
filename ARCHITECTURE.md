# Ghost 架构文档

> Web4.0 AtoA 全域自主智能体操作系统 — 七层架构设计
> **版本 2.0** | **2026-08-04**
> **对应**: GHOST.md v5.0 | 2.md.md | 1.md.md

---

## 1. 架构总览

Ghost 是一个 **Web4.0 AtoA (Agent-to-Anything) 全域自主智能体操作系统**。

### 1.1 三层终极堆栈

```
┌─────────────────────────────────────────────────────────────────┐
│  理念层 (外置大脑)                                                │
│  Denny AI ── 人机共生哲学、智能体行为规范、商业伦理               │
├─────────────────────────────────────────────────────────────────┤
│  系统中枢 (Alpha-ID)                                             │
│  个人终身DID身份 + 双链记忆 + Agent生态 + Skill市场               │
│  github.com/wenwanqing1217/alpha-id (~35K+ 行 Python)            │
├─────────────────────────────────────────────────────────────────┤
│  底层网络 (Ghost AtoA)                                           │
│  Gateway + Nebula + Orchestrator + Net-Agent + Feishu Bot        │
│  + Ghost DS + 监控栈                                             │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 七层系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│  L7 知识协同层                                                    │
│  Obsidian + 飞书多维表格 + Ghost DS 看板                          │
│  知识沉淀 → 团队协同 → 数据可视化                                 │
├─────────────────────────────────────────────────────────────────┤
│  L6 业务展现层                                                    │
│  Ghost DS (Next.js) ── 电商看板 / 订单管理 / 产品管理             │
│  Feishu Bot ── 4合1 入口 (Chat/Execute/Notify/Approve)           │
├─────────────────────────────────────────────────────────────────┤
│  L5 统一网关层                                                    │
│  Gateway (:18080) ── 9 路由模块 + 代理重试 + 统一信封            │
│  /v1/human /v1/agent /v1/internal /v1/net                        │
├─────────────────────────────────────────────────────────────────┤
│  L4 智能调度层                                                    │
│  Orchestrator (:19090) ── 任务编排 + 后台循环                     │
│  Redis Streams ── 事件总线 + 消费者组 + DLQ                       │
├─────────────────────────────────────────────────────────────────┤
│  L3 工作流引擎层                                                  │
│  Nebula (:2002) ── 工作流编排 + 思维导图 + 审批流                 │
│  7 层中间件: 审计 → 限流 → 租户 → 策略 → 缓存 → 日志 → 异常处理  │
├─────────────────────────────────────────────────────────────────┤
│  L2 身份与权限层                                                  │
│  Alpha-ID (:8000) ── DID 身份 + JWT/CSRF + 双链记忆              │
│  Net-Agent (:18180) ── 路由器管理 + JWT + AES-GCM                │
├─────────────────────────────────────────────────────────────────┤
│  L1 感知与接入层                                                  │
│  Docker Compose ── 12 服务统一编排                                │
│  数据采集: 豆包网页版 / 飞书消息 / 路由器 / 开发工具              │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 服务全景图

```
                              用户入口
                    ┌──────────┼──────────┐
                    ▼          ▼          ▼
              Ghost.html   飞书 Bot   桌面 FAIRY
              (A2A+AI)       │      (Tkinter+Ollama)
                    │          │             │
                    └──────────┼────────────┘
                               ▼
                    ┌─────────────────────┐
                    │   Gateway (:18080)   │
                    │ 9 路由 | 代理 | 重试  │
                    └──┬──────┬──────┬────┘
                       │      │      │
          ┌────────────┘      │      └────────────┐
          ▼                   ▼                   ▼
   Alpha-ID (:8000)     Nebula (:2002)     Orchestrator (:19090)
   身份+Agent+记忆       工作流+审批+地图    任务调度+后台循环
          │                   │
          │                   ├──→ Ghost DS (:3004) ← 电商看板
          │                   └──→ MindFlow (:3036) ← 前端门户
          │
          ├──→ Net-Agent (:18180)  ──→ 路由器管理
          ├──→ Feishu Bot          ──→ 飞书 4合1 通道
          └──→ Redis Streams       ──→ 事件总线
                                  
   数据采集层
   ┌──────────────────────────────────────────────────────────┐
   │ 豆包网页版 ──(Chrome扩展)──→ Gateway                       │
   │ 飞书消息   ──(WebSocket)──→ Feishu Bot → Gateway           │
   │ 路由器     ──(HTTP)──────→ Net-Agent                      │
   │ 开发工具   ──(HTTP)──────→ Gateway                         │
   └──────────────────────────────────────────────────────────┘
```

---

## 2. 服务详细设计

### 2.1 Alpha-ID (:8000) — 身份与智能体核心

**职责**: 个人终身DID身份 + Agent对话 + 双链记忆 + 社交恢复

**技术栈**: FastAPI + SQLite/PostgreSQL + JWT + AES-256-GCM + PyNaCl (Ed25519)

**核心模块** (~35K+ 行 Python):

| 模块 | 文件 | 行数 | 职责 |
|:-----|:-----|:----:|:-----|
| Agent Loop | `core/agent.py` | ~8K | ReAct 循环，工具调用 |
| TwinBrain | `core/twin_brain.py` | ~6K | 本地+云端双大脑 |
| 双链记忆 | `core/memory/` | ~10K | 显式记忆(语义) + 隐式记忆(情景) |
| A2A 协议 | `core/a2a.py` | ~8K | Agent-to-Agent 通信 + 发现 |
| 存储引擎 | `core/storage.py` | ~5K | 多后端存储 (SQLite/JSON/Async) |
| 认证模块 | `auth/` | ~4K | JWT + CSRF + 中间件 |

**端口**: 8000 | **状态**: ✅ 生产可用 | **测试**: 839+ 用例全绿

### 2.2 Gateway (:18080) — 统一API网关

**职责**: 三层路由 (Human/Agent/Internal) + 代理重试 + 统一信封格式

**技术栈**: FastAPI + httpx + Redis + OpenTelemetry

**9 个路由模块**:

| 路由 | 路径 | 后端 | 功能 |
|:-----|:-----|:-----|:-----|
| Human | `/v1/human/*` | Alpha-ID | 人类用户对话 |
| Agent | `/v1/agent/*` | Alpha-ID | 智能体调用 |
| Internal | `/v1/internal/*` | Alpha-ID | 内部服务通信 |
| Net | `/v1/net/*` | Net-Agent | 路由器管理代理 |
| Webhook | `/webhook/*` | Feishu Bot | 飞书回调 |
| Sync | `/api/sync/*` | DS / Nebula | 数据同步 |
| Cron | `/api/cron/*` | DS | 定时任务 |
| Orders | `/api/orders/*` | DS | 订单管理 |
| Products | `/api/products/*` | DS | 产品管理 |

**代理特性**:
- httpx 异步客户端 + 连接池
- 自动重试 (exponential backoff)
- 请求/响应日志记录
- 统一错误响应格式

**端口**: 18080 | **状态**: ✅ 生产可用 | **测试**: 22 用例全绿

### 2.3 Nebula (:2002) — 工作流引擎

**职责**: 工作流编排 + 思维导图生成 + 任务执行 + 审批流

**技术栈**: FastAPI + PostgreSQL + Prisma + 7层中间件

**7层中间件栈**:

| 层级 | 中间件 | 功能 |
|:-----|:-------|:-----|
| L1 | AuditMiddleware | 全链路审计日志 |
| L2 | RateLimitMiddleware | IP + 租户级限流 |
| L3 | TenantMiddleware | 租户上下文注入 |
| L4 | PolicyMiddleware | 策略引擎 (RBAC/ABAC) |
| L5 | CacheMiddleware | 响应缓存 + ETag |
| L6 | LoggingMiddleware | 结构化日志 |
| L7 | ExceptionMiddleware | 统一异常处理 |

**适配器**:
- Shoplazza 电商适配器 (产品/订单/库存同步)
- 1688 货源适配器
- 工作流模板引擎 (YAML 定义)

**端口**: 2002 | **状态**: ✅ 生产可用 | **测试**: 153 用例全绿

### 2.4 Orchestrator (:19090) — 任务调度

**职责**: 全局任务队列 + 失败重试 + 死信处理 + 定时任务

**技术栈**: FastAPI + Redis Streams + asyncio

**核心组件**:

| 组件 | 职责 |
|:-----|:-----|
| TaskQueue | Redis Streams 队列，消费者组模式 |
| DeadLetterQueue | 失败任务兜底，人工介入 |
| Scheduler | 定时任务，cron 表达式 |
| EventBus | 内部事件分发 (Redis Pub/Sub) |

**当前状态**: ⚠️ 骨架已完成，核心调度逻辑待实现

**端口**: 19090 | **状态**: ⚠️ 20% | **Docker**: ✅ 运行中

### 2.5 Ghost DS (:3004) — 电商数据看板

**职责**: Shoplazza 店铺数据管理 (产品/订单/库存/同步)

**技术栈**: Next.js 14 + Prisma + PostgreSQL + Redis + Tailwind CSS

**数据模型** (Prisma):

```
┌──────────┐     ┌───────────┐     ┌──────────┐     ┌─────────────┐
│   Shop   │────▶│  Product  │────▶│   Order  │────▶│  Fulfillment │
│ tenantId │     │ tenantId  │     │ tenantId │     │  (内联)     │
│ storeMode│     │ shopId    │     │ shopId   │     │ status      │
│ shopId   │     │ title     │     │ productId│     │ tracking    │
│ name     │     │ price     │     │ total    │     │             │
│ platform │     │ inventory │     │ status   │     └─────────────┘
└──────────┘     │ sku       │     │ customer │
                 │ variants  │     │ items    │
                 │ status    │     │ createdAt│
                 └───────────┘     └──────────┘
                                     ▲
                                     │
                              ┌─────────────┐
                              │   SyncLog   │
                              │ tenantId    │
                              │ resource    │
                              │ action      │
                              │ status      │
                              │ startedAt   │
                              │ completedAt │
                              └─────────────┘
```

**API 路由**:

| 路由 | 方法 | 功能 |
|:-----|:-----|:-----|
| `/api/shop` | GET/POST | 店铺注册/列表 |
| `/api/products` | GET/POST/PUT/DELETE | 产品 CRUD |
| `/api/orders` | GET | 订单列表 |
| `/api/orders/[id]/fulfill` | POST | 订单履约 |
| `/api/sync` | POST | 触发数据同步 |
| `/api/cron/sync` | POST | 定时同步 (Vercel Cron) |
| `/api/stats` | GET | 统计看板 |
| `/api/health` | GET | 健康检查 |

**端口**: 3004 | **状态**: ✅ 90% | **功能度**: 高

### 2.6 Net-Agent (:18180) — 路由器管理

**职责**: 多品牌路由器远程管理 (OpenWrt/小米/TP-Link)

**技术栈**: FastAPI + SQLite + JWT + AES-GCM + requests

**核心功能**:

| 功能 | 端点 | 说明 |
|:-----|:-----|:-----|
| 设备管理 | `/api/devices` | 路由器注册/列表/删除 |
| 在线状态 | `/api/devices/{id}/status` | 实时在线检测 |
| 配置管理 | `/api/devices/{id}/config` | 获取/修改路由器配置 |
| 命令执行 | `/api/devices/{id}/command` | 远程执行命令 |
| 流量监控 | `/api/devices/{id}/traffic` | 带宽使用统计 |
| 认证 | `/api/auth/*` | JWT + AES-GCM 加密 |

**安全特性**:
- JWT 令牌认证
- AES-GCM 加密敏感配置
- 设备指纹验证
- IP 白名单

**端口**: 18180 | **状态**: ✅ 60% | **Docker**: ✅ 运行中

### 2.7 Feishu Bot — 飞书集成

**职责**: 飞书双通道机器人 (WebSocket + HTTP 轮询)，4合1 功能

**技术栈**: Python + WebSocket + HTTP + 飞书开放平台 API

**4合1 功能**:

| 模式 | 说明 | 端点 |
|:-----|:-----|:-----|
| Chat | 普通对话，提取工作上下文 | `/webhook/feishu` |
| Execute | 执行代码/工具任务 | `/webhook/feishu/execute` |
| Notify | 主动推送通知 | `/webhook/feishu/notify` |
| Approve | 审批确认 | `/webhook/feishu/approve` |

**双通道**:
- **WebSocket** (首选): 实时消息推送
- **HTTP 长轮询** (备选): 兼容旧版飞书

**端口**: 通过 Gateway :18080 暴露 | **状态**: ✅ 80% | **Docker**: ⚠️ Unhealthy

### 2.8 Redis Streams — 事件总线

**职责**: 服务间异步通信 + 事件持久化 + 消费者组 + 死信队列

**技术栈**: Redis 7.x + Redis Streams + Consumer Groups

**事件拓扑**:

```
生产端                          消费端
─────────                      ─────────
DS 服务                         Orchestrator
├── product.created    ──────▶  │ 自动铺货任务
├── order.created      ──────▶  │ 订单履约任务
├── sync.completed     ──────▶  │ 数据同步任务
└── sync.failed        ──────▶  │ 告警通知

Nebula 服务
├── workflow.completed ──────▶  │ 工作流结果处理
└── approval.requested ──────▶  │ 飞书审批通知

Feishu Bot
├── message.received   ──────▶  │ 工作上下文提取
└── command.executed   ──────▶  │ 任务结果回复
```

**消费者组**:

| 组名 | 消费者 | 处理内容 |
|:-----|:-------|:---------|
| `orchestrator` | Orchestrator | 任务执行 |
| `notification` | Feishu Bot | 通知推送 |
| `analytics` | DS | 数据统计 |
| `dlq` | 人工处理 | 死信兜底 |

**当前状态**: ⚠️ 架构已定义，`startConsuming()` 未被任何服务调用，事件总线处于休眠状态

---

## 3. 数据流

### 3.1 电商核心链路: 浏览商品

```
用户浏览器
    │
    ▼
Ghost DS (:3004) ── Next.js 前端
    │
    ├── GET /api/products
    │       │
    │       ▼
    │   Prisma → PostgreSQL
    │   SELECT * FROM products WHERE tenantId = ?
    │       │
    │       ▼
    │   JSON 响应 (产品列表)
    │       │
    ▼       ▼
渲染页面    显示产品卡片 (图片/价格/库存)
```

### 3.2 电商核心链路: 同步店铺数据

```
Ghost DS (:3004)
    │
    ├── POST /api/sync
    │       │
    │       ▼
    │   调用 Nebula (:2002) Shoplazza 适配器
    │       │
    │       ├── GET /shoplazza/products → 拉取远程产品
    │       ├── GET /shoplazza/orders  → 拉取远程订单
    │       │
    │       ▼
    │   Prisma 批量 upsert
    │       │
    │       ▼
    │   ┌─────────────┐
    │   │   SyncLog   │ ← 记录同步结果
    │   └─────────────┘
    │       │
    │       ▼
    │   JSON 响应 (同步结果)
    ▼
前端显示同步状态
```

### 3.3 电商核心链路: 订单履约

```
用户 (商家)
    │
    ▼
Ghost DS (:3004) ── FulfillModal
    │
    ├── POST /api/orders/[id]/fulfill
    │       │
    │       ▼
    │   调用 Nebula (:2002) 履约引擎
    │       │
    │       ├── 验证订单状态
    │       ├── 扣减库存
    │       ├── 生成物流单
    │       └── 更新订单状态 → "fulfilled"
    │       │
    │       ▼
    │   Prisma update Order
    │       │
    │       ▼
    │   ┌─────────────┐
    │   │ Fulfillment │ ← 内联记录
    │   └─────────────┘
    │       │
    │       ▼
    │   JSON 响应 (履约结果)
    ▼
前端显示成功 + 物流信息
```

### 3.4 电商核心链路: 店铺接入

```
用户 (商家)
    │
    ▼
Ghost DS (:3004) ── Settings 页面
    │
    ├── POST /api/shop
    │       │
    │       ▼
    │   Prisma create Shop (tenantId + storeMode + shopId)
    │       │
    │       ▼
    │   ┌─────────────────────────────────┐
    │   │ shopId 用于后续所有 API 调用    │
    │   │ storeMode: marketplace|independent │
    │   │ platform: shoplazza|shopify|... │
    │   └─────────────────────────────────┘
    │       │
    │       ▼
    │   JSON 响应 (Shop 配置)
    ▼
前端显示店铺列表
```

### 3.5 AI 链路: AI 文案生成

```
用户 (商家)
    │
    ▼
Ghost DS (:3004) ── ProductAiDialog
    │
    ├── 调用 AI 生成文案
    │       │
    │       ▼
    │   Gateway (:18080) ── /v1/agent/*
    │       │
    │       ▼
    │   Alpha-ID (:8000) ── Agent Loop
    │       │
    │       ├── 加载产品信息 (Prisma)
    │       ├── 构建 prompt
    │       ├── 调用 LLM (OpenAI/DeepSeek/...)
    │       └── 返回 AI 生成内容
    │       │
    ▼       ▼
前端显示 AI 文案 (标题/描述/卖点)
```

### 3.6 通知链路: 飞书消息处理

```
飞书用户
    │
    ▼
飞书开放平台
    │
    ├── WebSocket 事件 / HTTP 回调
    │       │
    │       ▼
    │   Gateway (:18080) ── /webhook/shoplazza
    │       │
    │       ▼
    │   Feishu Bot 服务
    │       │
    │       ├── 解析消息内容
    │       ├── 判断模式 (Chat/Execute/Notify/Approve)
    │       │
    │       ├── [Chat] → 提取工作上下文 → Gateway → Alpha-ID
    │       ├── [Execute] → 执行工具 → 返回结果
    │       ├── [Notify] → 推送通知到飞书
    │       └── [Approve] → 审批确认 → 更新状态
    │       │
    ▼       ▼
飞书用户收到响应 / 状态更新
```

---

## 4. 认证与身份链

### 4.1 全链路认证流程

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  用户    │────▶│ Gateway  │────▶│ Alpha-ID │────▶│ SQLite   │
│ (浏览器) │     │ (:18080) │     │ (:8000)  │     │ / PostgreSQL│
└──────────┘     └──────────┘     └──────────┘     └──────────┘
     │                │                  │
     │  1. 登录请求    │                  │
     │───────────────▶│                  │
     │                │ 2. 转发认证请求   │
     │                │─────────────────▶│
     │                │                  │ 3. 验证凭据
     │                │                  │ 4. 生成 JWT
     │                │◀─────────────────│
     │  5. 返回 JWT   │                  │
     │◀───────────────│                  │
     │                │                  │
     │  6. API 请求 + JWT                 │
     │─────────────────▶│                  │
     │                │ 7. 验证 JWT       │
     │                │ 8. 注入租户上下文  │
     │                │ 9. 转发到后端      │
     │                │─────────────────▶│
```

### 4.2 认证机制

| 服务 | 认证方式 | 说明 |
|:-----|:---------|:-----|
| Alpha-ID | JWT (HS256) + HKDF-SHA256 | 密钥派生，双链记忆加密 |
| Gateway | 透传 JWT | 不验证，只转发到 Alpha-ID |
| Net-Agent | JWT + AES-GCM | 设备配置加密传输 |
| Feishu Bot | 飞书签名验证 | HMAC-SHA256 验证回调 |
| Nebula | 租户上下文 | 从 JWT 提取 tenantId |

---

## 5. 端口分配

| 服务 | 端口 | 协议 | 状态 | 说明 |
|:-----|:-----|:-----|:-----|:-----|
| Alpha-ID | 8000 | HTTP | ✅ 运行 | 身份 + 双链记忆 + Agent |
| Gateway | 18080 | HTTP | ✅ 运行 | 统一网关 + 9 路由 |
| Nebula | 2002 | HTTP | ✅ 运行 | 工作流 + 审批 + 地图 |
| Orchestrator | 19090 | HTTP | ⚠️ 骨架 | 任务调度 |
| Net-Agent | 18180 | HTTP | ✅ 运行 | 路由器管理 |
| Ghost DS | 3004 | HTTP | ✅ 运行 | 电商看板 |
| MindFlow | 3036 | HTTP | ✅ 运行 | 前端门户 |
| Feishu Bot | - | WebSocket | ⚠️ 通过 GW | 通过 Gateway 暴露 |
| PostgreSQL | 5432 | TCP | ✅ 运行 | 主数据库 |
| Redis | 6379 | TCP | ✅ 运行 | 缓存 + 事件总线 |
| Ollama | 11434 | HTTP | 可选 | 本地 AI 推理 |

> ⚠️ Windows 端口排除范围 2936-3035，MindFlow 使用 3036 避免冲突。

---

## 6. 环境变量配置

### 6.1 Gateway

```bash
ALPHAID_URL=http://alphaid:8000
NEBULA_URL=http://nebula:2002
NET_AGENT_URL=http://net-agent:18180
GATEWAY_PORT=18080
REDIS_URL=redis://redis:6379
```

### 6.2 Alpha-ID

```bash
AUTH_MASTER_KEY=<your-master-key>
OPENAI_API_KEY=<your-openai-key>
DATABASE_URL=postgresql://user:pass@postgres:5432/alphaid
REDIS_URL=redis://redis:6379
```

### 6.3 Orchestrator

```bash
REDIS_URL=redis://redis:6379
ALPHAID_URL=http://alphaid:8000
NEBULA_URL=http://nebula:2002
OBSIDIAN_VAULT=<path-to-obsidian-vault>
FEISHU_APP_ID=<feishu-app-id>
FEISHU_APP_SECRET=<feishu-app-secret>
GITHUB_TOKEN=<github-api-token>
```

### 6.4 Ghost DS

```bash
DATABASE_URL=postgresql://user:pass@postgres:5432/ghost_ds
REDIS_URL=redis://redis:6379
NEXT_PUBLIC_API_URL=http://localhost:3004/api
PLATFORM_URL=http://localhost:3004
SHOPLAZZA_API_KEY=<your-api-key>
```

### 6.5 MindFlow

```bash
PORT=3036
HOST=127.0.0.1
GATEWAY_URL=http://localhost:18080
```

---

## 7. 测试策略

### 7.1 测试分布

| 服务 | 测试文件数 | 测试用例数 | 状态 |
|:-----|:-----------|:-----------|:-----|
| Alpha-ID | 30+ | 839+ | ✅ 全绿 |
| Gateway | 3 | 22 | ✅ 全绿 |
| Nebula | - | 153 | ✅ 全绿 |
| Ghost DS | 0 | 0 | ⚠️ 待建设 |
| Orchestrator | 0 | 0 | ⚠️ 待建设 |

### 7.2 测试类型

- **单元测试**: 纯函数、边界条件、属性测试 (Hypothesis)
- **集成测试**: 模块间交互、完整链路
- **E2E 测试**: API 端到端、社交恢复流程
- **契约测试**: API 接口契约验证

---

## 8. 安全设计

### 8.1 安全原则

- **零信任**: 默认拒绝，显式允许
- **CORS**: 生产环境拒绝 wildcard
- **限流**: 按 IP + 租户限流，滑动窗口
- **关联 ID**: 全链路追踪
- **加密**: AES-256-GCM 隐私数据加密
- **社交恢复**: 见证人机制 + 时间锁

### 8.2 已知安全问题

| 级别 | 问题 | 说明 |
|:-----|:-----|:-----|
| 🔴 D | 默认密码硬编码 | docker-compose.yml 中 ghost_secret 默认密码 |
| 🔴 D | A2A 签名降级 | PyNaCl 不可用时降级 HMAC-SHA256 |
| 🔴 D | Ed25519 密钥降级 | 无 PyNaCl 时 sha256(priv) 非有效公钥 |
| 🟡 C | JsonStorage 无线程安全 | 多线程读写 JSON 文件可能损坏 |
| 🟡 C | MemoryStore 路径遍历 | alpha_id 直接拼接路径 |
| 🟡 C | bare except 吞异常 | 5 处 except Exception: pass |

---

## 9. 项目结构

```
D:\MW/
├── alphaid/projects/          # Alpha-ID 身份层 (~35K+ 行 Python)
│   ├── src/
│   │   ├── core/              # AgentLoop/TwinBrain/双链记忆/A2A/事件总线
│   │   ├── auth/              # JWT/CSRF/中间件
│   │   ├── api/               # REST 路由
│   │   ├── entrypoints/       # API/MCP/NURO 入口
│   │   └── tools/             # MCP 工具集
│   └── tests/                 # 839+ 测试用例
├── ghost-main/                # Gateway + Net-Agent + 飞书Bot
│   ├── gateway/               # 统一API网关
│   │   ├── routes/            # 9 个路由模块
│   │   ├── services/          # 代理服务
│   │   └── middleware/        # 中间件
│   ├── net_agent_server/      # 路由器管理服务
│   └── feishu-bot/            # 飞书机器人
├── nebula/                    # 工作流引擎
│   ├── src/mindflow_map/      # FastAPI 服务
│   │   ├── routes/            # 7 个路由模块
│   │   ├── middleware/        # 7 层中间件
│   │   └── models/            # Prisma 模型
│   └── pyproject.toml         # 依赖管理
├── orchestrator/              # 任务调度服务 (骨架阶段)
│   ├── app.py                 # FastAPI 主应用
│   └── requirements.txt       # 依赖
├── DS/                        # Ghost DS 电商看板
│   ├── src/
│   │   ├── app/               # Next.js 14 App Router
│   │   │   ├── api/           # API 路由
│   │   │   ├── orders/        # 订单页面
│   │   │   ├── products/      # 产品页面
│   │   │   ├── settings/      # 设置页面
│   │   │   └── page.tsx       # 首页
│   │   ├── components/        # React 组件
│   │   └── lib/               # 工具函数
│   └── prisma/                # Prisma Schema + 迁移
├── docker-compose.yml         # 基础服务定义
├── docker-compose.override.yml # 开发环境覆盖
└── docker-compose.prod.yml    # 生产环境配置
```

---

*最后更新: 2026-08-04*
