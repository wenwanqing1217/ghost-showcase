# 🔍 Ghost 项目完整审计

> **审计日期：2026-07-24**
> **审计范围：** D:\MW 全部文件 + Git 历史 + 未提交变更
> **目的：** 搞清楚到底有什么、缺什么、哪些做了没连上

---

## 一、目录结构（现状）

```
D:\MW/
├── .env.example                  ← 环境变量模板（PostgreSQL + DeepSeek + 飞书 + 百度地图 + Shoplazza）
├── .env.production.example       ← 生产环境模板
├── .github/workflows/ci.yml      ← CI 配置
├── .gitignore
├── .pre-commit-config.yaml
├── AGENT_PLAYBOOK.md             ← Agent 工作手册（需更新）
├── ARCHITECTURE.md               ← 五层架构设计（需与文档对齐）
├── Caddyfile                     ← 生产反向代理配置（:80 本地开发）
├── Ghost.html                    ← 唯一官网（~4100行，已连接真实 API）
├── PROJECT_BRAIN.md              ← 项目大脑（需更新）
├── README.md
├── docker-compose.yml            ← 编排：PostgreSQL + Nebula + DS + AlphaID
├── docker-compose.prod.yml       ← 生产编排
├── package.json                  ← 根目录 npm（scripts）
├── package-lock.json
│
├── alphaid/                      ← 身份层（Python + FastAPI，端口 8000）
│   └── projects/src/alpha_id/
│       ├── web.py                ← 20+ API 路由（/identity, /chat, /brain, /network, /profile）
│       ├── agent.py              ← AgentLoop + 14 工具
│       ├── agent_network.py      ← A2A 网络（本地模拟）
│       ├── did.py                ← DID 身份
│       ├── poe.py                ← Proof of Execution
│       ├── signer.py             ← Ed25519 签名
│       ├── container.py          ← 依赖注入容器
│       ├── collectors/           ← 数据收集器
│       ├── mining/               ← 数据挖掘
│       └── *_cli.py              ← 各种 CLI 工具
│
├── core/                         ← 编排层（TypeScript）
│   ├── dispatcher/               ← 调度器（关键词匹配）
│   ├── roles/                    ← 12 角色 JSON 定义
│   └── safety/                   ← 安全护栏
│
├── nebula/                       ← 执行层（Python + FastAPI，端口 2002）
│   └── src/mindflow_map/
│       ├── main.py               ← FastAPI 入口
│       ├── api/                  ← 工作流 API
│       ├── config.py             ← 配置
│       └── ...
│
├── DS/                           ← 电商后端（Next.js + Prisma，端口 3004）
│   └── src/app/api/
│       ├── products/route.ts     ← 商品 API
│       ├── orders/route.ts       ← 订单 API
│       ├── shop/route.ts         ← 店铺 API
│       └── sync/route.ts         ← 同步 API
│
├── flow/                         ← 前端（Next.js + Fastify，端口 3000/3001）
│   ├── apps/web/                 ← Next.js 前端
│   └── apps/api/                 ← Fastify API
│       └── src/
│           ├── services/aid.service.ts  ← 已代理到 Alpha-ID
│           └── routes/aid.ts            ← 已加 /alphaid/* 代理
│
├── ghost-main/                   ← 统一网关（新建，端口 18080）
│   └── gateway/
│       ├── app.py                ← FastAPI 统一网关
│       ├── .env                  ← 后端地址配置
│       └── requirements.txt
│
├── obsidian-plugin/              ← Obsidian 插件（TypeScript）
│   ├── main.ts                   ← 插件源码
│   ├── manifest.json
│   └── styles.css
│
├── skills/                       ← MCP 技能
│   └── baidu-ai-map/             ← 百度地图技能
│
├── sql/init/
│   └── 01-databases.sql          ← 初始化 4 个数据库
│
├── scripts/                      ← 工具脚本
│   ├── start_all.bat             ← 一键启动
│   ├── smoke_test.bat            ← 烟雾测试
│   ├── health_check.py           ← 健康检查
│   ├── acceptance_check.py       ← 验收检查
│   └── github_sync.py            ← GitHub 同步
│
├── docs/                         ← 文档（部分已删除）
├── assets/                       ← 静态资源
└── profile-readme/               ← GitHub Profile README
```

---

## 二、服务端口分配

| 端口 | 服务 | 状态 | 说明 |
|------|------|------|------|
| 5432 | PostgreSQL | Docker | 共享数据库 |
| 8000 | Alpha-ID | ✅ 运行中 | 身份层 API |
| 2002 | Nebula | ❌ 未启动 | 执行层（工作流） |
| 3000 | Flow Web | ❌ 未启动 | Next.js 前端（非官网） |
| 3001 | Flow API | ❌ 未启动 | Fastify API |
| 3004 | DS Dashboard | ✅ 运行中 | 电商后端 |
| 8090 | Ghost Gateway | ✅ 运行中 | 统一 API 网关 |
| 80 | Caddy | ❌ 未启动 | 生产反向代理 |

---

## 三、已配置但未集成的服务

### 3.1 环境变量中已配置

| 服务 | 配置文件 | 状态 |
|------|----------|------|
| DeepSeek LLM | `.env.example` | 有模板，无真实 key |
| 飞书机器人 | `.env.example` | 有模板，无真实 key |
| 百度地图 | `.env.example` | 有模板，无真实 key |
| Shoplazza | `.env.example` | 有模板，DS 已连接 |
| PostgreSQL | `docker-compose.yml` | 有配置，需 Docker 启动 |

### 3.2 用户已完成但未体现在代码中

根据用户描述，已完成以下申请/注册：
- **支付宝** — 申请了支付接口
- **短信验证** — 申请了短信服务
- **人脸验证** — 申请了活体核验服务

**问题：** 这些服务的 SDK/Key/配置尚未集成到代码中。

---

## 四、六层架构 vs 实际对照

| 文档描述的六层 | 对应代码 | 完成度 |
|---------------|----------|--------|
| **Layer 1: 身份层** | `alphaid/` | 70% — DID/记忆/A2A 有代码，实名核验未接 |
| **Layer 2: 记忆层** | `alphaid/` (双链记忆) | 40% — 有结构，无真实数据沉淀 |
| **Layer 3: 网关层** | `ghost-main/gateway/` | 50% — 有统一网关，未接 Caddy |
| **Layer 4: 调度层** | `core/dispatcher/` | 20% — 只有关键词匹配 |
| **Layer 5: 业务层** | `DS/`, `flow/`, `Ghost.html` | 60% — 电商可用，前端未统一 |
| **Layer 6: 商业层** | ❌ 不存在 | 0% — 支付/版权/积分未实现 |

---

## 五、核心问题诊断

### 问题 1：代码散落，无统一入口
- alphaid:8000、DS:3004、nebula:2002 各自为政
- Ghost.html 直接调多个端口
- **解决：** ✅ 已建 Ghost Gateway (18080)

### 问题 2：已做的工作未提交
- 大量未跟踪文件：`ghost-main/`, `obsidian-plugin/`, `DS/`, `ARCHITECTURE.md` 等
- 大量已修改未提交：`Ghost.html`, `alphaid/`, `nebula/`, `flow/` 等
- **解决：** ⏳ 需要提交

### 问题 3：用户申请的服务未集成
- 支付宝、短信、人脸 — 只有申请，没有代码
- **解决：** ⏳ 需要 SDK 集成

### 问题 4：Agent 文档过时
- `AGENT_PLAYBOOK.md` 和 `PROJECT_BRAIN.md` 不反映当前状态
- **解决：** ⏳ 需要更新

### 问题 5：两个前端
- `Ghost.html`（已部署）+ `flow/apps/web/`（未部署）
- **解决：** ⏳ 需要明确：Ghost.html 是唯一官网，flow/web 要么删除要么明确用途

---

## 六、Git 状态

### 未跟踪的文件（关键）
- `ghost-main/` — 统一网关
- `obsidian-plugin/` — Obsidian 插件
- `DS/` — 电商后端
- `ARCHITECTURE.md` — 架构文档
- `AGENT_PLAYBOOK.md` — Agent 手册
- `PROJECT_BRAIN.md` — 项目大脑
- `profile-readme/` — GitHub Profile

### 已修改未提交
- `Ghost.html` — 连接真实 API
- `alphaid/` — CORS + 新 API
- `nebula/` — 配置更新
- `flow/` — aid.service.ts 代理
- `docker-compose*.yml` — 配置更新
- `Caddyfile` — 端口修正

### 分支状态
- 当前分支：`master`
- 领先 origin/master 3 个 commit
- 无 stash，无其他分支

---

## 七、下一步行动（按优先级）

### P0: 立即做
1. **提交所有未提交工作** — 防止再次丢失
2. **更新 Agent 文档** — PROJECT_BRAIN.md + AGENT_PLAYBOOK.md
3. **集成支付宝/短信/人脸** — 把已申请的服务接入 alphaid

### P1: 本周
4. **启动 Nebula** — 连接工作流引擎
5. **Caddy 配置** — 统一入口 :80
6. **PostgreSQL Docker 启动** — 数据库持久化

### P2: 本月
7. **实名 DID 链路** — 注册→人脸→Alpha-ID→双链记忆
8. **Obsidian 插件完善** — 双向同步
9. **飞书机器人** — 连接 TwinBrain

---

*审计完成。这是一份真实反映项目状态的文档，不是愿景。*
