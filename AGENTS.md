<!-- ════════════════════════════════════════════════════════════════════ -->
<!-- STATUS: ACTIVE -->
<!-- 本文件是项目级 AI 指令，TERM 规则、命名规范、死代码处理等约定必须遵守。 -->
<!-- 与 GHOST.md 互补：GHOST.md 管架构，AGENTS.md 管行为。 -->
<!-- ════════════════════════════════════════════════════════════════════ -->

# Ghost Platform — AGENTS.md

> 项目级 AI Agent 指令文件。所有参与 Ghost Platform 开发的 AI Agent 必须遵守以下规范。

---

## 1. 术语标准（TERM 规则）

**在代码中遇到以下概念时，必须使用统一术语，不得自行创造。**

| 标准术语 | 是什么 | 禁止使用的别名 | 所在文件参考 |
|:---------|:-------|:---------------|:-------------|
| `OrchestratorEngine` | 统一后台循环管理（合并自 alpha_id/orchestrator.py + core/orchestrator.py） | MasterOrchestrator | orchestrator/engine.py |
| `EventBus` | Redis Streams 跨服务事件总线（替代旧 blinker 实现） | blinker, event bus | core/event_bus.py |
| `AgentGraph` | A2A 网络拓扑（运行时计算，非持久化） | agent_graph, topology | a2a.py:447 |
| `MemoryGraph` | 记忆知识图谱（按标签关联） | memory graph | memory_graph.py |
| `TwinBrain` | 智能体大脑（唯一实例） | brain, 大脑 | core/twin_brain.py |
| `ChannelAdapter` | 渠道适配器基类（飞书/Web/微信/Telegram） | adapter, 适配器 | core/orchestrator.py |
| `GhostDS` | Next.js 电商看板（端口 3000） | DS, dashboard | DS/ |
| `Gateway` | 统一 API 网关（端口 18080） | 网关 | ghost-main/gateway/ |

**代码注释规范**：在关键类/函数定义处加 `# TERM:` 注释：
```python
# TERM: OrchestratorEngine — 统一后台循环管理
class OrchestratorEngine:
    ...
```

---

## 2. 命名规则

### 2.1 Orchestrator 相关

- **禁止**在代码中创建新的 `MasterOrchestrator` 类
- **禁止**在代码中创建新的 `AgentOrchestrator` 类（orchestrator/main.py 的类名保留但功能已迁移）
- 新代码必须使用 `OrchestratorEngine` 或 `get_orchestrator()`
- 旧 `MasterOrchestrator` 类保留为兼容层，内部委托到 `OrchestratorEngine`

### 2.2 EventBus 相关

- **必须**使用 `EventBus` 接口（`on()`, `emit()`, `start_consuming()`）
- **禁止**直接使用 blinker 的 `Namespace` 或 `signal()`
- **禁止**在 Python 代码中直接调用 Redis Streams 命令（走 EventBus 封装）
- 事件类型必须使用 `EventType` 常量，不得硬编码字符串

### 2.3 路径相关

- `alphaid/projects/src/` 是 Python 源代码根目录
- `ghost-main/gateway/` 是 Gateway 源代码根目录
- `DS/src/` 是 Ghost DS 源代码根目录
- `nebula/src/` 是 Nebula 源代码根目录
- `orchestrator/` 是 Orchestrator 服务根目录
- **禁止**在上述目录外创建相同功能的代码

---

## 3. 文档更新规则

修改代码后，必须同步更新以下文档：

| 改动类型 | 必须更新的文档 |
|:---------|:--------------|
| 新增/修改 API 端点 | ARCHITECTURE.md（路由表） |
| 新增/修改数据模型 | ARCHITECTURE.md（数据流） |
| 新增/修改端口 | SYSTEM_MAP.md（端口表） |
| 新增/修改术语 | PROJECT_MAP.md（术语表） |
| 新增/修改决策 | DECISIONS.md |
| 新增/修改进度 | PROJECT_STATUS_REPORT.md |
| 新增/修改 Bug 修复 | WORK_LOG.md |

**核心原则**：改代码必须改文档，改架构必须改 ARCHITECTURE.md + SYSTEM_MAP.md。

---

## 4. 提交信息规范

使用 Conventional Commits 格式：

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Type 枚举**：
- `feat` — 新功能
- `fix` — Bug 修复
- `refactor` — 代码重构（不改变功能）
- `perf` — 性能优化
- `docs` — 文档变更
- `chore` — 构建/工具变更
- `test` — 测试相关

**Scope 枚举**：
- `orchestrator` — 调度器
- `eventbus` — 事件总线
- `gateway` — 网关
- `alphaid` — 身份层
- `nebula` — 工作流引擎
- `ds` — 电商看板
- `feishu` — 飞书
- `infra` — 基础设施（Docker/Makefile/CI）

**示例**：
```
feat(eventbus): rewrite EventBus from blinker to Redis Streams
fix(gateway): add /v1/chat alias for feishu webhook
refactor(orchestrator): merge two MasterOrchestrator into OrchestratorEngine
docs: update ARCHITECTURE.md with 7-layer architecture
```

---

## 5. 死代码处理规则

**核心原则：死代码是用来盘活的，不是用来删的。**

- 发现死代码（未被 import、未被调用）→ **先尝试接入活跃链路，而不是删除**
- 接入方式：通过 EventBus、渠道适配器、API 路由等方式连通
- 仅在以下情况才允许删除：确认无任何接入价值，且删除后不影响其他模块
- 删除前必须在 DECISIONS.md 中记录删除理由

---

## 6. 禁止事项

- ❌ 不在 `alphaid/projects/src/` 之外创建 Python 业务逻辑（除非是独立服务如 orchestrator）
- ❌ 不创建第三个 EventBus 实现
- ❌ 不创建第三个 Orchestrator 类
- ❌ 不改动 Docker Compose 服务依赖关系（除非在 P0-P2 计划内）
- ❌ 不在代码中硬编码端口号（使用环境变量）
- ❌ 不在代码中硬编码 API 密钥/凭证（使用环境变量）
- ❌ 不删除未读懂的代码（先读，再决定盘活还是删除）

---

## 7. 项目文档权威层级

| 层级 | 文档 | 用途 |
|:-----|:-----|:-----|
| L1 宪法 | GHOST.md | 项目定位、三层堆栈、七层架构、愿景 |
| L2 架构 | ARCHITECTURE.md | 服务设计、数据流、端口分配 |
| L3 地图 | SYSTEM_MAP.md | 服务拓扑、调用链、部署图 |
| L4 术语 | PROJECT_MAP.md | 术语表、冲突解决、端口表 |
| L5 计划 | PHASE1_PLAN.md | 实施路线图、优先级 |
| L6 状态 | PROJECT_STATUS_REPORT.md | 服务健康、功能评分 |
| L7 决策 | DECISIONS.md | 技术决策记录 |
| L8 日志 | WORK_LOG.md | 每日工作记录 |

**修改代码时，必须查阅 L1-L4 确保理解当前架构。**

---

## 8. 七层架构速查

```
L1 感知层 — 输入来源（飞书/Web/微信/Telegram/NURO）
L2 身份层 — DID + 身份验证（Alpha-ID :8000）
L3 工作流层 — 流程编排（Nebula :2002）
L4 调度层 — 任务调度（Orchestrator :19090）
L5 网关层 — API 路由（Gateway :18080）
L6 业务层 — 电商运营（Ghost DS :3000）
L7 知识层 — 记忆 + 知识图谱（MemoryGraph / Obsidian）
```

---

*本文件由 Phase 1 实施创建，所有 AI Agent 参与 Ghost Platform 开发前必须阅读。*
