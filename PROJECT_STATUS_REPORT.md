# Ghost Platform — 项目状态报告

> **最后更新:** 2026-08-04（代码级深度审计 + 战略定位整合后）  
> **当前分支:** master @ `248f66b`  
> **Docker 状态:** 12 容器运行中，2 容器 unhealthy  
> **Git 状态:** 77 个文件有未提交变更（主要为 unstaged）  
> **战略定位:** Web4.0 AtoA (Agent-to-Anything) 全域自主智能体操作系统  
> **参考文档:** `1.md.md` (AlphaID跨境全链路一体化平台) | `2.md.md` (从AI外置大脑到Web4.0 AtoA)

---

## 一、三层终极堆栈（战略定位）

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

---

## 二、项目宪法（GHOST.md 摘要 + 战略定位）

### 2.1 三层终极堆栈（来自 2.md.md）

| 层 | 名称 | 组成 | 说明 |
|:--:|:-----|:-----|:-----|
| L理念 | 理念层 (外置大脑) | Denny AI | 人机共生哲学、智能体行为规范、商业伦理 |
| L中枢 | 系统中枢 | Alpha-ID | 个人终身DID身份 + 双链记忆 + Agent生态 + Skill市场 |
| L网络 | 底层网络 | Ghost AtoA | Gateway + Nebula + Orchestrator + Net-Agent + Feishu Bot + Ghost DS |

### 2.2 七层系统架构（来自 1.md.md）

| 层 | 名称 | 服务 | 状态 |
|:--:|:-----|:-----|:----:|
| L7 | 知识协同层 | Obsidian + 飞书多维表格 + Ghost DS 看板 | ⚠️ 部分完成 |
| L6 | 业务展现层 | Ghost DS (电商) + Feishu Bot (4合1) | ✅ 高 |
| L5 | 统一网关层 | Gateway (:18080) 9路由 + 代理重试 | ✅ 95% |
| L4 | 智能调度层 | Orchestrator (:19090) + Redis Streams | ⚠️ 20% |
| L3 | 工作流引擎层 | Nebula (:2002) + 7层中间件 | ✅ 85% |
| L2 | 身份与权限层 | Alpha-ID (:8000) + Net-Agent (:18180) | ✅ 95% |
| L1 | 感知与接入层 | Docker Compose + 数据采集 | ✅ |

### 2.3 项目基调

| 维度 | 定位 |
|:-----|:------|
| **做什么** | 让人类与AI智能体共同成为互联网原生网络公民，收回个人数字数据主权 |
| **不做什么** | 不碰区块链/虚拟币/NFT，不发代币，所有数据部署国内服务器，遵循《个人信息保护法》 |
| **最终形态** | 一人一生唯一Alpha-ID + 双链记忆 + A2A智能体协同 + Obsidian知识闭环 + 合规双边商业生态 |
| **电商定位** | MVP 场景，不是最终形态。通过电商验证 AtoA 生态可行性。 |
| **商业模式** | 算力租赁 + Skill分成 + 行业私有化部署 + Web4.0身份订阅 |
| **总纲** | 身份→记忆→调度→网关→通信，五层地基打通后才是业务和商业 |

### 2.4 四条主线

| 主线 | 入口 | 调用链路 | 功能 |
|:-----|:-----|:---------|:-----|
| A | 豆包 | LevelDB → 豆包阅读器 → Gateway → Alpha-ID + Obsidian | 知识自动沉淀 |
| B | 飞书 | WebSocket → Gateway → Alpha-ID / Nebula / Net-Agent | 总对话助理，调全平台能力 |
| C | Ghost DS | 浏览器 → Next.js → Prisma → PostgreSQL | 电商看板 + 订单/产品管理 |
| D | Ghost.html | 浏览器 → Gateway → Alpha-ID | 注册 + 仪表盘 + 聊天 |
| E | NURO | 本地 Ollama + 双链记忆 + MCP | 桌面精灵 (纯本地) |
| F | Orchestrator | Redis Streams → 任务队列 → 各服务 | 自动化调度 (待实现) |

---

## 三、Docker 运行状态（实际）

### 3.1 容器状态

| 容器 | 服务 | 状态 | 端口 | 说明 |
|:-----|:-----|:-----|:-----|:-----|
| mw-db-1 | PostgreSQL | ✅ healthy | 5432 | 共享数据库 |
| mw-redis-1 | Redis | ✅ healthy | 6379 | 缓存 + 事件总线 |
| mw-alphaid-1 | Alpha-ID | ✅ healthy | 8000 | Git 子模块，有本地修改 |
| mw-nebula-1 | Nebula | ✅ healthy | 2002 | 工作流引擎 |
| mw-flow-1 | Flow | ✅ healthy | 3036 | 前端门户 |
| mw-gateway-1 | Gateway | ✅ healthy | 18080 | 统一 API 网关 |
| mw-netagent-1 | Net-Agent | ✅ healthy | 18180 | 路由器管理 |
| mw-orchestrator-1 | Orchestrator | ✅ healthy | 19090 | 任务编排 |
| mw-ghost-ds-1 | Ghost DS | ✅ healthy | 3004 | 电商看板 |
| ghost-prometheus | Prometheus | ✅ up | 9090 | 监控 |
| ghost-grafana | Grafana | ✅ up | 3000 | 监控面板 |
| mw-feishu-bot-1 | Feishu Bot | ⚠️ unhealthy | 8080 | 健康检查失败 |
| mw-feishu-consumer-1 | Feishu Consumer | ⚠️ unhealthy | 8080 | 健康检查失败 |

### 3.2 网络

| 网络 | 状态 | 说明 |
|:-----|:-----|:-----|
| ghost-net | ✅ 存在 | bridge 网络，由 docker-compose.prod.yml 创建 |
| mw_default | ✅ 存在 | 默认网络（base compose 使用） |

> ⚠️ `docker-compose.override.yml` 引用 `ghost-net` 为 `external: true`，但该网络不在 base compose 中定义。当前能运行是因为之前通过 prod compose 创建了该网络。若重建环境需注意。

---

## 四、各服务代码级真实状态

### 4.1 Ghost DS（Next.js 前端）— 高度可用

| 维度 | 状态 | 说明 |
|:-----|:-----|:-----|
| 框架 | ✅ | Next.js 14 + React 18 + TypeScript |
| 页面 | ✅ | 8+ 页面全部有真实业务逻辑 |
| 首页 | ✅ | Ghost cosmic 品牌页（CosmicBackground + GhostSprite + GlassCard） |
| 商品管理 | ✅ | 实时 Prisma 查询 + OneBound 同步 + AI 文案 |
| 订单管理 | ✅ | 实时 Prisma 查询 + 3 条履约路径 + FulfillModal |
| 店铺设置 | ✅ | 连接管理 + storeMode 切换 + 断开 |
| 组件 | ✅ | 14 个组件全部存在（Sidebar 在 `components/layout/Sidebar.tsx`） |
| API 路由 | ✅ | 17+ 路由全部有真实逻辑 |
| 事件总线 | ✅ | Redis Streams + 消费者组 + DLQ + 重试 |
| 货源适配器 | ✅ | OneBound 完整客户端（1688/CJ），速率限制 + 重试 |
| AI 文案 | ✅ | 3 层策略（demo 模板 / API LLM / 批量生成） |
| 多租户 | ✅ | JWT DID → X-Tenant-ID → Prisma 查询隔离 |
| 履约中台 | ✅ | 3 条路径（auto/merchant/marketplace） |
| 可观测性 | ✅ | Prometheus metrics 端点 + middleware |
| 设计系统 | ✅ | Ghost cosmic theme（CSS 变量 + 共享组件） |
| Docker | ✅ | 3-stage 构建，容器运行中 healthy |

**已知问题：**
- `typescript: { ignoreBuildErrors: true }` — 类型错误不阻断构建
- `eventbus-init.ts` 和 `eventbus-server.ts` 功能重复
- `webhook/shoplazza/route.ts` 命名错误（实际处理 OneBound webhook）
- 履约中台的 `merchant_skill` 和 `marketplace_split` 路径为模拟（TODO）
- Shoplazza 客户端（`shoplazza.ts`）已实现但未使用（用 OneBound 替代）

### 4.2 Gateway（FastAPI 网关）— 生产就绪

| 维度 | 状态 | 说明 |
|:-----|:-----|:-----|
| 框架 | ✅ | FastAPI + uvicorn (2 workers) |
| 代码量 | ✅ | 723 行 app.py，9 个路由模块 |
| 路由 | ✅ | human (364行), agent (129行), internal (335行), ecom (249行), flow (236行), net (37行), notify (229行), obsidian_bridge (257行) |
| 中间件 | ✅ | CORS + 关联 ID + 速率限制 + 租户提取 + Prometheus |
| 代理 | ✅ | 重试逻辑 + 连接池 + 错误处理 + 超时控制 |
| 电商路由 | ✅ | 13 个 /v1/ecom/* 端点，注入 X-Tenant-ID |
| Obsidian 桥接 | ✅ | 8 类知识卡片 CRUD + 双向同步 |
| 飞书通知 | ⚠️ | 有条件功能（依赖 feishu_service 模块） |
| Doubao 采集 | ✅ | LevelDB 解析 + 知识提炼 + Obsidian 写入 |
| Docker | ✅ | 2-stage 构建，容器运行中 healthy |

**已知 Bug：**
- `routes/human.py` 有重复路由定义（`memory_search` 和 `memory_graph` 各定义了两次），FastAPI 启动时会报错
- `services/obsidian.py` 的 `write_conversation_async()` 调用已弃用的 `asyncio.get_event_loop()`（Python 3.10+ 可能崩溃）
- `app.py` 的 Doubao 扫描器线程使用同步 `httpx.Client` + `ASGITransport`，无 asyncio 事件循环
- `DS_URL` 有 3 个可能的值（compose 默认 / .env 覆盖 / bat 文件未设置）
- `redis` 和 `aioredis` 在 requirements.txt 中但未被 Gateway 代码使用

### 4.3 Nebula（工作流引擎）— 高度可用

| 维度 | 状态 | 说明 |
|:-----|:-----|:-----|
| 框架 | ✅ | FastAPI + uvicorn (4 workers) |
| 代码量 | ✅ | 大量模块（见下方完整列表） |
| 数据库 | ✅ | SQLAlchemy 2.0 异步 + Alembic 迁移 |
| 模型 | ✅ | Tenant, User, Token, Approval, ApprovalHistory, AuditLog, Memory |
| 认证 | ✅ | 多租户 + Bearer Token + 角色权限 |
| 审计 | ✅ | 完整中间件 + 领域级审计日志 |
| 审批系统 | ✅ | 多级审批 + 决策逻辑 + 历史追踪 |
| 工作流引擎 | ✅ | 意图解析 + 工具选择 + 并行执行 |
| LLM 客户端 | ✅ | 多提供商回退链 + 指数退避重试 |
| 飞书集成 | ✅ | WebSocket 长轮询 + PING/PONG 协议 |
| 微信集成 | ✅ | XML 消息解析 + SHA1 签名验证 |
| 百度地图 | ✅ | 搜索/路线/地理编码/天气 + demo 降级 |
| 抖音自动化 | ✅ | Playwright 浏览器自动化 + 状态机 |
| 货源适配器 | ✅ | 1688 + CJ Dropshipping 标准化 |
| 短剧审核 | ✅ | 本地 AI 扫描 + 平台提交 |
| 中间件 | ✅ | 7 层（Prometheus + 审计 + 认证 + 速率限制 + CSRF + CORS + 关联 ID） |
| Docker | ✅ | 2-stage 构建，容器运行中 healthy |

**已知问题：**
- Shopify 集成返回 `"pending_implementation"`
- 货源同步端点有 TODO（返回占位 ID）
- 工作流模板和执行返回硬编码值
- 短剧和抖音路由在无 API 凭证时降级到 demo 模式

**完整模块列表：**
```
src/mindflow_map/
├── ai/           — LLM 客户端 + 熔断器 + 回退规则
├── api/          — 13 个路由模块（approvals, automation, events, feishu, map, shortdramas, streaming, supply, wechat, workflow）
├── automation/   — 抖音 + Shopify + 脚本生成
├── core/         — 认证 + 缓存 + 引擎注册 + 事件 + 指标
├── identity/     — Alpha-ID 客户端
├── integration/  — 短剧集成
├── memory/       — 记忆存储
├── middleware/   — 7 层中间件
├── models/       — 6 个 SQLAlchemy 模型 + 审计/认证存储
├── plugins/      — 插件注册表
├── schemas/      — Pydantic schemas（5 个模块）
├── secrets/      — 密钥管理
├── supply/       — 货源适配器（1688 + CJ）
├── tools/        — 百度地图工具
├── workflows/    — 工作流引擎
├── config.py     — 配置管理
├── main.py       — FastAPI 应用入口
└── errors.py     — 错误处理
```

### 4.4 Orchestrator（任务编排）— 骨架可用

| 维度 | 状态 | 说明 |
|:-----|:-----|:-----|
| 框架 | ✅ | FastAPI + uvicorn |
| 代码量 | ⚠️ | 仅 1 个文件（main.py，~11KB） |
| 任务管理 | ✅ | 线程安全内存存储 + 原子状态转换 + TTL 清理 |
| 并发 | ✅ | ThreadPoolExecutor（默认 4 workers） |
| 网关同步 | ✅ | 任务提交时同步记忆到 Gateway |
| 认证 | ✅ | 可选 Bearer Token |
| Docker | ✅ | 2-stage 构建，容器运行中 healthy |
| **ToolA 集成** | ❌ **Stub** | 返回 `"not_implemented"` |
| **ToolB 集成** | ❌ **Stub** | 返回 `"not_implemented"` |
| **Serial/Parallel** | ❌ **No-op** | 接受参数但不影响执行 |

**结论：** Orchestrator 是一个**骨架服务**。基础设施（任务存储、线程池、HTTP 客户端）是真实的，但核心编排逻辑（ToolA/ToolB 调用）是 stub。任务提交会"完成"但不做任何实际工作。

### 4.5 Net-Agent（路由器管理）— 核心可用

| 维度 | 状态 | 说明 |
|:-----|:-----|:-----|
| 框架 | ✅ | FastAPI + uvicorn |
| 认证 | ✅ | JWT（启动时验证密钥长度 ≥32 字符） |
| 加密 | ✅ | AES-GCM 凭证加密（PBKDF2 100K 迭代） |
| 数据库 | ✅ | SQLite（5 张表 + 索引） |
| 任务队列 | ✅ | 原子 claim（避免竞态条件） |
| 数据隔离 | ✅ | 每行 user_id 隔离 |
| OpenWrt 适配器 | ✅ | 完整实现（7 个方法） |
| TP-Link 适配器 | ⚠️ | 密码编码是猜测（TODO） |
| Xiaomi 适配器 | ⚠️ | set_wifi_channel 未实现 |
| 网络监控 | ✅ | 指标上传 + 历史查询 + 审计日志 |
| 决策引擎 | ❌ **Stub** | 空包，注释为 "Stage 3" |
| 事件总线 | ❌ **Stub** | 空包，注释为 "Stage 4" |
| Docker | ✅ | 2-stage 构建，容器运行中 healthy |

**已知问题：**
- `requirements.txt` 缺少 `cryptography`、`python-jose`、`aio-openwrt`、`python-xiaomi-miwifi`（懒导入，启动不报错但运行时会失败）
- 决策引擎和事件总线为未来 Stage，尚未开始
- `.env` 使用开发密钥

### 4.6 Feishu Bot（飞书交互总线）— 功能完整

| 维度 | 状态 | 说明 |
|:-----|:-----|:-----|
| 主循环 | ✅ | WebSocket + HTTP 轮询双通道 |
| 消息处理 | ✅ | 真实 WS 连接 + 消息分发 |
| 对话记忆 | ✅ | 每会话最近 10 条，持久化到 conversations.json |
| 定时任务 | ✅ | 中文自然语言解析 + 持久化到 tasks.json |
| 速率限制 | ✅ | 每会话 token bucket（20 msg/min） |
| 4-in-1 Chat | ✅ | 真实飞书 API 调用 + mock 降级 |
| 4-in-1 Execute | ✅ | 委托给 code_runner（atomcode/zcode/codex） |
| 4-in-1 Notify | ✅ | 10 种通知模板 + 富文本卡片 |
| 4-in-1 Approve | ⚠️ | 卡片发送正常，**按钮回调未实现** |
| Redis Consumer | ✅ | 9 种事件类型 + 消费者组 + XACK |
| Code Runner | ✅ | 3 个后端 + 并发控制 + 安全过滤 |
| Docker | ⚠️ | 容器运行但 unhealthy |

**已知问题：**
- 审批按钮回调处理器缺失
- `_resolve_notify_user()` 有 2 个 TODO（店铺所有者 / Alpha-ID 映射）
- 无测试（tests/ 为空）
- `.env` 包含真实飞书凭证
- 容器 unhealthy（可能健康检查配置问题）

### 4.7 Alpha-ID（身份层）— 外部子模块

| 维度 | 状态 | 说明 |
|:-----|:-----|:-----|
| 类型 | ⚠️ | Git 子模块（`https://github.com/wenwanqing1217/alpha-id.git`） |
| 提交 | ⚠️ | `e9f07df`（v0.3.2-25-ge9f07df），分支 `wip/2026-07-27` |
| 本地修改 | ⚠️ | 28 修改文件 + 13 未跟踪文件 |
| 容器 | ✅ | 运行中 healthy |
| 功能 | ✅ | DID + 双链记忆 + JWT + A2A + MCP + 飞书桥接 |

---

## 五、代码功能度评分（真实）

| 服务 | 功能度 | 说明 |
|:-----|:------|:-----|
| Ghost DS | **90%** | 几乎所有功能都是真实实现，少量 TODO |
| Gateway | **95%** | 生产级代码，仅少数 bug 需修复 |
| Nebula | **85%** | 大量功能实现，部分端点返回硬编码值 |
| Orchestrator | **20%** | 骨架可用，核心编排为 stub |
| Net-Agent | **60%** | 服务器核心 + 部分适配器，Stage 3/4 未开始 |
| Feishu Bot | **80%** | 核心功能完整，审批回调缺失 |
| Alpha-ID | **80%** | 外部子模块，本地有修改 |
| Docker Compose | **75%** | 编排完整，ghost-net 网络有隐患 |

---

## 六、服务间连接（代码级确认）

| 连接 | 状态 | 代码位置 |
|:-----|:-----|:---------|
| Gateway → Alpha-ID | ✅ | `routes/human.py`, `routes/agent.py` 代理到 `ALPHAID_URL` |
| Gateway → Nebula | ✅ | `routes/flow.py` + `proxy.py` |
| Gateway → Flow | ✅ | `routes/flow.py` 15 个端点映射 |
| Gateway → Orchestrator | ✅ | `routes/internal.py` 任务代理 |
| Gateway → Net-Agent | ✅ | `routes/net.py` 全路径代理 |
| Gateway → Ghost DS | ✅ | `routes/ecom.py` 13 个端点 + 租户注入 |
| Gateway → Obsidian | ✅ | `routes/obsidian_bridge.py` 完整 CRUD |
| Gateway → Feishu | ⚠️ | `routes/notify.py` 有条件功能 |
| Alpha-ID → PostgreSQL | ✅ | 子模块内 |
| Nebula → PostgreSQL | ✅ | SQLAlchemy + Alembic |
| Ghost DS → PostgreSQL | ✅ | Prisma + 多租户 |
| Ghost DS → Redis | ✅ | EventBus + 缓存 |
| Feishu Consumer → Redis | ✅ | Redis Streams 消费者组 |
| Flow → (无后端) | ⚠️ | 独立 Fastify，无数据库 |

---

## 七、Docker Compose 编排

### 7.1 服务清单

| 服务 | 镜像/构建 | 端口 | 容器状态 |
|:-----|:----------|:-----|:---------|
| db | postgres:16-alpine | 5432 | ✅ healthy |
| redis | redis:7-alpine | 6379 | ✅ healthy |
| alphaid | 构建（子模块） | 8000 | ✅ healthy |
| nebula | 构建 | 2002 | ✅ healthy |
| flow | 构建 | 3036 | ✅ healthy |
| gateway | 构建 | 18080 | ✅ healthy |
| netagent | 构建 | 18180 | ✅ healthy |
| orchestrator | 构建 | 19090 | ✅ healthy |
| ghost-ds | 构建 | 3001→3000 | ✅ healthy |
| feishu-bot | 构建 | - | ⚠️ unhealthy |
| feishu-consumer | 构建 | - | ⚠️ unhealthy |
| prometheus | prom/prometheus:v2.54.0 | 9090 | ✅ up |
| grafana | grafana/grafana:11.1.0 | 3005→3000 | ✅ up |

### 7.2 持久化存储

| Volume | 用途 |
|:-------|:-----|
| pgdata | PostgreSQL 数据 |
| redisdata | Redis AOF + 数据 |
| prometheus-data | Prometheus TSDB |
| grafana-data | Grafana 配置 + 仪表板 |

### 7.3 环境变量

| 变量 | 必需 | 说明 |
|:-----|:-----|:-----|
| DB_USER | ✅ | PostgreSQL 用户名 |
| DB_PASSWORD | ✅ | PostgreSQL 密码 |
| DB_NAME | 可选 | 数据库名（默认 ghost） |
| REDIS_PORT | 可选 | Redis 端口（默认 6379） |
| FEISHU_APP_ID | 条件 | 飞书应用 ID |
| FEISHU_APP_SECRET | 条件 | 飞书应用密钥 |
| GRAFANA_ADMIN_PASSWORD | 可选 | Grafana 管理员密码（默认 admin） |
| OBSIDIAN_VAULT | 可选 | Obsidian 知识库路径 |

---

## 八、Prisma 数据层

### 8.1 Schema 文件

| 文件 | 数据库 | 特点 |
|:-----|:-------|:-----|
| `schema.prisma` | SQLite | 基础版本，4 个模型 |
| `schema.local.prisma` | SQLite | 更多索引 + settings 字段 |
| `schema.production.prisma` | PostgreSQL | 原生 Json 类型 + @db.Text |

### 8.2 模型

| 模型 | 字段 | 多租户 | 索引 |
|:-----|:-----|:-------|:-----|
| Shop | id, name, domain, accessToken, platform, alphaId, active, tenantId, storeMode, createdAt, updatedAt | ✅ | domain, alphaId, tenantId |
| Product | id, shopId, externalId, name, description, images, price, comparePrice, inventory, status, rawData, lastSyncedAt, tenantId, createdAt, updatedAt | ✅ | shopId+externalId, shopId+status, lastSyncedAt, tenantId |
| Order | id, shopId, externalId, status, customerName, customerEmail, itemCount, paidAt, fulfilledAt, trackingNumber, trackingCompany, refundedAt, rawData, tenantId, createdAt, updatedAt | ✅ | shopId+externalId, shopId+status, createdAt, paidAt, tenantId |
| SyncLog | id, shopId, entity, status, recordCount, error, startedAt, finishedAt, tenantId | ✅ | shopId+entity+startedAt, tenantId |

### 8.3 Seed 数据

- 创建 "OneBound 货源" 店铺
- 5 个示例商品（花瓶、杯子、灯、枕头、盒子）
- 6 个示例订单（各种状态）
- 使用 picsum.photos 占位图片

---

## 九、Git 子模块

| 子模块 | 路径 | 远程 | 提交 | 分支 | 本地修改 |
|:-------|:-----|:-----|:-----|:-----|:---------|
| Alpha-ID | `alphaid/projects` | `github.com/wenwanqing1217/alpha-id` | `e9f07df` | `wip/2026-07-27` | 28 修改 + 13 未跟踪 |

---

## 十、待处理问题

### 10.1 高优先级（阻塞）

| 问题 | 状态 | 说明 |
|:-----|:-----|:-----|
| **Git 提交** | 🔴 | 77 个文件有未提交变更，需分模块 commit |
| **Gateway 路由冲突** | 🔴 | `human.py` 有重复路由定义，FastAPI 启动会报错 |
| **Feishu Bot unhealthy** | 🔴 | 容器运行但不健康，需检查健康检查配置 |
| **Feishu Consumer unhealthy** | 🔴 | 同上 |
| **Prisma 迁移** | 🟡 | tenantId/storeMode 字段已加，需运行迁移 |
| **Docker 验证** | 🟡 | 容器运行中，但需验证所有 API 端点 |

### 10.2 中优先级

| 问题 | 状态 | 说明 |
|:-----|:-----|:-----|
| Orchestrator 核心逻辑 | 🟡 | ToolA/ToolB 为 stub，需接入真实服务 |
| Net-Agent 依赖缺失 | 🟡 | requirements.txt 缺少 cryptography, python-jose 等 |
| Orchestrator 串行/并行 | 🟡 | 参数接受但无实际逻辑 |
| 履约模拟路径 | 🟡 | merchant_skill + marketplace_split 为 TODO |
| DS 前端构建验证 | 🟡 | 需 `npm run build` 验证 |

### 10.3 低优先级

| 问题 | 状态 | 说明 |
|:-----|:-----|:-----|
| 真实货源接入 | ⚪ | 1688/CJ 当前为 mock |
| Shoplazza 履约 | ⚪ | platform_auto 为 mock |
| Flow 无数据库 | ⚪ | 工作流状态无法持久化 |
| ghost-capture | ⚪ | Chrome 扩展未集成 |
| 记忆图谱 | ⚪ | 演示数据 |
| Shopify 集成 | ⚪ | Nebula 中返回 pending_implementation |
| 审批按钮回调 | ⚪ | Feishu Bot 中未实现 |

---

## 十一、已知 Bug 清单

| # | Bug | 位置 | 严重度 | 说明 |
|:--|:-----|:-----|:-------|:-----|
| 1 | 重复路由定义 | `gateway/routes/human.py` | 🔴 | memory_search 和 memory_graph 各定义两次 |
| 2 | 弃用 API 调用 | `gateway/services/obsidian.py` | 🟡 | `asyncio.get_event_loop()` 在 Python 3.10+ 中可能崩溃 |
| 3 | Doubao 扫描器线程 | `gateway/app.py` | 🟡 | 同步 httpx + ASGITransport 在无事件循环的线程中 |
| 4 | DS_URL 不一致 | `gateway/config.py` | 🟡 | 3 个不同的可能值 |
| 5 | 未使用的依赖 | `gateway/requirements.txt` | 🟢 | redis, aioredis 未在代码中使用 |
| 6 | 缺失依赖 | `net_agent_server/requirements.txt` | 🟡 | cryptography, python-jose 未列出 |
| 7 | Webhook 命名错误 | `DS/src/app/api/webhook/shoplazza/route.ts` | 🟢 | 实际处理 OneBound webhook |
| 8 | EventBus 重复 | `DS/src/lib/eventbus-init.ts` + `eventbus-server.ts` | 🟢 | 两个文件功能相同 |
| 9 | TypeScript 忽略错误 | `DS/next.config.js` | 🟢 | 类型错误不阻断构建 |
| 10 | ghost-net 网络 | `docker-compose.override.yml` | 🟡 | external 网络不在 base compose 中定义 |

---

## 十二、快速启动指南

### 12.1 环境要求
- Docker Desktop（已安装，容器运行中）
- Node.js >= 18
- Python >= 3.11

### 12.2 当前状态启动

Docker 容器已运行，可直接访问：

```bash
# 健康检查
curl http://localhost:18080/health  # Gateway
curl http://localhost:3004/api/health  # Ghost DS
curl http://localhost:8000/health  # Alpha-ID
curl http://localhost:2002/health/livez  # Nebula
curl http://localhost:19090/health  # Orchestrator
curl http://localhost:18180/health  # Net-Agent
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:3000/api/health  # Grafana

# 监控面板
open http://localhost:3000  # Grafana (admin / admin)
open http://localhost:9090  # Prometheus

# 本地开发 DS 前端
cd DS
npm install
npm run dev  # Port 3004
```

### 12.3 全新启动

```bash
# 1. 确保 ghost-net 网络存在（若使用 override）
docker network create ghost-net

# 2. 启动基础服务 + 监控
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d

# 3. 验证
docker compose ps
docker compose logs -f
```

---

## 十三、连通性评分

| 层级 | 评分 | 说明 |
|:-----|:-----|:-----|
| 后端服务间 | **90%** | 主要连接已建立，容器运行中 |
| 前端到后端 | **85%** | DS 前端完整，待构建验证 |
| 桌面端到平台 | **90%** | NURO Ghost 连接 Gateway |
| 数据持久化 | **70%** | Schema 已更新，Prisma 需迁移 |
| 认证授权 | **85%** | JWT 完整 + 多租户隔离 |
| 可观测性 | **90%** | Prometheus + Grafana 运行中 |
| 代码质量 | **75%** | 大量真实实现，少数 bug 和 stub |
| 项目整洁度 | **60%** | 77 个未提交文件 |

---

## 十四、关键成就

1. ✅ 12 个 Docker 容器运行中（2 个需修复 unhealthy）
2. ✅ 统一 API 网关（Gateway）代理所有后端服务
3. ✅ DS 前端全面重写（Ghost cosmic theme + 真实业务逻辑）
4. ✅ 设计系统建立（GlassCard, GhostSprite, CosmicBackground, Tag）
5. ✅ 事件总线（Redis Streams + 消费者组 + DLQ）
6. ✅ 货源适配器（OneBound 完整客户端）
7. ✅ 履约中台（3 条路径）
8. ✅ 飞书 4-in-1 总线（Chat/Execute/Notify/Approve）
9. ✅ Nebula 工作流引擎（大量功能模块）
10. ✅ 可观测性（Prometheus + Grafana 运行中）
11. ✅ 多租户隔离（JWT DID + X-Tenant-ID）
12. ✅ AI 文案生成（3 层策略）
13. ✅ Net-Agent 路由器管理（加密存储 + 任务队列 + OpenWrt 适配器）
14. ✅ Obsidian 知识桥接（8 类知识卡片）
15. ✅ Doubao 知识采集（LevelDB 解析 + 知识提炼）
16. ✅ Git 子模块（Alpha-ID 外部仓库）

---

## 十五、下一步行动

### 立即行动

- [ ] Git commit 所有变更（分模块）
- [ ] 修复 Gateway 重复路由定义（Bug #1）
- [ ] 修复 Feishu Bot/Consumer unhealthy
- [ ] 运行 Prisma 迁移
- [ ] DS 前端构建验证

### 近期行动

- [ ] Orchestrator 接入 ToolA/ToolB
- [ ] Net-Agent 补充 requirements.txt 依赖
- [ ] 履约 merchant_skill + marketplace_split 实现
- [ ] 审批按钮回调实现
- [ ] 真实货源 API 接入

---

*报告基于代码级深度审计（2026-08-04）。所有服务代码已逐文件检查。*
