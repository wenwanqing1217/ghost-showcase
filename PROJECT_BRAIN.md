# 🧠 PROJECT_BRAIN — Ghost 项目大脑

> **每个新会话的第一件事：读这个文件。读透它，你就知道一切。**
> 最后更新：2026-07-24

---

## 一、项目本质（30 秒理解）

**Ghost 是什么：** 一个 AI Agent 矩阵平台。核心理念是"让每个 AI Agent 都认识你是谁"。

**一句话：** 用户注册一次 → 获得 DID 数字身份 → 所有 AI 工具通过这个身份认识你、记住你、代表你。

**商业叙事：** 不是做另一个 AI 助理，而是做 AI 世界的"身份证 + 征信系统"。

**唯一官网：** `D:\MW\Ghost.html`（单文件，已部署，所有面板对接真实后端）

**统一入口：** `Ghost Gateway`（port 18080）— 所有请求走这一个端口

---

## 二、六层架构

```
┌─────────────────────────────────────────────────────────┐
│  Layer 6: 商业层         积分/支付/店铺 (DS + Shoplazza) │
├─────────────────────────────────────────────────────────┤
│  Layer 5: 业务层         工作流/飞书/微信 (nebula)       │
├─────────────────────────────────────────────────────────┤
│  Layer 4: 调度层         API Gateway (port 18080)        │
├─────────────────────────────────────────────────────────┤
│  Layer 3: 网关层         Caddy / Nginx 反向代理           │
├─────────────────────────────────────────────────────────┤
│  Layer 2: 记忆层         Brain 双链 (私链+知链)           │
├─────────────────────────────────────────────────────────┤
│  Layer 1: 身份层         DID/JWT (alphaid, port 8000)    │
└─────────────────────────────────────────────────────────┘
```

**当前完成度：**
- ✅ Layer 1 身份层：alphaid 完整（DID/记忆双链/A2A 网络/MCP/飞书/CLI）
- ✅ Layer 2 记忆层：Brain 双链 + 数据采集器
- 🔄 Layer 3 网关层：Caddy 本地开发配置已有
- ✅ Layer 4 调度层：Ghost Gateway (18080) 统一路由
- ✅ Layer 5 业务层：nebula 运行中（工作流引擎+飞书+地图+抖音+Shopify）
- ✅ Layer 6 商业层：DS 电商后端运行中

---

## 三、各模块详解

### 3.1 官网 — Ghost.html

| 属性 | 值 |
|------|-----|
| 位置 | `D:\MW\Ghost.html` |
| 技术 | 单文件 HTML + Tailwind CDN（无构建步骤） |
| 部署 | 直接打开文件或 CDN 托管 |
| 行数 | ~4100 |
| 数据来源 | **统一走 Gateway (18080)**，不直连各后端 |

**包含的视图：**
- `homepageView` — 首页 Landing（品牌展示 + 小精灵互动系统）
- `workbenchView` — Web 4.0 智能路由器（9 个功能面板）
- `mindflowView` — 个人工作台（4 个标签页）

**数据流（统一网关）：**
```
Ghost.html  ──fetch──▶  Ghost Gateway (:18080)
                         ├── /v1/dashboard      ← 聚合全部数据（一次性加载）
                         ├── /v1/identity       ← alphaid 身份
                         ├── /v1/brain/status   ← alphaid 记忆
                         ├── /v1/network/topology ← alphaid A2A 网络
                         ├── /v1/shop           ← DS 店铺信息
                         ├── /v1/products       ← DS 商品列表
                         ├── /v1/orders         ← DS 订单列表
                         ├── /v1/ecommerce/stats ← DS 统计
                         ├── /v1/intent/parse   ← 智能路由（按关键词分发）
                         ├── /v1/chat           ← alphaid AI 对话
                         └── /v1/workflows      ← nebula 工作流（✅ 已连）
```

---

### 3.2 Ghost Gateway — 统一网关（NEW）

| 属性 | 值 |
|------|-----|
| 位置 | `ghost-main/gateway/app.py` |
| 技术 | Python + FastAPI + httpx (async) |
| 端口 | **18080** |
| 配置 | `ghost-main/gateway/.env` |

**API 端点表：**

| 端点 | 方法 | 代理到 | 功能 |
|------|------|--------|------|
| `/health` | GET | — | 网关自身健康 |
| `/v1/dashboard` | GET | alphaid+DS 聚合 | **全量数据一次性返回** |
| `/v1/identity` | GET | alphaid :8000 | 身份信息 |
| `/v1/profile` | GET | alphaid :8000 | 用户画像 |
| `/v1/brain/status` | GET | alphaid :8000 | Brain 状态 |
| `/v1/brain/awake` | POST | alphaid :8000 | 唤醒 Brain |
| `/v1/network/topology` | GET | alphaid :8000 | A2A 网络拓扑 |
| `/v1/chat` | POST | alphaid :8000 | AI 对话 |
| `/v1/intent/parse` | POST | 智能路由 | 按关键词分发到 alphaid/DS/chat |
| `/v1/shop` | GET | DS :3004 | 店铺信息 |
| `/v1/products` | GET | DS :3004 | 商品列表 |
| `/v1/orders` | GET | DS :3004 | 订单列表 |
| `/v1/ecommerce/stats` | GET | DS :3004 | 电商统计 |
| `/v1/ecommerce/sync` | POST | DS :3004 | 触发同步 |
| `/v1/workflows` | GET | nebula :2002 | 工作流列表 ✅ |
| `/v1/workflows/execute` | POST | nebula :2002 | 执行工作流 ✅ |

**Intent 路由规则：**
- 含"订单/商品/店铺"关键词 → DS 电商
- 含"身份/DID/记忆"关键词 → alphaid 身份
- 其他 → alphaid chat（AI 对话）

---

### 3.3 身份层 — alphaid

| 属性 | 值 |
|------|-----|
| 位置 | `alphaid/projects/` |
| 技术 | Python + FastAPI + SQLAlchemy + SQLite/PostgreSQL |
| 端口 | 8000 |
| 测试 | 928/928 全部通过 |
| 仓库 | [github.com/wenwanqing1217/alpha-id](https://github.com/wenwanqing1217/alpha-id) |

**API 端点：**

| 端点 | 方法 | 功能 |
|------|------|------|
| `/identity` | GET | 获取身份信息（需 X-Alpha-ID header） |
| `/brain/status` | GET | 获取 Brain 状态（参数：alpha_id） |
| `/brain/awake` | POST | 唤醒/初始化 Brain |
| `/network/topology` | GET | 获取网络拓扑（节点/边/统计） |
| `/api/profile` | GET | 获取用户画像（persona） |
| `/chat` | POST | AI 对话（参数：alpha_id, message） |
| `/health` | GET | 健康检查 |

**核心能力：**
- DID 数字身份（Ed25519 签名，`did:aid:` 格式）
- JWT 认证（零依赖实现）
- 记忆双链（私链 + 知链）
- 数据采集器（ChatGPT/Claude/Cursor/Browser/Git 导入）
- Agent 框架（ReAct 模式）
- MCP Server（标准化工具调用入口）
- 飞书 Bot
- CLI 工具（`aid init` / `aid collect` / `aid profile`）

---

### 3.4 编排层 — core

| 属性 | 值 |
|------|-----|
| 位置 | `core/` |
| 技术 | TypeScript + Node.js + Vitest |
| 端口 | 3001 |
| 测试 | 42/42 全部通过 |
| 仓库 | [github.com/wenwanqing1217/zcode-brain](https://github.com/wenwanqing1217/zcode-brain) |

**核心能力：**
- 任务调度（输入校验 → 安全检查 → 角色匹配 → Prompt 组装）
- 角色匹配（12 种专家角色 JSON 定义，关键词触发）
- 安全护栏（正则拦截危险命令、敏感信息泄露）

---

### 3.5 执行层 — nebula

| 属性 | 值 |
|------|-----|
| 位置 | `nebula/` |
| 技术 | Python + FastAPI + SQLAlchemy async + PostgreSQL + Alembic |
| 端口 | 2002 |
| 测试 | 221/221 全部通过 |
| 状态 | ⚠️ 代码完整，当前未运行 |

**核心能力：**
- 工作流引擎（任务编排与状态管理）
- LLM 意图识别（支持熔断、降级、健康检查）
- 飞书集成（Bot + Webhook 双模式）
- 微信接入（基础消息回调）
- 百度地图（地点查询、路径规划、POI 搜索）
- 抖音自动化
- Shopify 接入
- 中间件栈（审计、认证、限流、Prometheus 监控）

---

### 3.6 电商后端 — DS

| 属性 | 值 |
|------|-----|
| 位置 | `DS/` |
| 技术 | Next.js 14 + Prisma + SQLite |
| 端口 | 3004 |
| 部署 | 连接 Shoplazza（店匠）API |
| 店铺 | `nero.myshoplaza.com` |

**API 端点：**

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/shop` | GET | 店铺信息 |
| `/api/products` | GET | 商品列表（分页/搜索） |
| `/api/orders` | GET | 订单列表（分页/状态筛选） |
| `/api/orders/[id]/fulfill` | POST | 订单发货 |
| `/api/stats` | GET | 统计数据（含7天收入） |
| `/api/sync` | POST | 手动触发同步 |
| `/api/webhook/shoplazza` | POST/GET | Shoplazza 事件回调 |
| `/api/cron/sync` | POST/GET | 定时同步任务 |
| `/api/health` | GET | 健康检查 |

---

### 3.7 前端原型 — flow

| 属性 | 值 |
|------|-----|
| 位置 | `flow/` |
| 技术 | Next.js 14 + React 18 + TypeScript + Fastify + Leaflet |
| 端口 | 3000（前端）/ 3001（API） |
| 测试 | 32/32 全部通过 |
| 部署 | ❌ 未部署 |
| 仓库 | [github.com/wenwanqing1217/mindflow](https://github.com/wenwanqing1217/mindflow) |

**包含页面：** register、identity、dashboard、ai、map、multimodal、platform、usage、assistant

**定位：** 功能原型参考，不是官网。Ghost.html 是唯一对外入口。

**flow/api 更新：** `aid.service.ts` 已改为代理到 alphaid（:8000），不再返回假数据。

---

## 四、实际调用链（当前状态）

```
Ghost.html (唯一官网)
  │
  ├── fetch(GATEWAY_API + "/v1/dashboard")  ──▶  Ghost Gateway (:18080)
  │                                                ├── alphaid (:8000) → identity + brain + network + profile
  │                                                └── DS (:3004)       → shop + products + orders + stats
  │
  ├── fetch(GATEWAY_API + "/v1/intent/parse") ──▶  Ghost Gateway (:18080)
  │    {"message": "查看我的订单"}                     ├── 关键词匹配 → 路由到 DS
  │    {"message": "我的身份是什么"}                   ├── 关键词匹配 → 路由到 alphaid
  │    {"message": "今天天气如何"}                     └── 兜底 → alphaid chat
  │
  └── fetch(GATEWAY_API + "/v1/chat") ──▶  Ghost Gateway (:18080)
       {"message": "..."}                            └── alphaid (:8000) → ReAct Agent

Ghost Gateway (:18080)  ←── 统一入口
  ├── /v1/identity/*    → alphaid (:8000) ← 身份唯一源
  ├── /v1/brain/*       → alphaid (:8000) ← 记忆唯一源
  ├── /v1/network/*     → alphaid (:8000) ← A2A 网络
  ├── /v1/shop/*        → DS (:3004)     ← 电商唯一源
  ├── /v1/products/*    → DS (:3004)
  ├── /v1/orders/*      → DS (:3004)
  ├── /v1/ecommerce/*   → DS (:3004)
  ├── /v1/workflows/*   → nebula (:2002) ← 工作流唯一源 ✅
  └── /v1/intent/*      → 智能路由分发

alphaid (:8000)
  ├── DID 生成/验证 (Ed25519)
  ├── JWT 认证
  ├── Brain 记忆双链（私链 + 知链）
  ├── 数据采集器（ChatGPT/Claude/Cursor/Browser/Git）
  ├── A2A 网络拓扑
  ├── Agent 框架（ReAct 模式）
  ├── MCP Server
  ├── 飞书 Bot
  └── CLI 工具 (aid init/collect/profile)

DS (:3004) → Shoplazza OpenAPI → nero.myshoplaza.com
  ├── /api/shop     → 店铺信息
  ├── /api/products → 商品列表
  ├── /api/orders   → 订单列表
  └── /api/sync     → 手动同步

nebula (:2002) [✅ 运行中]
  ├── 工作流引擎
  ├── LLM 意图识别
  ├── 飞书/微信接入
  ├── 百度地图/抖音/Shopify
  └── ⚠️ 自有 identity/memory 模块（与 alphaid 重复，长期应删除）

flow/api (:3001) [代理模式]
  ├── /alphaid/identity → alphaid (:8000) ← 真实数据
  ├── /alphaid/chat    → alphaid (:8000) ← 真实对话
  └── /alphaid/health  → alphaid (:8000) ← 健康检查
```

---

## 五、架构问题诊断（当前）

### ✅ 已解决问题

| 问题 | 解决方案 |
|------|----------|
| Ghost.html 散端口调用 | **Ghost Gateway (18080) 统一入口** |
| flow/api 返回假数据 | **aid.service.ts 改为代理 alphaid** |
| alphaid CORS 跨域 | **已加 CORSMiddleware** |
| 端口 8080/8090 权限 | **改为 18080** |

### 🔴 待解决问题

| # | 问题 | 影响 | 优先级 |
|---|------|------|--------|
| 1 | nebula 自有 identity/memory 与 alphaid 重复 | 数据不一致 | P1 |
| 2 | ~~nebula 未运行~~ | ✅ 已运行，工作流引擎可用 | — |
| 3 | PostgreSQL 未启动（Docker 未运行） | nebula 用 SQLite，影响有限 | P2 |
| 4 | flow/web 与 Ghost.html 双前端 | 维护浪费 | P2 |
| 5 | 支付宝/短信/人脸验证 SDK 未接入 | 身份层缺少实名认证 | P0 |
| 6 | core 编排层为"空壳" | 没有真正调度 | P2 |

---

## 六、目标架构

```
┌─────────────────────────────────────────────────────────┐
│                    唯一官网：Ghost.html                    │
│  单文件 HTML，部署在 CDN                                   │
│  所有面板通过 fetch() 调 Ghost Gateway                      │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│              Ghost API Gateway (port 18080)               │
│  统一入口，负责路由、鉴权、限流                             │
│  /v1/identity/*  → alphaid    身份唯一源                  │
│  /v1/brain/*     → alphaid    记忆唯一源                  │
│  /v1/ecommerce/* → DS         电商唯一源                  │
│  /v1/workflows/* → nebula     工作流唯一源                │
│  /v1/intent/*    → 智能路由分发                           │
│  /v1/chat        → alphaid    AI 对话                    │
└──────────────────────────┬──────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐  ┌───────────────┐  ┌───────────────┐
│  身份引擎     │  │  工作流引擎    │  │  电商引擎      │
│  alphaid     │  │  nebula       │  │  DS           │
│  (唯一源)    │  │  (唯一源)     │  │  (唯一源)     │
│  DID/JWT/    │  │  意图识别/    │  │  Shoplazza/   │
│  记忆/MCP    │  │  飞书/微信    │  │  商品/订单    │
└──────────────┘  └───────────────┘  └───────────────┘
```

**关键原则：**
1. **身份唯一源 = alphaid** — 删除 nebula 里的重复身份模块
2. **记忆唯一源 = alphaid** — 删除 nebula 里的重复记忆模块
3. **工作流唯一源 = nebula** — 不另建工作流引擎
4. **官网唯一 = Ghost.html** — 不维护两套前端
5. **API 统一入口 = Ghost Gateway (18080)** — 所有请求走网关

---

## 七、迁移路径

### Phase 1：打通数据 ✅ 已完成
- [x] Ghost.html 的 workbench 面板连接真实 API
- [x] flow/api 的 aid.service 改成代理到 alphaid（:8000）
- [x] Ghost Gateway (18080) 统一入口
- [x] Ghost.html 统一走网关，清理散落端口调用
- [x] /v1/dashboard 聚合全部数据

### Phase 2：合并重复
- [ ] 删除 nebula/src/identity/，改为调 alphaid API
- [ ] 删除 nebula/src/memory/，改为调 alphaid API
- [ ] 统一用户体系：一个 DID 贯穿所有层

### Phase 3：整合前端
- [ ] 把 flow/web 里有价值的页面（register/identity/ai）移植到 Ghost.html
- [ ] 或者：部署 flow/web 为正式官网，Ghost.html 降为 landing page

### Phase 4：补齐基础设施
- [ ] 启动 PostgreSQL (Docker)
- [x] 启动 nebula，连接到网关
- [ ] Caddy 生产配置
- [ ] 支付宝/短信/人脸验证 SDK 接入

---

## 八、Agent 工作规范

### 8.1 新会话必做
1. **先读此文件**（PROJECT_BRAIN.md）
2. 读 `AGENT_PLAYBOOK.md`（操作手册）
3. 理解当前任务属于哪个 Phase

### 8.2 意图识别框架
当用户提出需求时，先回答这三个问题：
1. **用户真正想要什么？**（不是表面需求，是底层意图）
2. **这个功能应该在哪一层？**（身份/工作流/电商/展示/网关）
3. **是否已有类似实现？**（grep 检查，避免重复建设）

### 8.3 架构红线
- ❌ 不要在 nebula 里新建身份模块（alphaid 是唯一源）
- ❌ 不要在 flow/api 里写业务逻辑（它应该是 Gateway/代理）
- ❌ 不要在 Ghost.html 里直接调 Shoplazza API（走网关 → DS）
- ❌ 不要在 Ghost.html 里直连 alphaid:8000（走网关 :18080）
- ❌ 不要创建新的"临时"后端服务（除非架构评审通过）
- ✅ 所有前端请求走 Ghost Gateway (18080)
- ✅ 每层通过 API 调用其他层，不直接访问数据库
- ✅ 新功能先问"这属于哪一层？"

### 8.4 遇到设计错误时
如果你发现当前代码沿着一个**错误的架构路径**做（比如在错误的地方加功能、重复建设、假数据冒充真实 API）：
1. **停下来**，不要继续沿着错路走
2. **指出问题**，说明为什么这是错的
3. **提出正确方案**，基于第六章的目标架构
4. **等用户确认**后再改

**不要默默接受错误的设计继续做。**

---

## 九、关键环境信息

| 服务 | 端口 | 地址 | 状态 |
|------|------|------|------|
| **Ghost Gateway** | **18080** | `http://localhost:18080` | ✅ 运行中 |
| alphaid（身份层） | 8000 | `http://localhost:8000` | ✅ 运行中 |
| DS（电商后端） | 3004 | `http://localhost:3004` | ✅ 运行中 |
| core（编排层） | 3001 | `http://localhost:3001` | ❓ 未知 |
| nebula（执行层） | 2002 | `http://localhost:2002` | ✅ 运行中 |
| flow/web（前端原型） | 3000 | `http://localhost:3000` | ❌ 未部署 |
| flow/api（BFF） | 3001 | `http://localhost:3001` | ❓ 未知 |

**Shoplazza 店铺：** `nero.myshoplaza.com`

**Gateway 环境配置：** `ghost-main/gateway/.env`
```
ALPHAID_URL=http://localhost:8000
DS_URL=http://localhost:3004
NEBULA_URL=http://localhost:2002
DEFAULT_ALPHA_ID=Alpha-001
GATEWAY_PORT=18080
```
