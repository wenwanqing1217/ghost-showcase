# Alpha-ID 项目独立审计报告

> 审计标准：与 Ghost 项目相同的问题清单 + 差距分析
> 审计范围：`alphaid/projects/` 全部源码 + 测试 + 配置

---

## 一、代码健康度

### 核心层 `src/core/` — 25 文件，约 22,000 行

| 状态 | 文件数 | 行数 | 说明 |
|:-----|:------:|:----:|:------|
| 🟢 被引用、可用 | 7 | ~9,500 | storage, storage_sqlite, dual_chain, user_identity, alpha_social, memory_store, risk_engine |
| 🟡 写完了但 0 处引用 | 18 | ~6,530 | agent, agent_react, twin_brain, a2a, coala_memory, orchestrator, event_bus, recovery, observability, reputation, memory_poisoning_defense, benchmark_adapter, tenant, storage_postgres, storage_factory, interfaces 等 |

**结论：约 30% 的 core 代码是死代码。写完了但从未接入。**

### API 层 `src/api/` — 32 条路由

| 路由 | 条数 | 状态 |
|:-----|:----:|:------|
| identity | 11 | 🟢 完整可用 |
| dual_chain | 7 | 🟢 完整可用 |
| registration | 6 | 🟢 可用（SMS demo 模式） |
| social | 6 | 🟡 需登录后测试 |
| risk | 2 | 🟡 需风控数据 |

### 重复入口

- `src/main.py` — 实际运行的 API 入口 🟢
- `src/entrypoints/api.py` — 从未启动过的重复入口 🔴
- `src/entrypoints/aid_mcp_server.py` — MCP Server，从未启动 🔴
- `src/alpha_id/web.py` — 独立 FastAPI 应用，从未启动 🔴

### 采集器 `src/alpha_id/collectors/` — 9 个文件

| 文件 | 行数 | 问题 |
|:-----|:----:|:------|
| base.py | 94 | 🟡 V1 基础类 |
| base_v2.py | 74 | 🟡 V2 基础类（两版并存，混乱） |
| browser.py | 327 | 🟡 模块级函数（非类），不一致 |
| chatgpt.py | 174 | 🟡 可用但未集成 |
| claude.py | 132 | 🟡 可用但未集成 |
| cursor.py | 205 | 🟡 可用但未集成 |
| trae.py | 237 | 🟡 可用但未集成 |
| git.py | 127 | 🟡 可用但未集成 |
| local_signals.py | 191 | 🟡 可用但未集成 |

**所有采集器都写完了，但没有任何一个被实际集成到注册或工作流中。**

### mindflow 工作流 — 7 文件 + 3 agent

| 文件 | 行数 | 问题 |
|:-----|:----:|:------|
| engine.py | 298 | 🟡 工作流引擎，路径未通 |
| intent.py | 135 | 🟡 意图解析，路径未通 |
| onboarding.py | 286 | 🟡 新用户引导，路径未通 |
| voice_control.py | 283 | 🟡 语音控制，路径未通 |
| route_optimizer.py | 294 | 🟡 路线优化，路径未通 |
| user_profile.py | 192 | 🟡 用户画像，路径未通 |
| schedule_parser.py | 137 | 🟡 日程解析，路径未通 |

**10 个文件全写了，GHOST.md 自己标注为「路径未通」。**

---

## 二、测试健康度

| 指标 | 数据 |
|:-----|:------|
| 测试文件总数 | 37 |
| 收集错误（无 --noconftest） | 37 |
| 收集错误（有 --noconftest） | 3（已修） |
| 注册测试通过率 | 8/8 ✅ |
| 健康检查测试 | 5/5 ✅ |

**核心问题：测试只有加 `--noconftest` 才能跑。CI 不会加这个参数。**

---

## 三、安全风险

| 风险 | 位置 | 严重度 |
|:-----|:------|:-------|
| BAIDU_MAP_AUTH_TOKEN 硬编码 | `mindflow/agents/travel.py:15` | 🔴 密钥在 git 里 |
| .env 文件含真实密钥（已提交） | `.env` | 🔴 密钥在 git 里 |
| JWT 密钥有 fallback 默认值 | `auth/jwt.py` | 🟡 |
| CORS dev 模式通配符 | `alpha_id/web.py` | 🟡 |

---

## 四、差距分析（文档 vs 代码）

| 文档描述的功能 | 代码状态 | 差距 |
|:---------------|:---------|:------|
| 数字身份 DID | 🟢 完整 | 无差距 |
| 双链记忆 | 🟢 完整 | 无差距 |
| Agent 主循环 | 🟡 813 行但 0 引用 | 未接入口 |
| 双大脑 TwinBrain | 🟡 690 行但 0 引用 | 未接入口 |
| A2A 通信 | 🟡 410 行但 0 引用 | 未接入 |
| CoALA 记忆架构 | 🟡 507 行但 0 引用 | 未接入 |
| 故障恢复 | 🟡 534 行但 0 引用 | 未接入 |
| 可观测性 | 🟡 553 行但 0 引用 | 未接入 |
| 多租户 | 🟡 281 行但 0 引用 | 未接入 |
| 个人数据采集 | 🟡 9 采集器全写了 | 未集成到产品流程 |

### 五、一句话总结

> **Alpha-ID 的核心能力（DID + 双链记忆 + Gateway）已写完且可用。但 70% 的代码（AgentLoop + TwinBrain + A2A + 采集器 + mindflow）写完了但没接通。项目现在是有引擎没方向盘的状态。**
