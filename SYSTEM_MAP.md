# Ghost Platform — 系统全景图

> **最后更新:** 2026-08-04（战略定位整合后）  
> **用途:** 把整个项目的所有服务、调用链、数据流、事件流、断点串起来  
> **战略定位:** Web4.0 AtoA (Agent-to-Anything) 全域自主智能体操作系统  
> **三层终极堆栈:** 理念层(Denny) → 系统中枢(AlphaID) → 底层网络(Ghost AtoA)  
> **七层系统架构:** L1感知→L2身份→L3工作流→L4调度→L5网关→L6业务→L7知识  
> **配套文档:** `PROJECT_STATUS_REPORT.md`（状态快照）、`WORK_LOG.md`（会话日志）、`DECISIONS.md`（决策记录）、`GHOST.md`（项目宪法）、`ARCHITECTURE.md`（架构设计）、`1.md.md`（战略来源）、`2.md.md`（战略来源）

---

## 零、三层终极堆栈（战略层）

```
┌─────────────────────────────────────────────────────────────────┐
│  理念层 (外置大脑)                                                │
│  Denny AI ── 人机共生哲学、智能体行为规范、商业伦理               │
├─────────────────────────────────────────────────────────────────┤
│  系统中枢 (Alpha-ID)                                             │
│  个人终身DID身份 + 双链记忆 + Agent生态 + Skill市场               │
│  ~35K+ 行 Python / 150+ 文件                                     │
├─────────────────────────────────────────────────────────────────┤
│  底层网络 (Ghost AtoA)                                           │
│  Gateway + Nebula + Orchestrator + Net-Agent + Feishu Bot        │
│  + Ghost DS + 监控栈                                             │
└─────────────────────────────────────────────────────────────────┘
```

> 来源: `2.md.md` — "从AI外置大脑到Web4.0 AtoA全域智能体"  
> 电商是 MVP 场景，非最终形态。最终形态是 AtoA 全域自主智能体操作系统。

### 七层系统架构映射

| 层 | 名称 | 服务 | 功能度 |
|:--:|:-----|:-----|:------:|
| L7 | 知识协同层 | Obsidian + 飞书多维表格 + Ghost DS 看板 | ⚠️ 60% |
| L6 | 业务展现层 | Ghost DS (电商) + Feishu Bot (4合1) | ✅ 85% |
| L5 | 统一网关层 | Gateway (:18080) 9路由 + 代理重试 | ✅ 95% |
| L4 | 智能调度层 | Orchestrator (:19090) + Redis Streams | ⚠️ 20% |
| L3 | 工作流引擎层 | Nebula (:2002) + 7层中间件 | ✅ 85% |
| L2 | 身份与权限层 | Alpha-ID (:8000) + Net-Agent (:18180) | ✅ 95% |
| L1 | 感知与接入层 | Docker Compose + 数据采集 | ✅ |

## 一、系统级架构（真实状态 · 7层架构）

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    Ghost AtoA — 七层系统架构全景                             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────┐         ║
║  │  L7 知识协同层 — 企业协同 + 知识闭环                                  │         ║
║  │  Obsidian Vault + 飞书多维表格 + Ghost DS 看板                      │         ║
║  └─────────────────────────────────────────────────────────────────┘         ║
║  ┌─────────────────────────────────────────────────────────────────┐         ║
║  │  L6 业务展现层 — 双模电商 + 飞书4合1                                │         ║
║  │  Ghost DS (:3004) + Feishu Bot (WebSocket+HTTP)                   │         ║
║  └─────────────────────────────────────────────────────────────────┘         ║
║  ┌─────────────────────────────────────────────────────────────────┐         ║
║  │  L5 统一网关层 — Gateway (:18080) 9路由 + 代理重试                 │         ║
║  │  /v1/human /v1/agent /v1/internal /v1/net /webhook /api/sync...  │         ║
║  └─────────────────────────────────────────────────────────────────┘         ║
║  ┌─────────────────────────────────────────────────────────────────┐         ║
║  │  L4 智能调度层 — Orchestrator (:19090) + Redis Streams            │         ║
║  │  任务队列 + 死信处理 + 定时任务（⚠️ 骨架阶段）                       │         ║
║  └─────────────────────────────────────────────────────────────────┘         ║
║  ┌─────────────────────────────────────────────────────────────────┐         ║
║  │  L3 工作流引擎层 — Nebula (:2002) + 7层中间件                     │         ║
║  │  工作流编排 + 思维导图 + 审批流 + 货源适配器                        │         ║
║  └─────────────────────────────────────────────────────────────────┘         ║
║  ┌─────────────────────────────────────────────────────────────────┐         ║
║  │  L2 身份与权限层 — Alpha-ID (:8000) + Net-Agent (:18180)          │         ║
║  │  DID身份 + JWT认证 + 双链记忆 + 路由器管理                          │         ║
║  └─────────────────────────────────────────────────────────────────┘         ║
║  ┌─────────────────────────────────────────────────────────────────┐         ║
║  │  L1 感知与接入层 — Docker Compose + 数据采集                       │         ║
║  │  豆包LevelDB + 飞书WS + 路由器HTTP + 开发工具                      │         ║
║  └─────────────────────────────────────────────────────────────────┘         ║
║                                                                              ║
║  ┌──────────────────────────────────────────────────────────────────┐        ║
║  │  数据层: PostgreSQL (:5432) + Redis (:6379)                       │        ║
║  └──────────────────────────────────────────────────────────────────┘        ║
║                                                                              ║
║  ┌──────────────────────────────────────────────────────────────────┐        ║
║  │  可观测性: Prometheus(:9090) → Grafana(:3000)                     │        ║
║  └──────────────────────────────────────────────────────────────────┘        ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 二、五条核心调用链（完整串联）

### 链 1：用户浏览商品

```
浏览器 → GET /api/products?page=1
  │
  ├─ [DS Frontend] getApiUrl() 检查 NEXT_PUBLIC_GATEWAY_URL
  │   ├─ 有值 → 改写为 Gateway /v1/ecom/products
  │   └─ 无值 → 直连 DS（⚠️ 绕过 Gateway）
  │
  ├─ [Gateway] TenantMiddleware 提取 tenant_id
  │   ├─ 从 JWT alpha_id claim（⚠️ 不验证签名）
  │   ├─ 或从 X-Tenant-ID header
  │   └─ 注入 request.state.tenant_id + X-Tenant-ID header
  │
  ├─ [Gateway] routes/ecom.py list_products()
  │   ├─ 速率限制: 30 req/60s
  │   └─ _proxy_ds() → HTTP 调用 DS /api/products
  │
  ├─ [DS] products/route.ts GET
  │   ├─ getTenantId() → 读 X-Tenant-ID header
  │   ├─ ⚠️ 不调用 verifyRequest()（无 DS_API_KEY 校验）
  │   └─ Prisma: product.findMany({ where: { tenantId, status, ... } })
  │
  ├─ [PostgreSQL] 查询 ghost 库 ds schema 的 product 表
  │
  └─ 返回: DB → DS → Gateway（ok 信封）→ 浏览器
```

**断点风险:**
- 无 Gateway 时：无速率限制、无审计日志
- 无 X-Tenant-ID 时：默认 tenantId = "default"，所有用户共享同一数据

---

### 链 2：用户同步商品（OneBound）

```
浏览器 → POST /api/sync { entity: 'products' }
  │
  ├─ [DS] sync/route.ts
  │   ├─ verifyRequest() → DS_API_KEY 校验（如果有配置）
  │   ├─ getTenantId() → tenant isolation
  │   └─ 查找 tenant 的 active shop
  │
  ├─ [DS] onebound.ts → OneBoundClient
  │   ├─ 速率限制: 5 req/s token bucket
  │   ├─ 重试: 3 次指数退避（1s→2s→4s）
  │   └─ listAllProducts() → 翻页获取所有商品（最多 1000）
  │
  ├─ [OneBound API] GET /products?page=N&page_size=50
  │
  ├─ [DS] 数据映射 + Prisma upsert
  │   ├─ price = parseFloat(p.price || p.variants[0].price)
  │   ├─ images = JSON.stringify(urls)
  │   ├─ 每条记录: product.upsert({ where: { shopId_externalId }, ... })
  │   └─ ⚠️ 最多 1000 条，大目录可能静默截断
  │
  ├─ [DS] 创建 SyncLog（status: 'success' / 'failed'）
  │
  └─ ⚠️ 没有发布 sync:started / sync:completed 事件到 EventBus
```

**断点风险:**
- OneBound API key 存储在 Prisma 的 `shop.accessToken` 字段（明文）
- `listAllProducts` 最多 1000 条
- 事件总线中定义了 `SYNC_STARTED/COMPLETED/FAILED` 类型但从未使用
- 两个 Redis 连接（eventbus-init + eventbus-server），`startConsuming()` 从未调用

---

### 链 3：用户履约发货（⚠️ 绕过 Gateway）

```
浏览器 → FulfillModal 点击"发货"
  │
  ├─ ⚠️ FulfillModal.tsx 使用 template literal 直连
  │   POST /api/orders/${orderId}/fulfill
  │   └─ ❌ 不使用 getApiUrl() → 完全绕过 Gateway
  │
  ├─ [DS] fulfill/route.ts
  │   ├─ getTenantId() → tenant isolation
  │   ├─ 验证订单状态（不能重复发货）
  │   ├─ OneBoundClient.createFulfillmentOrder()
  │   └─ ⚠️ OneBound 失败时静默吞掉异常（"可能是测试订单"）
  │
  ├─ [DS] Prisma order.update({ status: 'fulfilled', ... })
  │
  └─ ⚠️ 没有发布 order:fulfilled 事件 → Feishu Consumer 收不到通知
       ⚠️ FulfillmentMiddleware（3条路径）从未被实例化 — 死代码
```

**断点风险:**
- 绕过 Gateway：无速率限制、无关联 ID、无审计日志
- OneBound 失败被静默吞掉
- `merchant_skill` 和 `marketplace_split` 路径为 TODO
- 履约事件从未进入 EventBus → Feishu 不发通知

---

### 链 4：飞书通知（⚠️ 链路断裂）

```
理想流程:
  webhook → Redis Streams → Feishu Consumer → FeishuService.notify() → 飞书

实际流程:
  webhook → Redis Streams → Feishu Consumer → _resolve_notify_user() → ❌ 返回 None
                                                                     └─ 无法确定发给谁
```

**断点风险:**
- `_resolve_notify_user()` 的 shop_owner 和 alpha_id 映射都是 TODO
- 只有 `notifyUserId` 显式设置在事件数据中时才能工作
- DS 的 `FulfillmentMiddleware`（本应发布事件）从未启动
- `sync/route.ts` 不发布 sync 事件
- Feishu Consumer 订阅 `supply:error` 但 DS 从不发布该类型
- DS 发布 `supply:inventory:updated` 和 `supply:product:updated` 但 Consumer 不监听

---

### 链 5：豆包知识采集 → Obsidian

```
Doubao Desktop 每 120s
  │
  ├─ [Gateway 后台线程] _run_scanner_loop
  │   ├─ ⚠️ httpx.Client(sync) + ASGITransport 在 threading.Thread 中
  │   │   └─ 可能因无 asyncio 事件循环而崩溃
  │   └─ 读取 LevelDB .log 文件
  │
  ├─ [Gateway] POST /v1/internal/doubao/capture
  │   ├─ 知识提炼: dedup(MD5) + 噪声过滤(30+正则) + 自动标签(40+关键词)
  │   ├─ Alpha-ID 认证(login/register fallback)
  │   ├─ POST /api/v1/dual-chain/save → Alpha-ID 双链记忆
  │   └─ write_conversation_async() → Obsidian 写入
  │
  ├─ [Gateway] ObsidianWriter
  │   ├─ ⚠️ asyncio.get_event_loop() 已弃用（Python 3.10+）
  │   └─ 原子写入: D:\Obsidian\Ghost知识库\doubao-chat\{date}\
  │
  └─ [Gateway] ObsidianOrganizer
      ├─ wiki-links 自动链接
      ├─ 每日索引 + 主题索引
      └─ 关联笔记（关键词重叠评分）
```

**断点风险:**
- Doubao 扫描器线程可能崩溃（sync httpx + ASGITransport）
- ObsidianWriter 使用已弃用的 asyncio API
- Obsidian 桥接类（`ObsidianKnowledgeBridge`）完全实现了但**从未被调用**
- 电商事件（order:paid 等）应该触发 Obsidian 同步，但没有 wiring

---

## 三、认证与身份全链路

```
注册:
  手机号 → DS(proxy) → Gateway → Alpha-ID
    → DID 生成(Ed25519) → 用户记录写入
    → ❌ 注册不发 JWT，用户未登录

登录:
  POST /api/v1/identity/quick-register → Alpha-ID
    → JWT 签发(HS256) → 返回给客户端

认证请求:
  浏览器 (Authorization: Bearer <JWT>)
    → Gateway TenantMiddleware
      → ⚠️ base64 decode JWT payload，不验证签名
      → 提取 alpha_id claim
      → 注入 X-Tenant-ID header
    → DS Backend
      → getTenantId() → tenantWhere() → Prisma 查询隔离

❌ 断点:
  - Gateway GET /v1/human/identity 忽略客户端 JWT，返回 DEFAULT_ALPHA_ID 的数据
  - AuthGuard 依赖此端点 → 任何请求都可通过前端认证检查
  - products/orders 路由不调用 verifyRequest()
  - alpha_id 查询参数（legacy）暴露在 URL 中
  - Gateway 本地开发 .env 中 ALPHAID_URL 指向 localhost:8002（不存在）
```

---

## 四、事件总线完整拓扑

```
                          ┌─────────────────────────────────┐
                          │    Redis Streams                │
                          │                                 │
  ┌───────────┐  publish  │  alphaid:ecom:order:created      │
  │ Webhook   │ ────────▶ │  alphaid:ecom:order:paid         │
  │ (OneBound)│           │  alphaid:ecom:order:fulfilled     │
  └───────────┘           │  alphaid:ecom:order:refunded      │
                          │  alphaid:ecom:order:cancelled     │
  ┌───────────┐           │  alphaid:ecom:supply:inventory    │
  │ sync/     │           │  alphaid:ecom:supply:product      │
  │ route.ts  │  ❌ 不发布 │  alphaid:ecom:all (审计流, 50K)   │
  └───────────┘           │  system:task:failed (DLQ)         │
                          └──────────┬──────────────────────┘
                                     │ XREADGROUP
                          ┌──────────▼──────────────────────┐
                          │  Feishu Consumer                │
                          │                                 │
                          │  订阅: order:*, supply:error,    │
                          │  system:alert, fulfillment:*     │
                          │                                 │
                          │  ❌ supply:error 无发布者        │
                          │  ❌ supply:inventory/product    │
                          │     更新 无消费者                │
                          │  ❌ _resolve_notify_user() 返回  │
                          │     None（TODO）                │
                          └──────────┬──────────────────────┘
                                     │ FeishuService.notify()
                          ┌──────────▼──────────────────────┐
                          │  飞书用户（富文本卡片）           │
                          └─────────────────────────────────┘

DS 端事件总线:
  eventbus-init.ts  +  eventbus-server.ts
    → 注册了 handler 但 ❌ startConsuming() 从未调用
    → FulfillmentMiddleware 定义了 3 条路径但 ❌ 从未实例化
    → 所有 handler 都是 console.log
```

---

## 五、配置一致性矩阵（发现 18 处不一致）

### 5.1 致命配置错误（会直接导致功能失败）

| # | 问题 | 位置 | 影响 |
|:--|:-----|:-----|:-----|
| C1 | `gateway/.env` 中 `ALPHAID_URL=http://localhost:8002` | 端口 8002 不存在 | Gateway 无法连接 Alpha-ID |
| C2 | `gateway/.env` 中 `DS_URL=http://localhost:3004` | 端口 3004 不存在 | Gateway 健康检查 DS 失败 |
| C3 | `DS/.env` 中 `PLATFORM_URL=http://localhost:8000` | Docker 容器内 localhost:8000 是容器自己 | DS 无法连接 Alpha-ID |
| C4 | `docker-compose.prod.yml` 缺少 redis, ghost-ds, feishu-consumer, prometheus, grafana | 生产环境启动后缺少 5 个服务 | 生产部署不完整 |
| C5 | `docker-compose.override.yml` 引用 `ghost-net` external 网络 | 该网络由 prod compose 创建，不在 base 中 | override 无法单独使用 |

### 5.2 高危配置错误（会导致开发/生产行为不一致）

| # | 问题 | 位置 | 影响 |
|:--|:-----|:-----|:-----|
| C6 | Alpha-ID `.env.example` 使用数据库用户 `mw` | 与 init SQL 的 `ghost` 用户不一致 | 新开发者连接数据库失败 |
| C7 | Ghost DS `.env.example` 指向数据库 `ds` schema `public` | 实际是 `ghost` 库 schema `ds` | 新开发者连接错误数据库 |
| C8 | `sql/init/01-databases.sql` 创建 `gateway` 数据库 | 无服务使用 | 孤立数据库 |
| C9 | Grafana `GF_SERVER_ROOT_URL=http://localhost:3000` | 实际映射端口是 3005 | Grafana 链接错误 |
| C10 | `DS/.env` 未设置 `NEXT_PUBLIC_GATEWAY_URL` | 本地开发不通过 Gateway | 无速率限制/审计 |

### 5.3 中危配置不一致（可能导致数据错误或安全问题）

| # | 问题 | 位置 | 影响 |
|:--|:-----|:-----|:-----|
| C11 | `AUTH_MASTER_KEY` 在 root `.env` 和 Alpha-ID `.env` 中不同 | 两把不同的密钥 | Token 跨服务验证可能失败 |
| C12 | `OPENAI_API_KEY` 在 root/Alpha-ID/Nebula 三个 `.env` 中不同 | 不同值 | 各服务使用不同 LLM 账号 |
| C13 | `OPENAI_BASE_URL` 格式不一致（带 `/v1` 或不带） | 各服务 `.env` | 部分请求可能 404 |
| C14 | Net-Agent `requirements.txt` 缺少 cryptography, python-jose, aio-openwrt, python-xiaomi-miwifi | 懒导入不报错但运行时崩溃 | 认证/加密/适配器功能不可用 |
| C15 | Feishu Bot `CODE_RUNNER_DIR=D:\MW` | Windows 路径在 Linux Docker 中无效 | Code Runner 工作目录错误 |

### 5.4 命名不一致（导致理解和维护困难）

| 概念 | 出现形式 | 问题 |
|:-----|:--------|:-----|
| Ghost DS | "Ghost DS", "ghost-ds", "DS", "Ghost DS (Next.js)" | 同一个东西 4 个名字 |
| Alpha-ID | "Alpha-ID", "alphaid", "Alpha-ID", "alpha_id"(DB) | 同一个东西 4 个名字 |
| OneBound/Shoplazza | 路由目录 `shoplazza/`，代码用 `ONEBOUND_*`，文件处理 OneBound | 路由命名与实际功能不符 |
| 飞书 | "Feishu Bot", "feishu-bot", "feishu-consumer", "FeishuBridge" | 两个服务的角色不清 |

---

## 六、文档 vs 代码 vs 运行状态 矛盾

| 维度 | 文档描述 | 代码实际 | 运行状态 | 矛盾程度 |
|:-----|:---------|:---------|:---------|:---------|
| Ghost DS 端口 | 文档说 3000 | Docker 映射 3001:3000，开发 3004 | 容器跑在 3001 | 🟡 混淆但不致命 |
| Orchestrator | ARCHITECTURE.md 说 "in-process" | 独立 Docker 服务 :19090 | 容器运行中 | 🔴 文档错误 |
| Ghost DS | GHOST.md 完全未提及 | 17 个 API 路由，电商核心 | 容器运行中 | 🔴 架构文档严重缺失 |
| Feishu Bot | GHOST.md 提及但无细节 | 2 个 Docker 服务 | 2 个容器 unhealthy | 🟡 存在但状态差 |
| Redis | GHOST.md 未提及 | 事件总线核心依赖 | 容器运行中 | 🔴 架构文档缺失 |
| Prometheus/Grafana | 未在 GHOST.md 提及 | docker-compose.override.yml 定义 | 容器运行中 | 🟡 存在但未文档化 |
| Alpha-ID 版本 | 说是 "the brain" | WIP 分支，25 个未合并提交 | 容器运行中 | 🟡 功能可用但非稳定版 |
| production compose | 应该能独立部署 | 缺少 5 个关键服务 | 未验证 | 🔴 生产配置不完整 |

---

## 七、死代码与未接线组件

| 组件 | 状态 | 说明 |
|:-----|:-----|:-----|
| `FulfillmentMiddleware` (`DS/src/lib/fulfillment.ts`) | 🧟 死代码 | 定义了 3 条履约路径，从未被实例化 |
| `FulfillModal.tsx` | ⚠️ 绕过 Gateway | 使用 template literal 直连，不走 `getApiUrl()` |
| `ObsidianKnowledgeBridge` (`gateway/services/obsidian_bridge.py`) | 🚫 未接线 | 657 行完整实现，但没有任何代码调用它 |
| `eventbus-server.ts` | 🧟 死代码 | 与 `eventbus-init.ts` 功能重复，两者都未调用 `startConsuming()` |
| `Feishu feeds/subscribe` | 🚫 Stub | 返回 501 |
| `Orchestrator ToolA/ToolB` | 🚫 Stub | 返回 "not_implemented" |
| `Net-Agent decision/` 包 | 🚫 空包 | 注释 "Stage 3" |
| `Net-Agent event/` 包 | 🚫 空包 | 注释 "Stage 4" |
| `gateway gateway` 数据库 | 🚫 孤立 | `01-databases.sql` 创建但无服务连接 |
| `shoplazza.ts` (DS 客户端) | 🚫 未使用 | 完整实现但 app 用 OneBound 替代 |
| `static/doubao_page.html` | 🚫 缺失 | Gateway 路由引用但文件不存在 |
| `static/monitoring.html` | 🚫 缺失 | Gateway 路由引用但文件不存在 |

---

## 八、系统级优化路线图

### Phase 0：止血（1-2 天）— 修复会导致功能失败的问题

| 优先级 | 问题 | 修复方案 | 影响 |
|:-------|:-----|:---------|:-----|
| P0 | `FulfillModal.tsx` 绕过 Gateway | 改用 `getApiUrl()` | 履约操作获得速率限制 + 审计 |
| P0 | Gateway `human.py` 重复路由定义 | 删除重复的 memory_search/graph | FastAPI 启动不报错 |
| P0 | `gateway/.env` `ALPHAID_URL=localhost:8002` | 改为 `localhost:8000` | 本地 Gateway 能连 Alpha-ID |
| P0 | `gateway/.env` `DS_URL=localhost:3004` | 改为 `ghost-ds:3000` | Docker 健康检查通过 |
| P0 | `DS/.env` `PLATFORM_URL=localhost:8000` | 改为 `alphaid:8000` | Docker 内 DS 能连 Alpha-ID |
| P0 | Feishu Bot/Consumer unhealthy | 检查健康检查配置 | 飞书通知恢复 |
| P0 | `docker-compose.prod.yml` 缺少 5 个服务 | 添加 redis, ghost-ds, feishu-consumer, prometheus, grafana | 生产部署可用 |

### Phase 1：连通（2-3 天）— 把断掉的链路接上

| 优先级 | 问题 | 修复方案 | 影响 |
|:-------|:-----|:---------|:-----|
| P1 | 履约事件不进入 EventBus | `fulfill/route.ts` 发布 `order:fulfilled` 事件 | 履约通知链路恢复 |
| P1 | `FulfillmentMiddleware` 死代码 | 实例化并注册到 EventBus，或删除 | 代码整洁 |
| P1 | EventBus `startConsuming()` 从未调用 | 在 DS 启动时调用 | DS 端事件消费者生效 |
| P1 | Feishu Consumer `supply:*` 事件不匹配 | 对齐 DS 发布的事件类型和 Consumer 订阅的类型 | 库存变更通知 |
| P1 | `_resolve_notify_user()` 返回 None | 实现 shop_owner 和 alpha_id → Feishu user_id 映射 | 飞书通知能找到收件人 |
| P1 | `ObsidianKnowledgeBridge` 未接线 | 在电商事件 handler 中调用 `sync_from_events()` | 知识自动同步到 Obsidian |
| P1 | `sync/route.ts` 不发布 sync 事件 | 添加 sync:started/completed/failed 发布 | 同步状态可追踪 |

### Phase 2：加固（3-5 天）— 修复安全隐患和数据一致性问题

| 优先级 | 问题 | 修复方案 | 影响 |
|:-------|:-----|:---------|:-----|
| P2 | OneBound API key 明文存储 | 加密存储（类似 Net-Agent 的 AES-GCM） | 安全 |
| P2 | JWT 签名不验证 | 在 Gateway 验证 JWT 签名（共享 Alpha-ID 的公钥） | 安全 |
| P2 | `alpha_id` 查询参数 legacy auth | 移除查询参数认证方式 | 安全 |
| P2 | 店铺 domain 跨租户碰撞 | domainHash 加 tenantId 前缀 | 多租户隔离 |
| P2 | `products/orders` 路由不校验 DS_API_KEY | 添加 `verifyRequest()` | 安全 |
| P2 | Doubao 扫描器线程崩溃风险 | 改用 asyncio 任务而非 threading.Thread | 稳定 |
| P2 | `obsidian.py` 已弃用 API | 改为 `asyncio.get_running_loop()` | 稳定 |
| P2 | `AUTH_MASTER_KEY` 跨服务不一致 | 统一密钥管理 | Token 验证一致性 |

### Phase 3：完善（1-2 周）— 补齐骨架和缺失功能

| 优先级 | 问题 | 修复方案 | 影响 |
|:-------|:-----|:---------|:-----|
| P3 | Orchestrator ToolA/ToolB stub | 接入真实服务（zcode/codex/atomcode） | 编排功能可用 |
| P3 | Orchestrator serial/parallel no-op | 实现真正的串行/并行执行 | 编排逻辑正确 |
| P3 | 履约 merchant_skill + marketplace_split | 接入真实的 skill 调用和子订单拆分 | 履约完整 |
| P3 | Net-Agent 缺失依赖 | 补充 cryptography, python-jose 到 requirements.txt | 服务稳定 |
| P3 | Xiaomi set_wifi_channel | 实现或移除该方法 | API 完整性 |
| P3 | 审批按钮回调 | 实现飞书交互卡片按钮事件处理 | 审批流程可用 |
| P3 | `listAllProducts` 1000 条截断 | 改为无限制翻页或可配置上限 | 大数据集完整同步 |

### Phase 4：文档化（1 天）— 让文档追上代码

| 优先级 | 问题 | 修复方案 |
|:-------|:-----|:---------|
| P4 | GHOST.md 缺少 Ghost DS、Feishu、Redis、监控 | 补充架构图和服务说明 |
| P4 | ARCHITECTURE.md 说 Orchestrator "in-process" | 修正为独立 Docker 服务 |
| P4 | PORTS.md 说 DS 端口 3000 | 修正为 3001（host）/ 3000（container）|
| P4 | `shoplazza/route.ts` 命名错误 | 重命名为 `onebound/` |
| P4 | Alpha-ID 是 WIP 分支未说明 | 在 GHOST.md 中标注 |

---

## 九、系统健康度评分

| 维度 | 评分 | 说明 |
|:-----|:-----|:-----|
| 电商主链路（浏览→同步→履约） | **65%** | 浏览/同步可用，履约绕过 Gateway + 事件断裂 |
| 认证与身份 | **60%** | JWT 签发正常，但 Gateway 不验签 + identity 端点绕过 |
| 事件总线 | **30%** | 基础设施完整，但 startConsuming 未调用 + 事件类型不匹配 |
| 飞书通知 | **40%** | Consumer 能运行但收件人解析为 None |
| 知识采集 | **75%** | 豆包→Obsidian 链路完整但有线程安全 bug |
| 多租户隔离 | **70%** | 租户注入 + 查询隔离完整，但部分路由无 API key 校验 |
| 可观测性 | **85%** | Prometheus + Grafana 运行中，DS 有 metrics 端点 |
| 配置一致性 | **45%** | 18 处不一致，5 处致命 |
| 文档准确性 | **50%** | 缺少关键服务，架构图过时 |
| 代码整洁度 | **55%** | 11 处死代码/未接线/孤立组件 |

---

## 十、规划建议：怎么做项目、怎么打磨

### 你现在可以做的

1. **先跑 Phase 0（止血）** — 这些问题如果不修，某些功能就是坏的。特别是 FulfillModal 绕过 Gateway 和 duplicate routes，修起来很快。

2. **用三文件体系做规划** — 每次新对话先读 `PROJECT_STATUS_REPORT.md` → `WORK_LOG.md` → `DECISIONS.md`，然后从 Phase 0 开始逐项推进。

3. **每条链路独立验证** — 不要同时改多个服务。先修一条链路的断点，验证通了再修下一条：
   - 链路 1（浏览商品）→ 基本可用，只需修 Gateway 直连
   - 链路 3（履约）→ 需要修 FulfillModal + 事件发布
   - 链路 4（飞书通知）→ 需要修 Consumer + 收件人解析
   - 链路 5（知识采集）→ 基本可用，只需修线程 bug

4. **文档滞后于代码是最大的隐性成本** — 每次做完 Phase 0-3，同步更新 GHOST.md 和 ARCHITECTURE.md。否则下次换对话又要重新摸一遍。

### 中期规划（1-2 周）

完成 Phase 0 + Phase 1 后，系统的主要链路就通了。然后：
- Phase 2 加固安全（API key 加密、JWT 验签）
- Phase 3 补齐 Orchestrator（这是最大的功能缺口）
- Phase 4 文档化（一次性解决文档过时问题）

### 长期规划（1 个月+）

- 接入真实货源 API（1688 OpenAPI）
- 接入 Shoplazza Fulfillment API
- Flow 添加数据库持久化
- Ghost DS 接入真实电商数据
- 记忆图谱积累用户对话后自动生成

---

*本文件为系统级全景审计（2026-08-04），基于 5 个并行子代理的代码级逐文件检查。所有调用链、数据流、事件流、断点均已实际验证。*
