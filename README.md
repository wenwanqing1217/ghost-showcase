<!-- STATUS: ACTIVE -->
<!-- 项目入口：快速了解 + 快速启动 + 真实状态。数据流详见 DATA_FLOW.md。 -->

# Ghost Platform

<p align="center">
  <b>AI 运营工具平台</b> —— 一人一个 Alpha-ID，飞书当指挥中心，零成本跑通"种草 → 成交 → 出海"。
</p>

<p align="center">
  <a href="https://github.com/wenwanqing1217/ghost-showcase/actions"><img src="https://img.shields.io/github/actions/workflow/status/wenwanqing1217/ghost-showcase/ci.yml?branch=master&label=CI" alt="CI"></a>
  <a href="https://github.com/wenwanqing1217/ghost-showcase"><img src="https://img.shields.io/badge/tests-1138%20passed-green" alt="tests"></a>
  <a href="https://github.com/wenwanqing1217/ghost-showcase/blob/master/LICENSE"><img src="https://img.shields.io/github/license/wenwanqing1217/ghost-showcase" alt="license"></a>
</p>

**一句话定位**：把 AI 能力（文案、选品、履约）串成可执行闭环，飞书里发一条指令就能干活，不依赖任何电商平台 API，起步成本为零。

---

## 目录

- [架构与数据流](#架构与数据流)
- [服务清单](#服务清单)
- [快速启动](#快速启动)
- [验证与测试](#验证与测试)
- [核心业务闭环](#核心业务闭环)
- [文档索引](#文档索引)
- [真实状态](#真实状态)

---

## 架构与数据流

```
   飞书 / Web / NURO ──▶  Gateway :18080  ◀── 电商 Webhook (OneBound)
                          ┌──────┬──────┐
                          ▼      ▼      ▼
                   Alpha-ID    Nebula    Flow      Orchestrator
                   :8000      :2002     :3036     :19090
                   身份/记忆   工作流/飞书 编排      调度/技能换优
                    A2A/信用   指令中心    tool-a/b   EventBus
```

> **数据怎么流？每条链路通没通？** → 见 [DATA_FLOW.md](./DATA_FLOW.md)（6 条业务闭环 + 实测验证矩阵）

---

## 服务清单

| 服务 | 端口 | 说明 |
|:-----|:----:|:-----|
| Gateway | 18080 | 统一 API 网关，对外唯一入口 |
| Alpha-ID | 8000 | 身份层（DID）+ 记忆 + A2A 智能体 + 信用钱包 |
| Nebula | 2002 | 工作流引擎 + 飞书指令中心 + 短剧预审 |
| Flow | 3036 | Fastify 工作流编排 |
| Orchestrator | 19090 | 后台循环 + 技能基准换优（OPTIMAL_SWAP） |
| Net-Agent | 18180 | 路由器等网络运维 |
| Ghost DS | 3001 | Next.js 电商运营看板 + 智能体市场 |
| tool-a / tool-b | 8081 / 8082 | 代码生成 / 优化工具 |
| Redis | 6379 | EventBus（Redis Streams）+ 缓存 |
| PostgreSQL | 5432 | 持久化 |

---

## 快速启动

### 方式一：Docker 全栈（推荐）

```bash
# 0. 前置：Docker Desktop + git
git clone --recursive https://github.com/wenwanqing1217/ghost-showcase.git
cd ghost-showcase

# 1. 环境变量
cp .env.example .env                  # 编辑 DB_PASSWORD
cp DS/.env.example DS/.env
cp ghost-main/gateway/.env.example ghost-main/gateway/.env
cp alphaid/projects/.env.example alphaid/projects/.env

# 2. 启动（跳过 MoneyPrinterTurbo，仓库未包含该目录）
export DB_USER=ghost DB_PASSWORD=<你的密码> DB_NAME=ghost
docker compose up -d --build db redis nebula alphaid flow gateway netagent orchestrator tool-a tool-b ghost-ds

# 3. 验证
curl http://localhost:18080/health
node scripts/e2e_test.mjs --wait      # 全栈 E2E 校验
```

### 方式二：本地开发（无 Docker，跑单元测试）

```bash
make smoke        # 一键跑全部 6 个子项目单元测试（无需 Docker）
```

---

## 验证与测试

**2026-08-05 实测：1138 个测试通过**

| 子项目 | 结果 |
|:-------|:-----|
| alphaid/projects | 859 passed |
| nebula | 153 passed |
| gateway | 32 passed |
| orchestrator | 7 passed |
| net-agent | 12 passed |
| Ghost DS | 45 passed |
| flow | 30 passed |

CI（GitHub Actions）覆盖：路径过滤 → 各子项目 lint + test + build → Docker 全栈 E2E → 总门禁。详见 [.github/workflows/ci.yml](.github/workflows/ci.yml)。

---

## 核心业务闭环

| # | 闭环 | 一句话 |
|:--|:-----|:-------|
| A | 飞书指令 → 内容生产 | 飞书发「文案 商品=香薰 卖点=xx」→ Nebula 路由 → DS 生成闲鱼/小红书文案 |
| B | 看板 ↔ 网关 ↔ 身份 | DS 页面聊天/记忆 → Gateway → Alpha-ID 双链记忆 |
| C | 电商数据接入 | OneBound Webhook → DS 事件总线 → 订单/商品落库 |
| D | A2A 智能体市场 | 注册/发现/调用智能体，信用钱包计费（平台抽成 10%） |
| E | 工作流执行 | Nebula / Flow → tool-a/b 代码生成与优化 |
| F | 调度与换优 | OrchestratorEngine 每日用真实调用日志替换低分技能 |

---

## 文档索引

| 文档 | 层级 | 用途 |
|:-----|:-----|:-----|
| [GHOST.md](./GHOST.md) | L1 宪法 | 项目定位、七层架构、愿景 |
| [ARCHITECTURE.md](./docs/architecture/ARCHITECTURE.md) | L2 架构 | 服务设计、数据流、路由表 |
| [DATA_FLOW.md](./DATA_FLOW.md) | L2 数据流 | **数据怎么流 + 每条链路验证状态** |
| [SYSTEM_MAP.md](./SYSTEM_MAP.md) | L3 地图 | 服务拓扑、调用链、部署图 |
| [PROJECT_MAP.md](./PROJECT_MAP.md) | L4 术语 | 术语表、端口表、冲突解决 |
| [DECISIONS.md](./DECISIONS.md) | L7 决策 | 技术决策记录 |
| [PROJECT_STATUS_REPORT.md](./PROJECT_STATUS_REPORT.md) | L6 状态 | 模块健康、功能评分 |
| [WORK_LOG.md](./WORK_LOG.md) | L8 日志 | 每日工作记录 |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | — | 贡献规范 |

---

## 真实状态

**已落地并验证**：
- ✅ 6 个子项目 1126 个单元测试通过，CI 可在 GitHub 上完整运行
- ✅ 飞书指令中心（文案/视频/短剧/状态）参数路由 + 单元测试
- ✅ OneBound Webhook → EventBus → 订单落库（含事件参数断言）
- ✅ A2A 智能体注册（Ed25519/API Key 双模式）+ 信用钱包 + 审计日志
- ✅ OrchestratorEngine 统一后台循环 + 每日 OPTIMAL_SWAP

**未落地（诚实清单，详见 [DATA_FLOW.md](./DATA_FLOW.md#33-已确认未落地诚实清单)）**：
- ❌ 飞书真实收发端到端（需 App 凭据 + 公网回调）
- ❌ MoneyPrinterTurbo 视频生成（仓库未包含该目录）
- ❌ 闲鱼/小红书自动发布（定位为人工完成交易，仅文案生成）
- ⚠️ OPTIMAL_SWAP 自动换优依赖真实调用日志积累

---

*项目文档权威层级见 AGENTS.md 第 7 节；改代码必须同步改文档。*
