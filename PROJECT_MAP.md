<!-- STATUS: ACTIVE -->
<!-- L4 术语：术语表、端口汇总、文档层级、冲突解决。 -->

# PROJECT_MAP — 术语与端口权威表

> 权威层级 L4。回答：**项目里一个概念叫什么、禁止叫什么、端口是谁的、文档谁说了算。**

---

## 1. 术语表（TERM 规则）

> 代码中遇到以下概念必须使用标准术语，不得自行创造（详见 [AGENTS.md](./AGENTS.md#1-术语标准term-规则)）。

| 标准术语 | 是什么 | 禁止使用的别名 |
|:---------|:-------|:---------------|
| `OrchestratorEngine` | 统一后台循环管理（orchestrator/engine.py） | MasterOrchestrator |
| `EventBus` | Redis Streams 跨服务事件总线（core/event_bus.py） | blinker, event bus |
| `AgentGraph` | A2A 网络拓扑（运行时计算，非持久化） | agent_graph, topology |
| `MemoryGraph` | 记忆知识图谱（按标签关联） | memory graph |
| `TwinBrain` | 智能体大脑（唯一实例） | brain, 大脑 |
| `ChannelAdapter` | 渠道适配器基类（飞书/Web/微信/Telegram） | adapter, 适配器 |
| `GhostDS` | Next.js 电商看板（宿主端口 3001） | DS, dashboard |
| `Gateway` | 统一 API 网关（端口 18080） | 网关 |

## 2. 端口汇总

| 端口 | 服务 | 说明 |
|:----:|:-----|:-----|
| 18080 | Gateway | 对外唯一 API 入口 |
| 8000 | Alpha-ID | 身份 + 记忆 + A2A + 信用 |
| 2002 | Nebula | 工作流 + 飞书指令中心 |
| 3036 | Flow | Fastify 编排 |
| 19090 | Orchestrator | 后台循环 + 技能换优 |
| 18180 | Net-Agent | 网络运维 |
| 3001 | Ghost DS（宿主） | 容器内 3000 |
| 8081 / 8082 | tool-a / tool-b | 代码生成 / 优化 |
| 8080 | MoneyPrinterTurbo | 可选 profile: media |
| 6379 | Redis | EventBus + 缓存 |
| 5432 | PostgreSQL | 持久化 |

## 3. 文档权威层级

| 层级 | 文档 | 用途 |
|:-----|:-----|:-----|
| L1 宪法 | [GHOST.md](./GHOST.md) | 项目定位、七层架构、愿景 |
| L2 架构 | [ARCHITECTURE.md](./docs/architecture/ARCHITECTURE.md) | 服务设计、数据流、路由表 |
| L2 数据流 | [DATA_FLOW.md](./DATA_FLOW.md) | 数据怎么流 + 验证状态 |
| L3 地图 | [SYSTEM_MAP.md](./SYSTEM_MAP.md) | 服务拓扑、调用链、部署图 |
| L4 术语 | **本文件** | 术语表、端口表、冲突解决 |
| L5 计划 | [PHASE1_PLAN.md](./PHASE1_PLAN.md) | 实施路线图 |
| L6 状态 | [PROJECT_STATUS_REPORT.md](./PROJECT_STATUS_REPORT.md) | 服务健康、功能评分 |
| L7 决策 | [DECISIONS.md](./DECISIONS.md) | 技术决策记录 |
| L8 日志 | [WORK_LOG.md](./WORK_LOG.md) | 每日工作记录 |

## 4. 冲突解决记录

| 冲突 | 裁决 |
|:-----|:-----|
| `MasterOrchestrator` vs `OrchestratorEngine` | 保留 `MasterOrchestrator` 仅作兼容层，内部委托 `OrchestratorEngine`；新代码禁止创建 |
| `blinker` vs `EventBus` | 一律走 `EventBus` 接口（on/emit/start_consuming），禁止直接调 Redis Streams 命令 |
| Ghost DS 端口 3000 vs 3004 vs 3001 | 容器内 3000、宿主 3001；本地 dev 3000；health 脚本 3000 |
| `alpha_id/` vs `alphaid/projects/src/` | 源码根 `alphaid/projects/src/`；旧路径仅 Git 历史保留 |

## 5. 变更记录

| 日期 | 变更 |
|:-----|:-----|
| 2026-08-05 | 初版创建；端口表与 docker-compose.yml 对齐 |

---

*改术语/端口 → 同步本文件 + AGENTS.md §1/§2 + GHOST.md §5/§7。*
