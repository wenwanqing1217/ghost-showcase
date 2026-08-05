<!-- STATUS: ACTIVE -->
<!-- 数据流总览：每条业务闭环的路径、数据形态、真实验证状态。 -->
<!-- 与 GHOST.md 互补：GHOST.md 讲架构，本文件讲"数据怎么流、哪条通了、哪条没通"。 -->

# Ghost Platform — 数据流与验证状态

> 本文件回答三个问题：**平台数据怎么流？每条链路是否真的跑通？如何复现验证？**
> 所有状态均来自 2026-08-05 实际执行结果（本地测试 + CI 配置），不写未经验证的声明。

---

## 1. 服务拓扑

```
                        ┌──────────────┐
   飞书 / Web / NURO ──▶ │  Gateway     │◀── 电商 Webhook (OneBound)
                        │  :18080      │
                        └──┬───────┬───┘
          ┌────────────────┼───────┼───────────────────────┐
          ▼                ▼       ▼                       ▼
   ┌───────────┐   ┌────────────┐ ┌─────────────┐   ┌──────────────┐
   │ Alpha-ID  │   │  Nebula    │ │    Flow     │   │  Orchestrator│
   │ :8000     │   │  :2002     │ │   :3036     │   │  :19090      │
   │ 身份/记忆 │   │ 工作流/飞书 │ │ Fastify 编排 │   │ 调度/技能换优 │
   │ A2A/信用  │   │ 指令中心    │ │             │   │              │
   └───────────┘   └────────────┘ └─────────────┘   └──────┬───────┘
                                                          ▼
                                              ┌───────────────┐
                                              │ tool-a / tool-b│
                                              │ :8081 / :8082 │
                                              └───────────────┘
   ┌─────────────┐    ┌─────────────────┐    ┌─────────────────────┐
   │ Ghost DS    │    │ Net-Agent       │    │ Redis :6379         │
   │ :3001(host) │    │ :18180          │    │ (EventBus + 缓存)    │
   │ 电商看板    │    │ 网络运维         │    │ PostgreSQL :5432     │
   └─────────────┘    └─────────────────┘    └─────────────────────┘
```

### 端口与进程（docker-compose.yml 为准）

| 服务 | 容器内 | 宿主机 | 说明 |
|:-----|:------:|:------:|:-----|
| Gateway | 18080 | 18080 | 统一 API 网关，对外唯一入口 |
| Alpha-ID | 8000 | 8000 | 身份 + 记忆 + A2A + 信用 |
| Nebula | 2002 | 2002 | 工作流 + 飞书指令中心 + 短剧预审 |
| Flow | 3036 | 3036 | Fastify 工作流编排 |
| Orchestrator | 19090 | 19090 | 后台循环 + 技能基准换优 |
| Net-Agent | 18180 | 18180 | 路由器等网络运维 |
| Ghost DS | 3000 | 3001 | Next.js 电商看板 |
| tool-a / tool-b | 8081/8082 | 8081/8082 | 代码生成 / 优化工具 |
| Redis | 6379 | 6379 | EventBus（Redis Streams）+ 缓存 |
| PostgreSQL | 5432 | 5432 | 持久化 |

---

## 2. 业务闭环（数据怎么流）

### 闭环 A：飞书指令 → 内容生产（零成本运营主线）

```
用户发飞书消息 "文案 商品=香薰 卖点=xx 价格=59"
  → Nebula :2002/api/v1/feishu/webhook           (feishu_webhook.py)
  → route_command() 指令路由                     (feishu_commands.py：文案/视频/短剧/状态…)
  → 调用 Ghost DS :3001/api/ai/copy 等 API       (DS src/app/api/ai/*)
  → 生成闲鱼+小红书文案 / 种草视频脚本
  → FeishuSender 回复到飞书会话
未识别的指令 → 交给 AI 闲聊（Gateway /v1/human/chat → Alpha-ID）
```

- 涉及文件：`nebula/src/mindflow_map/api/feishu_commands.py`、`feishu_webhook.py`、`feishu_sender.py`、`DS/src/app/api/ai/copy/route.ts`、`DS/src/app/api/ai/channel-copy/route.ts`
- **验证**：⚠️ 单元测试覆盖 `route_command` 参数解析；端到端（飞书真实收发）需 Docker 全栈 + 飞书凭据，由 CI e2e 与人工联调验证

### 闭环 B：DS 看板 ↔ Gateway ↔ Alpha-ID（聊天 + 记忆闭环）

```
DS 页面 → NEXT_PUBLIC_GATEWAY_URL → Gateway /v1/human/chat
  → Gateway routes/human.py (chat) → Alpha-ID :8000 对话/记忆接口
  → 记忆写入 (memory/store → dual_chain) → MemoryGraph 标签关联
DS /api/v1/human/*、/api/v1/obsidian/*、/api/v1/workflow/* 同样经 Gateway 代理
```

- 涉及文件：`ghost-main/gateway/routes/human.py`、`DS/src/lib/gateway-client.ts`、`DS/src/app/api/v1/human/**`
- **验证**：✅ `gateway/tests/test_chat_proxy.py`；✅ `alphaid` 859 测试含 `test_dual_chain.py`/`test_memory_store.py`；⚠️ 全栈链路由 `scripts/e2e_test.mjs`（quick-register + memory store）在 CI 验证

### 闭环 C：电商数据接入（OneBound Webhook）

```
OneBound 平台推送订单/商品事件 → DS :3001/api/webhook/onebound
  → DS src/lib/onebound-webhook.ts 校验 + 归一化
  → EventBus.publish("order:created" 等)  (DS src/lib/eventbus-init.ts)
  → DS 订单/商品 API 落库（prisma + PostgreSQL）
  → 看板 /orders /products 渲染
```

- 涉及文件：`DS/src/app/api/webhook/onebound/route.ts`、`DS/src/lib/onebound-webhook.ts`、`DS/src/lib/eventbus-init.ts`
- **验证**：✅ `DS/src/app/api/webhook/onebound/route.test.ts`（5 测试，含事件发布参数断言）；✅ `DS/src/lib/eventbus.test.ts`

### 闭环 D：A2A 智能体市场 + 信用结算

```
DS 智能体市场页 → Gateway /v1/agent/a2a/{agents,graph,skills,market,call}
  → Alpha-ID :8000 AgentGraph（运行时计算拓扑） / 注册表 / 信用钱包
  → 调用计费：A2A_CALL_RESULT 事件 → Credits 钱包扣费（平台抽成 10%）
  → 审计日志 (audit_store)
```

- 涉及文件：`alphaid/projects/src/core/agent_graph.py`、`src/api/a2a.py`、`src/api/credits.py`、`DS/src/app/api/v1/agent/a2a/**`
- **验证**：✅ `alphaid` 测试 `test_agent_graph.py`、`test_registration.py`、`test_credits_growth.py`；⚠️ 钱包→调用→扣费全链路需 Docker e2e

### 闭环 E：工作流编排执行（Nebula / Flow → 工具）

```
Gateway /v1/workflow/execute 或 Nebula /api/v1/workflow/*
  → Nebula workflows/engine.py 或 Flow apps/api /workflow
  → 调用 tool-a :8081（代码生成）/ tool-b :8082（优化）/ 自动化（douyin/shopify）
  → 结果回写 → 事件流 (Nebula /api/v1/events)
```

- 涉及文件：`nebula/src/mindflow_map/workflows/engine.py`、`nebula/src/mindflow_map/api/workflow.py`、`flow/apps/api/src/routes/workflow.ts`
- **验证**：✅ `nebula` 153 测试含 `test_workflow.py`；✅ `flow` 30 测试含 `workflow.test.ts`（7）；⚠️ 跨服务真实执行需 Docker e2e

### 闭环 F：OrchestratorEngine 调度与技能换优

```
Orchestrator :19090（orchestrator/main.py）
  → gateway_sync_loop：轮询 Gateway 事件 → 分发给 agent
  → OPTIMAL_SWAP（每日）：用真实调用日志（A2A_CALL_RESULT）基准评分
    基础设施技能评分低的 → 自动替换为更高分候选（免费优先，prefer=paid 才用付费）
```

- 涉及文件：`orchestrator/main.py`、`alphaid/projects/src/orchestrator/engine.py`、`alphaid/projects/src/core/agent_graph.py`
- **验证**：✅ `orchestrator/test_orchestrator.py`（7 测试）；⚠️ OPTIMAL_SWAP 依赖真实调用日志累积，需运行态数据

---

## 3. 验证状态矩阵（2026-08-05 实测）

### 3.1 单元测试（本机 Windows 实际执行）

| 子项目 | 命令 | 结果 | 耗时 |
|:-------|:-----|:-----|:-----|
| alphaid/projects（子模块） | `python -m pytest tests/ -q` | **859 passed**, 98 skipped | 57s |
| nebula | `python -m pytest tests/ -q` | **153 passed** | 18s |
| gateway | `python -m pytest tests/ -q` | **32 passed**, 20 skipped | 3s |
| orchestrator | `python -m pytest . -q` | **7 passed** | 1.5s |
| net-agent | `python -m pytest net_agent_server/ -q` | **12 passed**（auth + adapter） | 1s |
| DS（Next.js） | `npm test` | **45 passed**（3 文件） | 1s |
| flow（Monorepo） | `npm test` | **30 passed**（7 文件） | 10s |
| **合计** | | **1138 passed** | |

> 跳过项（118）均为需要外部依赖（真实 LLM API / 飞书 / 短信 / Docker 服务）的用例，属预期跳过。

### 3.2 端到端（需 Docker 全栈）

| 链路 | 验证脚本 | 状态 |
|:-----|:---------|:-----|
| 服务健康 + quick-register + 聊天 | `scripts/e2e_test.mjs --wait` | ⚠️ 配置完毕，随 CI 执行 |
| 记忆写入 + A2A 审计/图谱/技能 | `scripts/e2e_test.mjs --wait` | ⚠️ 同上 |
| DS 健康 + 商品 + 订单 API | `scripts/e2e_test.mjs --wait` | ⚠️ 同上 |

**本机如何跑全栈 E2E**：
```bash
# 1. 启动 Docker Desktop
# 2. 配置环境变量（仓库根目录 .env 或环境变量）
export DB_USER=ghost DB_PASSWORD=xxx DB_NAME=ghost
# 3. 启动（跳过 MoneyPrinterTurbo，仓库不含该目录）
docker compose up -d --build db redis nebula alphaid flow gateway netagent orchestrator tool-a tool-b ghost-ds
# 4. 验证
node scripts/e2e_test.mjs --wait
```

### 3.3 已确认未落地（诚实清单）

| 项 | 状态 | 说明 |
|:---|:-----|:-----|
| 飞书真实收发端到端 | ❌ 未在本机验证 | 需飞书 App 凭据 + 公网回调；CI 亦无法自动验证 |
| MoneyPrinterTurbo 视频生成 | ❌ 未集成 | docker-compose 引用 `./MoneyPrinterTurbo` 目录，仓库未包含；DS 的"视频生成"调用会失败 |
| OPTIMAL_SWAP 自动换优 | ⚠️ 有实现无运行态 | 依赖真实调用日志，需长时间运行积累数据 |
| Net-Agent 真实路由器操作 | ⚠️ 部分 | 单元测试就绪，真实设备操作需硬件环境 |
| 闲鱼/小红书真实发布 | ❌ 未落地 | 仅文案生成，发布动作未接入（定位为人工完成交易） |

---

## 4. 复现验证（给新模型/新人的标准动作）

```bash
make smoke          # 一键：所有子项目单元测试（无需 Docker）
make lint           # 一键：ruff + eslint
node scripts/e2e_test.mjs --wait   # 全栈 E2E（需 Docker）
```

任何改动合入前，必须满足：`make smoke` 全绿 + 改动模块的 lint 通过。

---

*本文件随 WORK_LOG.md 同步更新；状态变化时先改这里，再改 PROJECT_STATUS_REPORT.md。*
