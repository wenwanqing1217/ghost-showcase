# Phase 1 实施路线图 — 全维度换血

> 版本：2026-08-04 | 状态：进行中  
> 原则：死代码是用来盘活的，优化才是王道。不动目录结构，只连通、只合并、只优化。

---

## 问题根因

三套 Orchestrator 不是"命名冲突"——是**同一套调度系统被三个人在不同时间、不同位置分别写出来的**，各自管一块，互不通信。两个 `MasterOrchestrator` 在同一个 Alpha-ID 进程里各有一个 TwinBrain 实例，各自管理记忆和状态，互不共享。

---

## P0 — 必须做（不动目录结构）

### 1. 合并两个 Python MasterOrchestrator → OrchestratorEngine

**问题**：
- `alpha_id/orchestrator.py` 管理 Feed/Capture/Obsidian/Feishu/NURO/Evolution 6个后台线程，自己创建 TwinBrain
- `core/orchestrator.py` 管理 TwinBrain 生命周期 + 渠道适配器 + Memory/Ops/Social 循环，惰性创建 TwinBrain
- 两个类同名 `MasterOrchestrator`，在同一个 Alpha-ID 进程里各有一个 TwinBrain 实例，互不通信

**方案**：
- 新建 `alphaid/projects/src/orchestrator/engine.py`，合并两个类的全部能力
- TwinBrain 只有一个实例（保留 `core/orchestrator.py` 的惰性初始化方式）
- 6个数据循环作为模块注册（`register_loop()`）
- 渠道适配器统一通过 `register_channel()`（复用 `core/orchestrator.py` 的 ChannelAdapter 基类）
- 所有旧 import 路径保留，内部转发到新引擎（兼容层不-breaking）

**文件变更**：
- 新增：`orchestrator/engine.py`（~400行，合并两个 MasterOrchestrator）
- 修改：`orchestrator/__init__.py`（导出新引擎）
- 修改：`alpha_id/orchestrator.py`（保留类定义，内部委托到 OrchestratorEngine）
- 修改：`core/orchestrator.py`（保留类定义，内部委托到 OrchestratorEngine）
- 修改：所有 `from alpha_id.orchestrator import MasterOrchestrator` 的引用文件（只加一行 import 兼容）

### 2. EventBus blinker → Redis Streams

**问题**：
- Python blinker 信号只在本进程内有效
- TS Redis Streams 跨服务可用，但 `startConsuming()` 从未被调用，完全休眠
- Python 和 TS 服务的事件完全不互通

**方案**：
- `core/event_bus.py` 保留接口（`on()`, `emit()`, `get_event_bus()`），底层从 blinker 改为 Redis Streams
- 所有 `self._event_bus.emit(...)` 调用不需要改
- 新增 `start_consuming()` 方法，在 Alpha-ID 启动时调用
- 飞书消息 → Redis Streams → Alpha-ID 消费者处理 → 更新 TwinBrain 记忆

**文件变更**：
- 修改：`core/event_bus.py`（重写底层为 Redis Streams，接口不变）
- 修改：`alpha_id/orchestrator.py`（启动时调用 `event_bus.start_consuming()`）
- 新增：`core/redis_client.py`（Redis 连接管理，单例）

### 3. 修复 /v1/chat 断裂链路

**问题**：
- `nebula/src/mindflow_map/api/feishu_webhook.py:103` 调用 `Gateway /v1/chat` → 端点不存在
- `ghost-main/gateway/app.py:547` demo UI 调用 `Gateway /v1/chat` → 端点不存在
- 正确路径是 `/v1/human/chat`

**方案**：
- `ghost-main/gateway/app.py` 加 `/v1/chat` 别名路由 → 转发到 `/v1/human/chat`
- `feishu_webhook.py:103` 也改为 `/v1/human/chat`（双重保障）
- 前端 demo UI 同上

**文件变更**：
- 修改：`ghost-main/gateway/app.py`（加 1 条 `/v1/chat` POST 别名路由）
- 修改：`nebula/src/mindflow_map/api/feishu_webhook.py`（改端点路径）

### 4. 激活 Redis Streams 消费

**问题**：
- `DS/src/lib/eventbus-init.ts` 注册了 handler 但从未调用 `startConsuming()`
- 所有 DS 事件（订单/履约/库存）发布后无人消费

**方案**：
- `eventbus-init.ts` 的 `initialize()` 函数末尾加 `await eventBus.startConsuming()`

**文件变更**：
- 修改：`DS/src/lib/eventbus-init.ts`（加 1 行 `startConsuming()` 调用）

---

## P1 — 做完 P0 后

### 5. 盘活 wechat.py

- Gateway 加 `/webhook/wechat` 路由
- 接入 `wechat.py` 渠道适配器到 OrchestratorEngine
- 让微信消息走统一渠道入口

### 6. 合并 eventbus-server.ts → eventbus-init.ts

- `eventbus-server.ts` 功能与 `eventbus-init.ts` 重复，且未被任何文件 import
- 合并到 `eventbus-init.ts`，删除 `eventbus-server.ts`

---

## P2 — 后续优化

### 7. ToolA/ToolB stub → 真实接入

- `orchestrator/main.py` 的 `_execute_task()` 目前返回 `not_implemented`
- 接入真实工具服务后，通过 HTTP 调用

### 8. 术语注释标准化

在关键文件中加 `# TERM:` 注释：

```python
# TERM: OrchestratorEngine — 统一后台循环管理（合并自 alpha_id/orchestrator.py + core/orchestrator.py）
# TERM: EventBus — Redis Streams 跨服务事件总线（替代旧 blinker 实现）
# TERM: AgentGraph — A2A 网络拓扑（运行时计算，非持久化）
# TERM: MemoryGraph — 记忆知识图谱（按标签关联）
```

### 9. 创建 AGENTS.md

项目级 AI agent 指令文件，定义术语标准、Orchestrator 命名规则、EventBus 使用规则等。

---

## 不做什么

- ❌ 不动目录结构（Phase 3 才考虑）
- ❌ 不删功能代码
- ❌ 不新建文档（只建 AGENTS.md 这一个）
- ❌ 不改 Docker Compose 结构

---

## 执行顺序

```
第 1 步：修复 /v1/chat（最小改动，快速验证）
第 2 步：激活 Redis Streams（1行代码）
第 3 步：合并 EventBus（接口不变，影响面可控）
第 4 步：合并 Orchestrator（核心改动）
第 5 步：盘活死代码
第 6 步：Git commit（每个阶段一个 commit）
```
