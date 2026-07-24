# Ghost 平台 — 顶级架构设计文档

> 本文档完全自包含，不依赖任何外部引用。所有结论基于对项目每个文件的实际阅读。

---

## 一、项目现状真实拓扑

### 1.1 三条对话路径（核心问题）

```
                    Ghost.html
                    │
                    ▼ POST /chat
            ┌───────────────────┐
            │ TwinBrain.receive │ ← 路径A: 有AgentLoop, 14工具, 有记忆
            │ (twin_brain.py)  │
            └────────┬──────────┘
                     │
                     ▼
              AgentLoop.run()
              (agent.py:709)


                    飞书
                    │
         ┌──────────┴──────────┐
         ▼                     ▼
   bot.py (WebSocket)    callback_server.py (HTTP)
         │                     │
         ▼                     ▼
  message_handler()       mindflow.engine (旧引擎)
  (main.py:271)           IntentClassifier (旧)
         │                     │
         ▼                     ▼
  _llm_decide_and_act()   PermissionGate → engine.execute()
  (main.py:301)           (无记忆, 无AgentLoop)
         │
         ▼
  3个工具: search_place, navigate_to, save_memory
  (无记忆查询, 无社交, 无身份)
```

### 1.2 各模块真实状态

| 模块 | 文件数 | 实际功能 | 核心问题 |
|------|--------|----------|----------|
| alphaid/core/ | 8 | AgentLoop(14工具), TwinBrain, MemoryStore, 身份, 风险, 信誉 | 结构好, 但未被飞书使用 |
| alphaid/feishu_bot/ | 2 | bot.py(WebSocket), callback_server.py(HTTP) | 两条路径, callback用旧引擎 |
| alphaid/alpha_id/ | ~15 | web.py(13 API), agent_network(A2A假), poe, 双链记忆 | A2A是本地模拟 |
| alphaid/projects/ | ~5 | main.py(入口), 用户画像, 语音控制, 旅行 | main.py用旧逻辑 |
| nebula/ | 75+ | 工作流引擎, LLM网关, 多平台适配 | CI路径错误, 引用已删文件 |
| DS/ | 28 | Next.js仪表盘, Prisma, Shoplazza连接 | 端口3004 vs Caddyfile 3000 |
| core/ | 21 | dispatcher(关键词匹配), 12角色JSON, 安全护栏 | 调度层太薄 |
| flow/ | ~30 | Next.js+Fastify, Ghost Key, 6 AI Provider, 双链记忆 | 内存存储, 无持久化 |
| Ghost.html | 1(4100行) | 三视图单体应用 | 两个工作台重叠, Web 4.0命名 |

---

## 二、五层架构模型

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Layer 5: 生态层 (Ecosystem)                                            │
│  第三方插件市场 │ Agent交易所 │ 社区治理 │ 开放API                       │
├─────────────────────────────────────────────────────────────────────────┤
│  Layer 4: 经济层 (Economy)                                              │
│  Ghost Key 2.0 │ 贡献证明(PoE) │ 服务计价 │ 激励机制                     │
├─────────────────────────────────────────────────────────────────────────┤
│  Layer 3: 平台层 (Platform)                                             │
│  多租户引擎 │ 插件系统 │ 事件总线 │ 可观测性 │ 安全隔离                   │
├─────────────────────────────────────────────────────────────────────────┤
│  Layer 2: 智能体层 (Agent Intelligence)                                 │
│  MasterAgent │ DomainAgents │ Loop引擎 │ 记忆系统 │ A2A通信               │
├─────────────────────────────────────────────────────────────────────────┤
│  Layer 1: 基础设施层 (Infrastructure)                                   │
│  LLM网关 │ 数据库 │ 消息队列 │ 加密 │ 日志 │ 监控                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Layer 1: 基础设施层

```
LLM Gateway (统一LLM入口)
├── DeepSeek / OpenAI / Anthropic / 本地模型
├── 熔断: 一个挂了自动切另一个
├── 限流: Token Bucket 防止配额耗尽
└── 缓存: 相同问题不重复调

Database Layer
├── PostgreSQL: 用户数据、交易记录
├── Redis: 会话、缓存、速率限制
├── VectorDB (pgvector/Milvus): 记忆向量搜索
└── 文件存储: 图片、附件

Message Bus (事件总线)
├── 模块间通信全部走事件
├── 事件类型: UserMessage, AgentAction, ToolCall, MemoryWrite...
├── 订阅模式: 模块只关心自己需要的事件
└── 持久化: 事件可回放、可审计

Security Vault
├── 密钥管理 (替代硬编码)
├── 端到端加密
└── 审计日志
```

### Layer 2: 智能体层

```
Agent Runtime
├── MasterAgent (单例/用户)
│   ├── IntentClassifier (LLM意图识别, 非关键词)
│   ├── TaskDecomposer (任务分解)
│   ├── ToolDispatcher (工具调度)
│   └── ResponseAggregator (结果汇总)
│
├── DomainAgents (按领域)
│   ├── MemoryAgent ← 记忆读写、整理、遗忘
│   ├── SocialAgent ← 社交互动、好友、A2A
│   ├── OpsAgent ← 项目运营、数据同步
│   ├── CreateAgent ← 内容创作、文案
│   └── [可扩展] ← 未来新领域
│
├── Loop引擎 (分层循环)
│   ├── MasterLoop: 每次消息触发
│   ├── MemoryLoop: 每5分钟
│   ├── OpsLoop: 每30分钟
│   └── SocialLoop: 事件驱动
│
└── Memory System
    ├── 短期: 当前对话 (Redis)
    ├── 中期: 近期记忆 (PostgreSQL)
    ├── 长期: 核心身份 (VectorDB)
    └── 双链: 公开链 + 私有链 (AES-256-GCM)
```

### Layer 3: 平台层

```
Multi-Tenant Engine
├── 每个用户 = 独立的Agent实例
├── 资源配额: LLM调用次数、存储、工具
├── 隔离: 用户A的数据对用户B不可见
└── 共享: 公共工具、公共知识库

Plugin System
├── Plugin SDK: 第三方开发标准
├── Plugin Registry: 插件注册/发现
├── Plugin Sandbox: 沙箱隔离运行
└── Plugin Market: 插件市场 (未来)

Channel Adapter (渠道抽象)
├── FeishuAdapter
├── WebAdapter (Ghost.html)
├── WeChatAdapter (未来)
├── TelegramAdapter (未来)
└── [任何新渠道] → 只需实现Adapter接口

Observability
├── Agent Trace: 每次决策的完整链路
├── Metrics: 响应时间、工具调用次数、成功率
├── Debug Console: 实时查看Agent内部状态
└── Alert: 异常自动告警
```

### Layer 4: 经济层

```
Ghost Key 2.0
├── 身份密钥: 证明"你是你"
├── 服务密钥: 访问特定功能
├── 邀请密钥: 邀请新用户获得奖励
└── 治理密钥: 社区投票权

Proof of Execution (PoE) 扩展
├── 每次Agent执行都生成证明
├── 证明上链 (可选)
└── 贡献度量: 你帮别人做了多少事

Service Pricing
├── Agent间服务计价
├── 按调用次数/按效果/按时长
└── 自动结算
```

### Layer 5: 生态层

```
Agent Exchange
├── 发布你的Agent能力
├── 发现他人的Agent服务
├── 自动匹配需求↔供给
└── 信任评分 (基于PoE)

Community Governance
├── 提案系统
├── 投票机制 (基于治理密钥)
├── 争议仲裁
└── 协议升级

Open API
├── RESTful API
├── WebSocket API
├── SDK (Python/JS/Go)
└── Webhook集成
```

---

## 三、完整问题→解决方案映射

### P0 问题（功能性 — 立即修复）

| # | 问题 | 根因 | 解决方案 | 层 |
|---|------|------|----------|-----|
| P0-1 | 飞书不像智能体 | `_llm_decide_and_act`无记忆查询, 只有3个工具 | message_handler → TwinBrain.receive → AgentLoop | L2 |
| P0-2 | 两条飞书路径 | bot.py + callback_server.py并存 | 删除callback_server.py, 统一走bot.py | L2 |
| P0-3 | /chat和飞书行为不一致 | 入口不同 | 统一入口: MasterAgent.handle() | L2 |
| P0-4 | A2A是假的 | call_skill()是本地函数, peer发现扫文件系统 | 实现HTTP/WebSocket A2A协议 | L2 |
| P0-5 | 旧引擎残留 | callback_server.py用mindflow.engine | 整个文件删除 | L2 |

### P1 问题（结构性 — 本周修复）

| # | 问题 | 根因 | 解决方案 | 层 |
|---|------|------|----------|-----|
| P1-1 | core/调度层太薄 | 只有关键词匹配 | 新建MasterOrchestrator (LLM意图分类) | L2 |
| P1-2 | flow/无持久化 | 内存存储 | 加Prisma + PostgreSQL | L1 |
| P1-3 | CI路径错误 | mindflow-map→nebula未更新 | 修正ci.yml | L1 |
| P1-4 | DS端口不匹配 | 3004 vs 3000 | 统一为3004 | L1 |
| P1-5 | Ghost.html两个工作台 | workbenchView + mindflowView重叠 | 合并为单一视图 | L2 |
| P1-6 | Web 4.0命名 | 暴露技术术语 | 重命名为Mindflow | L2 |
| P1-7 | 看板像控制台 | 缺乏社群感 | 加动态流+社群面板 | L2 |

### P2 问题（需要修复 — 两周内）

| # | 问题 | 根因 | 解决方案 | 层 |
|---|------|------|----------|-----|
| P2-1 | 硬编码飞书凭证 | bot.py L22-23 | 移入环境变量 + Vault | L1 |
| P2-2 | FOUNDER身份硬编码 | user_identity.py | 移入环境变量 | L1 |
| P2-3 | 无Agent监控 | 没有可观测性 | 加Trace + Metrics + Debug Console | L3 |
| P2-4 | 无插件系统 | 工具硬编码 | 设计Plugin SDK + Registry | L3 |
| P2-5 | 无事件总线 | 模块间直接调用 | 引入Message Bus | L1 |
| P2-6 | 无多租户 | 单用户假设 | 设计Tenant隔离机制 | L3 |
| P2-7 | 无测试 | 没有Agent测试框架 | 建Behavior Test Suite | L3 |
| P2-8 | 向量搜索自研 | TF-IDF不如专用VectorDB | 迁移到pgvector/Milvus | L1 |
| P2-9 | 无速率限制 | LLM调用无限制 | 加Token Bucket限流 | L1 |
| P2-10 | 无熔断 | LLM挂了整个系统挂 | 加Circuit Breaker | L1 |

### 未来问题（从架构视角发现）

| # | 问题 | 影响 | 解决方案 | 层 |
|---|------|------|----------|-----|
| F-1 | 无经济模型 | 生态没有驱动力 | Ghost Key 2.0 + PoE扩展 | L4 |
| F-2 | 无第三方接入 | 无法扩展 | Plugin SDK + Open API | L5 |
| F-3 | 无社区治理 | 决策集中 | 提案+投票机制 | L5 |
| F-4 | 无数据可移植 | 用户锁定 | 标准导出格式 (JSON-LD) | L3 |
| F-5 | 无跨平台抽象 | 每个渠道重复代码 | Channel Adapter模式 | L3 |

---

## 四、演进路线图

### Phase 0: 地基 (现在 - 2周)

目标: 飞书机器人"像智能体"了

- [ ] 统一对话路径 (P0-1,2,3,5)
- [ ] 安全加固 (P2-1,2)
- [ ] 修复CI/端口 (P1-3,4)
- [ ] 重写调度层 (P1-1)

### Phase 1: 核心 (2周 - 2个月)

目标: 平台可用，多人能接入

- [ ] 事件总线 (P2-5)
- [ ] 多租户引擎 (P2-6)
- [ ] 持久化 (P1-2, P2-8)
- [ ] A2A真实化 (P0-4)
- [ ] Ghost.html重构 (P1-5,6,7)

### Phase 2: 平台 (2个月 - 4个月)

目标: 稳定、可监控、可扩展

- [ ] 可观测性 (P2-3)
- [ ] 插件系统 (P2-4)
- [ ] 速率限制+熔断 (P2-9,10)
- [ ] 测试框架 (P2-7)

### Phase 3: 经济 (4个月 - 6个月)

目标: Agent间可以交易

- [ ] Ghost Key 2.0
- [ ] PoE扩展
- [ ] 服务计价

### Phase 4: 生态 (6个月 - 12个月)

目标: 第三方开发者入驻

- [ ] Agent交易所
- [ ] 社区治理
- [ ] Open API + SDK

---

## 五、关键架构决策

### 决策1: 事件驱动 > 直接调用

```
# 现在: 紧耦合
agent.run() → memory.write() → social.notify() → log.record()

# 未来: 事件驱动
agent.run() → emit("agent.action.completed")
              ├── memory.subscribe → write()
              ├── social.subscribe → notify()
              ├── log.subscribe → record()
              └── [未来模块] subscribe → do_something()
```

好处: 加新功能不需要改旧代码，只需要订阅事件。

### 决策2: Channel Adapter > 渠道硬编码

```
ChannelAdapter (抽象层)
├── FeishuAdapter
├── WebAdapter (Ghost.html)
├── WeChatAdapter (未来)
├── TelegramAdapter (未来)
└── [任何新渠道] → 只需实现Adapter接口
```

### 决策3: 多租户从第一天设计

```
所有数据表:
  id | tenant_id | ...fields | created_at | updated_at

所有API:
  middleware: 从token提取tenant_id
  query: WHERE tenant_id = ?
```

### 决策4: LLM网关抽象

```
LLMGateway
├── 当前: DeepSeek (主力) + OpenAI (备选)
├── 未来: 本地模型 (隐私场景)
├── 未来: 多模型路由 (简单问题用便宜模型，复杂问题用强模型)
└── 未来: 模型市场 (用户自选)
```

---

## 六、文件级变更清单

### Phase 0 变更

| 文件 | 操作 | 说明 |
|------|------|------|
| `alphaid/projects/main.py` | 重写 | message_handler → TwinBrain.receive |
| `alphaid/projects/src/feishu_bot/callback_server.py` | 删除 | 旧引擎, 整个文件 |
| `alphaid/projects/src/feishu_bot/bot.py` | 修改 | 凭证移入环境变量 |
| `alphaid/projects/src/core/user_identity.py` | 修改 | FOUNDER移入环境变量 |
| `.github/workflows/ci.yml` | 修改 | mindflow-map → nebula |
| `Caddyfile` | 修改 | DS端口 3000 → 3004 |
| `core/orchestrator.py` | 新建 | MasterOrchestrator |
| `.env.example` | 修改 | 新增凭证变量 |

### Phase 1 变更

| 文件 | 操作 | 说明 |
|------|------|------|
| `core/event_bus.py` | 新建 | 事件总线 |
| `core/tenant.py` | 新建 | 多租户引擎 |
| `flow/apps/web/prisma/schema.prisma` | 新增 | User, Memory, GhostKey模型 |
| `alphaid/projects/src/alpha_id/agent_network.py` | 重写 | 真实A2A通信 |
| `alphaid/projects/src/alpha_id/web.py` | 新增 | /a2a/register, /a2a/discover, /a2a/call |
| `Ghost.html` | 重构 | 合并工作台, 加社群面板 |

---

## 七、分层Loop设计

| Loop | 职责 | 触发条件 | 频率 |
|------|------|----------|------|
| MasterLoop | 全局任务调度、意图路由 | 每次用户消息 | 实时 |
| MemoryLoop | 记忆整理、遗忘、关联 | 定时/触发 | 每5分钟 |
| OpsLoop | 项目运营、数据同步 | 定时 | 每30分钟 |
| SocialLoop | 社交互动、A2A通信 | 事件驱动 | 实时 |

---

## 八、A2A通信协议

```
Agent A → POST /a2a/call
{
  "caller": "Alpha-1",
  "target": "Alpha-3",
  "skill": "generate_content",
  "params": {"topic": "AI Agent"},
  "proof": "<Ed25519签名>"
}

Agent B → Response
{
  "result": "...",
  "proof": "<执行证明>",
  "timestamp": 1721800000
}
```

---

*文档版本: 1.0*
*创建日期: 2026-07-24*
*基于: 对项目全部文件的完整审计*
