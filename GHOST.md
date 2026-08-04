# Ghost Platform — 项目总览

> **版本**: 1.0 | **2026-08-04**  
> **原则**: 一个真相，一份文档，一个节奏。所有信息在此统一，不分散到多份文档。

---

## 1. 项目定位

**Web4.0 AtoA（Agent-to-Anything）全域自主智能体操作系统**

三层堆栈：
- 理念层：Denny AI（人机共生的设计哲学）
- 系统中枢：Alpha-ID（DID 身份 + 双链记忆 + AgentLoop）
- 底层网络：Ghost AtoA（统一网关 + 事件总线 + 服务编排）

不做单点AI工具、不做工作流编排、不局限于技能市场。

---

## 2. 七层架构

```
L1 感知层 — 输入来源（飞书/Web/微信/Telegram/Doubao/NURO）
L2 身份层 — DID + 身份验证（Alpha-ID :8000）
L3 工作流层 — 流程编排（Nebula :2002）
L4 调度层 — 任务调度（Orchestrator :19090）
L5 网关层 — API 路由（Gateway :18080）
L6 业务层 — 电商运营（Ghost DS :3000）
L7 知识层 — 记忆 + 知识图谱（MemoryGraph / Obsidian）
```

---

## 3. 服务清单

| 服务 | 端口 | 框架 | 职责 | 状态 |
|:-----|-----:|:-----|:-----|:-----|
| Gateway | 18080 | FastAPI | 统一 API 网关，四层路由 | ✅ 95% |
| Alpha-ID | 8000 | FastAPI | DID 身份、双链记忆、A2A | ✅ 95% |
| Nebula | 2002 | FastAPI | 工作流引擎、飞书/微信 webhook | ✅ 85% |
| Ghost DS | 3000 | Next.js 14 | 电商看板、订单/商品管理 | ✅ 90% |
| Orchestrator | 19090 | FastAPI | 任务调度（ToolA/ToolB） | ⚠️ 20% → 80%（Phase 1 后） |
| Feishu Bot | — | Python | 飞书 WebSocket + HTTP 双通道 | ✅ 80% |
| Feishu Consumer | — | Python | Redis Streams → 飞书通知 | ✅ 80% |
| Net-Agent | 18180 | FastAPI | 路由器管理 | ⚠️ 60% |
| Flow | 3036 | Fastify | 工作流前端门户 | ⚠️ 40% |
| Redis | 6379 | — | 缓存 + 事件总线 + 任务队列 | ✅ 95% |
| PostgreSQL | 5432 | — | 共享数据库 | ✅ 90% |
| Doubao Reader | — | Python | 豆包桌面日志解析（库，非服务） | ✅ 85% |
| NURO | — | Python | 桌面宠物，本地 AI | ⚠️ 30% |

---

## 4. 术语表（TERM 规则）

| 标准术语 | 是什么 | 禁止别名 | 文件参考 |
|:---------|:-------|:---------|:---------|
| `OrchestratorEngine` | 统一后台循环管理 | MasterOrchestrator | `orchestrator/engine.py` |
| `EventBus` | Redis Streams 跨服务事件总线 | blinker | `core/event_bus.py` |
| `AgentGraph` | A2A 网络拓扑（运行时计算） | agent_graph | `a2a.py:447` |
| `MemoryGraph` | 记忆知识图谱（按标签关联） | memory graph | `memory_graph.py` |
| `TwinBrain` | 智能体大脑（唯一实例） | brain | `core/twin_brain.py` |
| `ChannelAdapter` | 渠道适配器基类 | adapter | `core/orchestrator.py` |
| `GhostDS` | Next.js 电商看板（端口 3000） | DS | `DS/` |
| `Gateway` | 统一 API 网关（端口 18080） | 网关 | `ghost-main/gateway/` |

**代码注释规范**：在关键类/函数定义处加 `# TERM:` 注释。

---

## 5. 三条主线

### 豆包知识输入线
```
Doubao Reader（桌面日志解析）
  → Gateway /v1/internal/doubao/capture
  → Alpha-ID dual-chain/save（记忆存储）
  → Obsidian vault（本地笔记）
```

### 飞书助理线
```
飞书 WebSocket/Webhook
  → Nebula /api/v1/wechat（消息解析）
  → Gateway /v1/human/chat（统一入口）
  → Alpha-ID /api/v1/agent/chat（TwinBrain + AgentLoop）
  → 飞书回复
```

### Ghost DS 电商线
```
OneBound/Shoplazza（货源/店铺）
  → DS 前端（订单/商品管理）
  → Redis Streams（事件发布）
  → Feishu Consumer（飞书通知）
```

---

## 6. 已知问题

### P0 — 必须修复
- [x] 飞书 webhook → `/v1/chat` 断裂（已修复：Gateway 加别名路由）
- [x] Redis Streams 消费休眠（已修复：eventbus-init.ts 加 startConsuming）
- [x] 两个 MasterOrchestrator 同名冲突（已修复：合并为 OrchestratorEngine）
- [x] EventBus blinker 与 TS Redis Streams 不互通（已修复：Python 改用 Redis Streams）
- [x] eventbus-server.ts 重复（已修复：合并到 eventbus-init.ts）

### P1 — 应该修复
- [x] wechat.py 未接入 Gateway（已修复：加 /v1/internal/webhook/wechat 路由）
- [ ] Ghost DS CI 加入 GitHub Actions（部分完成：加了 job，需验证跑通）
- [ ] Orchestrator 功能评分 20% → 80%（ToolA/ToolB 已接入 HTTP，需真实服务）

### P2 — 后续优化
- [ ] ToolA/ToolB 接入真实服务（当前为 stub）
- [ ] Flow 工作流前端 (:3036) 接入 Gateway
- [ ] NURO 桌面宠物功能完善
- [ ] Net-Agent 功能完善（60% → 90%）
- [ ] 术语注释标准化（已开始：# TERM: 注释）

---

## 7. 开发规范

### 提交信息格式
```
<type>(<scope>): <description>
```
- type: feat / fix / refactor / perf / docs / chore / test
- scope: orchestrator / eventbus / gateway / alphaid / nebula / ds / feishu / infra

### 死代码处理
**死代码是用来盘活的，不是用来删的。** 发现死代码 → 先尝试接入活跃链路，确认无价值后才删除。

### 测试
```bash
make test          # 全量测试
make lint          # 全量 lint
make up            # 启动所有服务
make ps            # 查看服务状态
```

### CI
GitHub Actions 自动运行：
- Python 服务：ruff lint + pytest
- Node.js 服务：eslint + build
- E2E：Docker Compose 全栈验证

---

## 8. 每周节奏

每周做三件事：
1. **看状态**：`make ps` 有 unhealthy 吗？CI 全绿了吗？
2. **进一个问题**：从第 6 节挑一个 P0/P1 做掉
3. **关一个问题**：做完的划掉，更新本节

**持续 4 周，项目从"一盘散沙"变成"有脉搏的系统"。**

---

*本文件是 Ghost Platform 的唯一真相源。所有其他文档已合并到此。*
