<!-- STATUS: ACTIVE -->
<!-- L3 地图：服务拓扑、调用链、端口、部署关系。数据流细节见 DATA_FLOW.md。 -->

# SYSTEM_MAP — 服务拓扑与部署地图

> 权威层级 L3。回答：**服务之间怎么连、依赖谁、走哪个端口、怎么部署。**
> 数据如何流动见 [DATA_FLOW.md](./DATA_FLOW.md)（L2 数据流）。

---

## 1. 服务拓扑

```
                    ┌──────────────┐   OneBound Webhook
 飞书 ─┐            │   Gateway    │◀───────────────────
 Web ──┼──────────▶ │    :18080    │                     │
 NURO ─┘            │ 对外唯一入口  │                     ▼
                    └──┬───┬───┬───┘            ┌─────────────────┐
                       │   │   │                │    Ghost DS     │
        ┌──────────────┤   │   └──────────┐     │  :3001 (host)   │
        ▼              ▼                  ▼     │  :3000 (容器)    │
 ┌────────────┐ ┌────────────┐  ┌────────────┐  │ 电商看板+市场    │
 │  Alpha-ID  │ │   Nebula   │  │    Flow    │  └───────┬─────────┘
 │   :8000    │ │   :2002    │  │   :3036    │          │ NEXT_PUBLIC
 │ 身份/记忆  │ │ 工作流/飞书 │  │ Fastify 编排│          │ _GATEWAY_URL
 │ A2A/信用   │ │ 指令中心    │  │            │          ▼
 └────────────┘ └────────────┘  └────────────┘       (回 Gateway)
                    ▲
                    │ Orchestrator :19090 ──▶ tool-a :8081 / tool-b :8082
                    │       (调度 + OPTIMAL_SWAP)
   ┌───────────────────────────────────────────────────────┐
   │        Redis :6379  (EventBus Redis Streams + 缓存)     │
   │        PostgreSQL :5432 (持久化)                        │
   └───────────────────────────────────────────────────────┘
```

## 2. 调用链速查

| # | 链路 | 起点 → 终点 | 详情 |
|:--|:-----|:-----------|:-----|
| A | 飞书指令 → 内容 | 飞书 → Nebula `:2002/api/v1/feishu/webhook` → DS `:3001/api/ai/*` | [DATA_FLOW.md §2-A](./DATA_FLOW.md) |
| B | 看板 ↔ 身份 | DS → Gateway `:18080/v1/human/*` → Alpha-ID `:8000` | [DATA_FLOW.md §2-B](./DATA_FLOW.md) |
| C | 电商数据 | OneBound → DS `:3001/api/webhook/onebound` → EventBus → PG | [DATA_FLOW.md §2-C](./DATA_FLOW.md) |
| D | A2A 市场 | DS → Gateway `:18080/v1/agent/a2a/*` → Alpha-ID | [DATA_FLOW.md §2-D](./DATA_FLOW.md) |
| E | 工作流 | Gateway `:18080/v1/workflow/*` → Nebula / Flow → tool-a/b | [DATA_FLOW.md §2-E](./DATA_FLOW.md) |
| F | 调度换优 | Orchestrator `:19090` → Gateway → EventBus | [DATA_FLOW.md §2-F](./DATA_FLOW.md) |

## 3. 端口表（与 docker-compose.yml 对齐）

| 服务 | 容器内 | 宿主机 | 健康检查 |
|:-----|:------:|:------:|:---------|
| Gateway | 18080 | 18080 | `/health` |
| Alpha-ID | 8000 | 8000 | `/health` |
| Nebula | 2002 | 2002 | `/health` |
| Flow | 3036 | 3036 | `/health` |
| Orchestrator | 19090 | 19090 | `/health` |
| Net-Agent | 18180 | 18180 | `/health` |
| Ghost DS | 3000 | 3001 | `/api/health` |
| tool-a | 8081 | 8081 | `/health` |
| tool-b | 8082 | 8082 | `/health` |
| MoneyPrinterTurbo | 8080 | 8080 | `/api/v1/tasks`（**可选 profile: media**） |
| Redis | 6379 | 6379 | `redis-cli ping` |
| PostgreSQL | 5432 | 5432 | `pg_isready` |

## 4. 部署关系

```
docker compose up -d            # 默认栈：10 服务（不含 moneyprinter）
docker compose --profile media up -d   # 启用视频生成（需自备 MoneyPrinterTurbo 目录）
docker compose -f docker-compose.caddy.yml up   # Caddy 反代（生产）
docker compose -f docker-compose.override.yml up # 监控（Prometheus :9090 / Grafana :3005）
```

**服务依赖链**（compose `depends_on`）：
- `db` ← nebula / alphaid / ghost-ds
- `redis` ← alphaid / gateway / orchestrator / ghost-ds / moneyprinter
- `gateway` ← netagent / orchestrator（gateway 依赖 alphaid、nebula、flow、redis 健康）
- `tool-a` / `tool-b` ← orchestrator

## 5. 变更记录

| 日期 | 变更 |
|:-----|:-----|
| 2026-08-05 | 初版创建；moneyprinter 改为可选 profile（仓库不含该目录） |

---

*改端口/新增服务 → 同步本文件 + GHOST.md §7 + README 服务清单。*
