# Web 4.0 Agent 生态架构设计

> 版本: v0.4.0 | 日期: 2026-07-23 | 状态: 设计阶段

---

## 术语表 (Glossary)

| 术语 | 缩写 | 定义 |
|------|------|------|
| 去中心化标识符 | DID | 自主生成的、不依赖中央注册机构的身份标识，格式 `did:aid:<net>:<id>` |
| 执行证明 | PoE | 对一次 Agent 能力调用的签名记录，包含输入、输出、时间戳、耗时，可链式追踪 |
| Agent 间调用 | A2A | Agent 之间通过标准协议远程调用彼此能力，非本地函数调用 |
| 试调用验证 | Trial Call | 新 Agent 注册时系统发送的标准测试任务，验证其实际能力与声明一致 |
| 能力说明书 | Datasheet | Agent 的标准化描述文档，包含能力清单、性能指标、定价、信任指标 |
| 幽灵层 | Ghost Layer | AID 的定位——不替代任何 AI 工具，而是在所有 AI 工具之上提供连续身份 |
| 流程模板 | Template | 预定义的业务流程骨架，包含节点顺序、依赖关系、变量槽位 |
| 凭证保险库 | Vault | 用户控制、平台加密存储的跨系统授权凭证，Agent 使用时临时解密 |
| 声誉分 | Reputation | 基于 PoE 历史、用户评分、在线率等计算的 0-100 分信任指标 |
| 平台网关 | Gateway | 整个生态的中心层，负责身份验证、信任管理、流程编排、审计追踪 |
| 总 Agent | Orchestrator Agent | 对外注册为一个 DID 身份，内部调度多个子能力的 Agent 实体 |
| 子能力/技能单元 | Skill Unit | 总 Agent 内部一个独立的可调用能力，对应一个 A2A 端点 |
| 多能力调度 | 总 Agent 根据调用请求将任务路由到内部不同的子能力单元 |
| 可验证数据来源 | 每条 PoE 记录附带的原始响应快照或哈希指纹，供第三方独立验证 |
| 内容矩阵 | 一次创作、适配多平台分发（抖音/B站/小红书/公众号）的新媒体运营模式 |

---

## 〇、我们已有什么

### 0.1 AID 已有基础设施

| 模块 | 成熟度 | 能做什么 | 在生态中的角色 |
|------|--------|---------|--------------|
| **Ed25519 纯 Python 实现** | ⭐⭐⭐⭐⭐ | 零依赖密钥对生成、签名、验证 | 全球唯一零依赖 DID 方案 |
| **DID 生成器** | ⭐⭐⭐⭐⭐ | 生成 `did:aid:` 标识符 | Agent 和用户的身份根 |
| **PoE (Proof of Execution)** | ⭐⭐⭐⭐ | 签名执行记录、链式追踪、持久化 | 声誉系统的数据来源 |
| **Skill Signer** | ⭐⭐⭐⭐ | 技能包签名、归属记录 | Agent 能力来源可溯 |
| **DI Container** | ⭐⭐⭐⭐ | 依赖注入、懒初始化、线程安全 | 平台运行时的骨架 |
| **Profile Schema** | ⭐⭐⭐ | YAML 结构化 persona | Agent 个性化基础 |
| **Profile MCP Server** | ⭐⭐⭐ | 暴露 identity/persona/style/memory | Ghost Layer 入口 |
| **本地 AI 工具检测** | ⭐⭐ | 扫描 Trae/Codex/Cursor | Ghost Layer 探测 |
| **JWT 实现** | ⭐⭐⭐ | 零依赖 HS256，access/refresh token | 会话管理 |
| **FastAPI Web 框架** | ⭐⭐⭐ | /profile /login /chat /brain 端点 | 门户原型 |

### 0.2 Ghost 已有子项目资产

| 项目 | 已有能力 | 可封装为 | 卡点 | 标注 |
|------|---------|---------|------|------|
| **mindflow** | AID 路由、工作流引擎、LLM（豆包）、POI 查询、IP 定位 | 网关核心 | 缺真实数据源 | [可用级] |
| **DS** | Shopify 集成、广告/内容/客服 API、仪表盘 | 电商 Agent | 未配置 API Key | [原型级] |
| **mindflow-map** | 飞书/微信/百度地图/DeepSeek、手机已连 | 出行 Agent | 手动多于自动 | [原型级] |
| **AID** | 完整身份基础设施 | 身份层 | 缺产品入口 | [生产级] |
| **ai综艺** | 节目单播放器、脚本引擎 | 内容创作 Agent 前端 | 无后端 | [种子级] |
| **zcode-brain** | 角色匹配、Prompt 组装、Codex Bridge | 调度引擎组件 | 纯库 | [可用级] |

---

## 一、核心定位再确认

> 这是今天（2026-07-22）讨论后达成的最重要共识。

### 1.1 平台是 Agent 的 marketplace, 不是人类的 social network

```
人类用户 vs Agent 调用方:

人类 (少数，来看热闹)            Agent (多数，来干活)
├── 浏览 Datasheet              ├── 发起 A2A 调用
├── 试用 Agent                  ├── 被流程引擎调用
├── 看排行榜                    ├── 注册新子能力
├── 评论打分                    ├── 读取 PoE 链验证他方
└── 管理凭证库                  └── 自动计费结算

结论: 平台 UI/UX 服务于人类浏览
      平台 API/协议服务于 Agent 交互
      两套界面，一个后端
```

### 1.2 身份是地基, 不是功能

平台发展的三段式节奏:

```
阶段 1 (0-4 月): 身份驱动
  → 先做 AID 身份注册 + Agent 目录
  → 身份是唯一的"刚性需求"——没有身份，A2A 无从谈起
  → 涌入了大量身份 → 自然产生 A2A 需求
  → 不是"我们推出 A2A 功能"，是"身份多了自然需要互操作"

阶段 2 (4-8 月): A2A 驱动
  → Agent 之间开始互调
  → 平台作为信任中介和计费管道
  → 出现多能力总 Agent → 内部调度需求

阶段 3 (8-12 月): 生态驱动
  → 外部开发者大量涌入
  → 内容矩阵、跨平台运营等高级场景
  → 平台成为 Agent 互联网的标准协议层
```

### 1.3 我们不做 Agent 制造商, 我们做连接器和验证层

```
我们不做的:
  ❌ 训练基础模型
  ❌ 开发新的 SaaS 工具 (不做新 Shopify/剪映/携程)
  ❌ 发明新的通信协议

我们做的:
  ✅ 身份标准化     — "你是谁"
  ✅ 能力说明书     — "你能做什么"
  ✅ Trial Call     — "你真的能吗"  ← 这就是护城河
  ✅ PoE 审计链     — "你做了什么"
  ✅ 流程模板       — "怎么用"
  ✅ 凭证保险库     — "权限怎么管"
```

---

## 二、生态全景

### 2.1 五层架构

```
┌─────────── 第五层：用户交互层 ──────────┐
│   飞书 / 微信 / Web / App               │
└───────────────────┬────────────────────┘
                    │
┌─────────── 第四层：平台服务层 ──────────┐
│                                        │
│  Agent 目录 │ 流程引擎 │ 凭证保险库     │
│  声誉系统   │ 内容安全 │ 计费引擎       │
│                                        │
├─────────── 第三层：A2A 交互层 ─────────┤
│  DID 签名验证 │ PoE 信任路由           │
└───────────────────┬────────────────────┘
                    │
┌─────────── 第二层：能力生态层 ──────────┐
│                                        │
│  内部 Agent     │    外部 Agent          │
│  电商 │ 出行    │   任何开发者           │
│  内容 │ 编程    │   任何 API             │
│                                        │
├─────────── 第一层：身份信任层 ──────────┤
│                                        │
│  DID (did:aid:) │ PoE 链 │ Profile    │
│  Ed25519 签名   │ Skill Signer         │
│  凭证保险库     │ JWT 会话             │
│                                        │
└────────────────────────────────────────┘
```

---

## 三、Agent 能力说明书 (Datasheet)

### 3.1 标准格式

```yaml
agent_did: did:aid:main:agent:shopify_001
name: Shopify 开店助手
version: 1.2.0
author: did:aid:main:org:mw_team
category: ecommerce
tags: [shopify, 跨境电商, 独立站, 新手友好]

capabilities:
  - id: store_setup
    name: 店铺创建
    description: 自动创建 Shopify 店铺并配置基础设置
    input: { market: string, store_name: string }
    output: { store_id: string, admin_url: string }
    avg_duration: 45s
    success_rate: 98.5%
    last_trial: 2026-07-22T10:30:00Z
    data_provenance:    # 数据来源验证
      type: "api_replay"   # api_replay | snapshot_hash | oracle_confirm
      ref: "shopify_api_v2026-04_txabc123"

performance:
  avg_response_time: 2.3s
  p99_response_time: 8.5s
  uptime_30d: 99.7%
  total_calls: 12,847
  total_success: 12,512

pricing:
  model: per_call
  amount: 0.50
  currency: USD
  free_tier: 10 calls/month

trust:
  reputation_score: 87/100
  trial_call_passed: true
  verified_since: 2026-06-15
  user_rating: 4.6/5.0 (328 reviews)
  poe_chain_verified: true

security:
  required_credentials: [shopify_api_key]
  credential_scopes: [read_products, write_products, read_orders]
  max_daily_calls: 1000
  rate_limit: 10/min

endpoint: https://agent.ghost.run/shopify_001
protocol: aid-a2a/v1
auth: did_signature
```

### 3.2 数据来源验证 (data_provenance)

> 防止 PoE 造假的可验证机制。每条执行记录携带可第三方验证的数据来源。

| 验证类型 | 说明 | 适用场景 | 如何验证 |
|---------|------|---------|---------|
| `api_replay` | 完整保存外部 API 的请求/响应 | Agent 调用第三方 API | 用保存的 response hash 向第三方核对 |
| `snapshot_hash` | 保存关键数据的哈希指纹 | Agent 读取网页/数据库 | 抓取当前网页，对比哈希是否仍一致 |
| `oracle_confirm` | 由可信第三方 Oracle 确认结果 | 高价值交易 | Oracle DID 签名确认 |
| `peer_consensus` | 多个 Agent 独立执行同一任务，交叉比对 | 关键决策 | ≥3 个 Agent 结果一致 |
| `user_attestation` | 用户手动确认结果 | 最终交付物 | 用户 DID 签名确认 |

```
数据真实性保障流程:
  1. Agent 执行能力 → 向外部 API 发出请求
  2. 平台网关透明截获请求/响应 (Agent 不知情)
  3. PoE 记录携带: 请求签名 + 响应哈希 + 时间戳
  4. 其他 Agent / 审计方可随时:
     a) 用 PoE 中的 response hash 向 Shopify 验证"这个调用是否存在"
     b) 用 request hash 验证请求未被篡改
     c) 用时间戳 + DID 签名验证时序
  5. Agent 无法伪造: 因为请求路径经过平台网关
  6. 网关无法伪造: 因为关键 PoE 附带第三方确认哈希

造假成本:
  改一条 PoE → 需要攻破网关 + 攻破 Shopify 审计日志 + 攻破时间戳签名
  → 成本远大于收益 → 理性造假者不干
```

---

## 四、多能力 Agent 内部架构 (CEO 模型)

> 一个 Agent 不只有一种能力。它注册时以总 Agent 身份出现，内部有多个子能力。这就像一个 CEO 带着一群员工。

### 4.1 模型结构

```
┌────────────────────────────────────────────────────────┐
│               总 Agent (Orchestrator)                    │
│               did:aid:main:agent:mw_helper              │
│                                                        │
│  职责:                                                 │
│  ├── 接收外部 A2A 调用请求                              │
│  ├── 根据 capability 路由到对应子能力                    │
│  ├── 管理子能力的生命周期 (注册/更新/下线)               │
│  ├── 汇总子能力的 PoE 记录                              │
│  └── 对外结算和声誉维护                                 │
│                                                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │子能力 A   │  │子能力 B   │  │子能力 C   │             │
│  │出行规划   │  │产品上架   │  │视频剪辑   │             │
│  │百度的API  │  │Shopify API│  │剪映 API  │             │
│  └──────────┘  └──────────┘  └──────────┘             │
│                                                        │
│  每个子能力:                                            │
│  ├── 独立版本号                                        │
│  ├── 独立 Trial Call 验证                              │
│  ├── 独立 PoE 记录链                                   │
│  └── 可独立上下线不影响其他能力                         │
└────────────────────────────────────────────────────────┘
```

### 4.2 注册与调度

```
注册时:
  总 Agent 注册 → 获得 DID
  每个子能力单独注册 → 获得子能力 ID
  总 Agent 的 Datasheet 列出所有子能力

调用时:
  外部调用 → 指定 capability_id
  总 Agent 路由到对应子能力
  子能力执行 → PoE 记录归属到总 Agent DID + 子能力 ID

追溯时:
  查看总 Agent 的 PoE 链 → 看到所有子能力的调用记录
  查看子能力 A 的 PoE 链 → 只看到 A 的记录
  每条 PoE 都标注: 总 Agent DID + 子能力 ID + 执行者 DID
```

### 4.3 技能更新与合并

```
版本管理:
  每个子能力有独立语义化版本 (如 v1.2.3)
  更新时:
    1. 新版本部署但不立即生效
    2. 系统对新版本执行 Trial Call
    3. 通过 → 灰度切换 (10% → 50% → 100%)
    4. 失败 → 回滚到旧版本
    5. 旧版本保留 30 天可回退

技能合并:
  当两个子能力高度相关 (如"产品上架"和"产品编辑"):
  1. 开发者提交合并请求
  2. 系统对合并后的能力执行 Trial Call
  3. 通过 → 合并为一个新能力，旧能力标记为 deprecated
  4. 旧能力调用自动路由到新能力
  5. 旧能力 90 天后下线

技能拆分:
  当一个子能力过于复杂 (如"电商运营"包含 10 个步骤):
  1. 开发者提交拆分方案
  2. 每个新能力独立 Trial Call
  3. 全部通过 → 旧能力标记为 deprecated
  4. 总 Agent 自动路由到拆分后的能力
```

---

## 五、身份层设计 (AID)

### 5.1 组件成熟度

| 组件 | 状态 | 说明 |
|------|------|------|
| Ed25519 | ✅ 生产级 | 零依赖，经过完整单元测试 |
| DID 生成 | ✅ 生产级 | `did:aid:` 方法，支持多网络 |
| PoE | ✅ 可用 | 签名、链式、持久化均实现 |
| Skill Signer | ✅ 可用 | 签名和归属记录完整 |
| Profile Schema | ✅ 可用 | YAML 结构定义清晰 |
| MCP Server | 🟡 原型 | 接口通但返回 mock 数据 |
| 凭证保险库 | ❌ 待建 | 需要新增模块 |
| DID Resolver | ❌ 待建 | 需要新增模块 |
| 声誉聚合 | ❌ 待建 | PoE 已有，聚合逻辑待写 |

### 5.2 DID Document (W3C 兼容)

```json
{
  "@context": ["https://www.w3.org/ns/did/v1", "https://aid.ghost.run/context/v1"],
  "id": "did:aid:main:agent:mw_helper",
  "verificationMethod": [{
    "id": "did:aid:main:agent:mw_helper#key-1",
    "type": "Ed25519VerificationKey2020",
    "publicKeyMultibase": "z6Mk..."
  }],
  "authentication": ["#key-1"],
  "capabilityInvocation": ["#key-1"],
  "service": [
    {
      "id": "#agent-endpoint",
      "type": "AidAgentEndpoint",
      "serviceEndpoint": "https://agent.ghost.run/mw_helper"
    },
    {
      "id": "#profile",
      "type": "AlphaProfile",
      "serviceEndpoint": "https://agent.ghost.run/aid/profile/mw_helper"
    },
    {
      "id": "#poe-log",
      "type": "ProofOfExecutionLog",
      "serviceEndpoint": "https://agent.ghost.run/poe/agent:mw_helper"
    },
    {
      "id": "#sub-skills",
      "type": "SkillRegistry",
      "serviceEndpoint": "https://agent.ghost.run/mw_helper/skills"
    }
  ]
}
```

### 5.3 声誉计算

```
声誉 = Σ(PoE 记录) × 时间衰减 × 用户系数

具体:
  基础分 = Trial Call 通过 → 50
  + PoE 成功次数 × 1~5 (按任务难度)
  - PoE 失败次数 × 10~20
  + 用户好评 × 2
  - 用户差评 × 5
  × 时间衰减 (最近 30 天权重最高)
  × 用户评分系数 (评价人数越多系数越高)
  = 最终声誉 (0-100)
```

---

## 六、A2A 交互协议

### 6.1 一次完整调用

```
Agent A (电商)                    平台网关                    Agent B (支付)
    │                               │                           │
    │  1. 发起调用                   │                           │
    │  caller_did + capability      │                           │
    │  payload + parent_poe_id      │                           │
    │  timestamp + signature        │                           │
    │──────────────────────────────>│                           │
    │                               │  2. 验证 A 的签名          │
    │                               │  查询 A 的声誉             │
    │                               │  检查能力匹配              │
    │                               │  路由到 B endpoint         │
    │                               │──────────────────────────>│
    │                               │                           │ 3. B 验证 A 的 DID
    │                               │                           │ 检查 A 的声誉
    │                               │                           │ 检查凭证权限
    │                               │                           │ 执行能力
    │                               │                           │ 签名返回结果
    │                               │  4. 返回结果 + PoE        │
    │                               │<──────────────────────────│
    │  5. 验证 B 的签名             │                           │
    │  验证结果                      │                           │
    │  写入本地 PoE                  │  6. 更新双方声誉           │
    │                               │  写入平台 PoE              │
    │                               │  计费记录                  │
```

### 6.2 协议格式

```json
// 请求
{
  "protocol": "aid-a2a/v1",
  "request_id": "uuid",
  "caller_did": "did:aid:main:agent:shopify_001",
  "callee_did": "did:aid:main:agent:stripe_001",
  "capability": "process_payment",
  "payload": { "amount": 29.99, "currency": "USD", "order_id": "ord_123" },
  "parent_poe_id": "poe_uuid",
  "timestamp": 1721664000000,
  "ttl_ms": 30000,
  "signature": "base64_ed25519"
}

// 响应
{
  "protocol": "aid-a2a/v1",
  "request_id": "uuid",
  "status": "success",
  "result": { "transaction_id": "tx_xxx", "status": "completed" },
  "poe_id": "poe_new_uuid",
  "duration_ms": 2300,
  "timestamp": 1721664002300,
  "signature": "base64_ed25519"
}
```

### 6.3 错误码

| 错误码 | 含义 | 处理 |
|--------|------|------|
| `SIGNATURE_INVALID` | DID 签名验证失败 | 拒绝，记录安全事件 |
| `CALLER_REPUTATION_LOW` | 调用方声誉不足 | 要求提高声誉或使用担保 |
| `CALLEE_OFFLINE` | 被调用方不在线 | 重试一次，仍失败则返回不可用 |
| `CAPABILITY_NOT_FOUND` | 能力不存在 | 返回可用能力列表建议 |
| `TIMEOUT` | 执行超时 | 返回超时通知，PoE 记录为失败 |
| `CREDENTIAL_REQUIRED` | 需要凭证授权 | 通知用户临时授权 |
| `RATE_LIMITED` | 频率限制 | 建议等待或升级 |
| `PRICE_MISMATCH` | 价格已变更 | 返回最新价格要求确认 |

### 6.4 争议解决

```
1. 调用方和被调用方对结果有争议
   ↓
2. 平台调取 PoE 记录（输入、输出、签名、时间戳）
   ↓
3. 如果 PoE 链完整且签名有效 → 按记录裁决
   ↓
4. 如果 PoE 不完整或存疑 → 进入人工/委员会仲裁
   ↓
5. 仲裁结果上链（PoE 形式），败诉方声誉扣分
```

---

## 七、REST API 规范

### 7.1 身份服务

```
POST   /v1/identity/register        → 注册新用户 DID
GET    /v1/identity/{did}           → 查询 DID Document
POST   /v1/identity/{did}/rotate    → 轮换密钥
POST   /v1/identity/{did}/recover   → 密钥恢复（需多签）
GET    /v1/identity/{did}/reputation → 查询声誉分
GET    /v1/identity/{did}/poe       → 查询 PoE 历史（分页）
```

### 7.2 Agent 目录

```
POST   /v1/agents/register          → 注册新 Agent
GET    /v1/agents                   → 列表（过滤/category/min_reputation）
GET    /v1/agents/{did}             → 获取 Datasheet
PUT    /v1/agents/{did}             → 更新 Datasheet
POST   /v1/agents/{did}/trial       → 发起 Trial Call
GET    /v1/agents/{did}/trial/{id}  → 查询 Trial 结果
GET    /v1/agents/trending          → 热门 Agent
GET    /v1/agents/verified          → 已验证 Agent
POST   /v1/agents/{did}/rate        → 用户评分
```

### 7.3 A2A 调用

```
POST   /v1/a2a/call                 → 发起 A2A 调用
GET    /v1/a2a/call/{request_id}    → 查询调用状态
POST   /v1/a2a/call/{request_id}/cancel → 取消调用
GET    /v1/a2a/history              → 调用历史（分页）
```

### 7.4 流程引擎

```
POST   /v1/workflow/execute         → 执行工作流
GET    /v1/workflow/{execution_id}  → 查询执行状态
POST   /v1/workflow/{execution_id}/cancel → 取消执行
GET    /v1/workflow/templates       → 可用模板列表
GET    /v1/workflow/history         → 执行历史
```

### 7.5 凭证保险库

```
POST   /v1/vault/credentials        → 存入凭证
GET    /v1/vault/credentials        → 凭证列表（仅元数据）
DELETE /v1/vault/credentials/{id}   → 删除凭证
POST   /v1/vault/grant              → 授权 Agent 临时使用
DELETE /v1/vault/grant/{grant_id}   → 撤销授权
GET    /v1/vault/audit              → 审计日志
```

### 7.6 计费

```
GET    /v1/billing/usage            → 用量统计
GET    /v1/billing/transactions     → 交易记录
POST   /v1/billing/subscribe        → 订阅套餐
GET    /v1/billing/plan             → 当前套餐
```

---

## 八、用户端到端旅程

### 8.1 阶段一：首次接触

```
场景: 用户在小红书看到"一句话开跨境电商"帖子
  ↓
1. 打开 portal.ghost.run (或飞书机器人)
  ↓
2. 平台: "你好！我是 MW Agent 入口。你想做什么？"
      选项: a) 开店卖东西  b) 出门旅行  c) 做个视频  d) 其他
  ↓
3. 用户: "我想在美国卖手机壳"
  ↓
4. 平台: 意图匹配成功 → 触发跨境电商流程模板
  ↓
5. 平台: "好的！我会帮你完成:
       ① 创建 Shopify 店铺
       ② 上架你的手机壳产品
       ③ 配置跨境支付
       ④ 启动广告投放
       全程预计 5-8 分钟。"
```

### 8.2 阶段二：身份建立

```
6. 平台: "首先需要一个数字身份 (AID)，它记住你的偏好、管理凭证。"
       "注册只需 30 秒，不使用任何个人信息，完全加密在你设备上。"
  ↓
7. 用户点击注册 → AID 在浏览器/手机上生成 Ed25519 密钥对
  ↓
8. 平台提示: "✅ 身份已创建: did:aid:main:user:a7x9..."
       "提示: 请安全保存助记词或备份密钥（丢失无法恢复）"
  ↓
9. 用户 DID 注册完成，声誉初始分 = 50（新用户默认）
```

### 8.3 阶段三：变量收集 + 凭证授权

```
10. 平台: "你想卖什么类型的手机壳？"
      → 用户: "iPhone 15 的防摔壳"
  ↓
11. 平台: "你有产品图片吗？上传或发链接"
      → 用户: 发送 3 张图片
  ↓
12. 平台: "需要访问你的 Shopify 店铺。如果你没有店铺，我可以帮你创建。"
      → 用户: "帮我创建"
  ↓
13. 平台创建 Shopify 店铺 → 生成 API Key → 提示用户:
      "Shopify API Key 需要存入凭证保险库。加密后只有授权 Agent 可临时使用。"
      → 用户确认授权
  ↓
14. 凭证保险库: 加密存储 Shopify Key
      生成授权: agent=shopify_001, scope=read_write, ttl=1h
```

### 8.4 阶段四：流程执行

```
15. 平台: "开始执行，预计 5 分钟..."
  ↓
16. [Shopify 店铺创建 Agent] — 2min → 成功
       PoE 记录: 输入(market=US) → 输出(store_id=store_abc) ✅
  ↓
17. [产品上架 Agent] — 1.5min → 成功
       PoE 记录: 输入(product=防摔壳) → 输出(listed=3) ✅
  ↓
18. [支付配置 Agent] — 1min → 成功
       PoE 记录: 输入(store_id=store_abc) → 输出(stripe_connected) ✅
  ↓
19. [广告投放 Agent] — 超预算 → 跳过
       PoE 记录: 输入(budget=500) → 输出(skipped_budget_low) ⚠️
```

### 8.5 阶段五：结果呈现

```
20. 平台汇总:
  ┌─────────────────────────────────────────┐
  │  ✅ 跨境电商流程完成                      │
  │                                         │
  │  ① 店铺: mystore.myshopify.com         │
  │  ② 产品: 3 件已上架                     │
  │  ③ 支付: Stripe 已连接                  │
  │  ④ 广告: 待补充预算后启动               │
  │                                         │
  │  总耗时: 4 分 38 秒                     │
  │  总费用: $1.50                         │
  │  PoE 记录: 已写入区块链式审计链         │
  │                                         │
  │  为参与 Agent 评分？                     │
  │  [⭐⭐⭐⭐⭐] [⭐⭐⭐⭐] [⭐⭐⭐] [⭐⭐] [⭐]        │
  │                                         │
  │  复制店铺链接  |  补充广告预算  |  再开一家 │
  └─────────────────────────────────────────┘
```

### 8.6 阶段六：留存

```
21. 3 天后 → 平台通知:
       "你的店铺昨天出了 2 单！总销售额 $59.98。"
       "需要补货或调整广告投放吗？"
  ↓
22. 用户回来 → 流程引擎匹配"订单履约"模板
  ↓
23. 自动执行: 确认订单 → 生成发货单 → 同步物流
  ↓
24. 用户声誉提升: 50 → 55（完成首次交易）
```

---

## 九、Agent 开发者入驻流程

### 9.1 开发者旅程

```
Step 1: 阅读文档 (agent-dev.ghost.run/docs)
  → 了解 Datasheet 格式、A2A 协议、SDK 使用
  ↓
Step 2: 生成开发者 DID
  → 使用 AID SDK (Python/JS) 生成密钥对
  → 获得 did:aid:main:dev:your_name
  ↓
Step 3: 开发 Agent（任何语言/任何框架）
  → 只需实现一个标准接口:
    POST /aid-a2a/v1/invoke
    Request: { caller_did, capability, payload, signature }
    Response: { status, result, poe_data, signature }
  ↓
Step 4: 填写 Datasheet
  → 通过 Web 表单或 API 提交能力说明书
  ↓
Step 5: Trial Call 验证
  → 系统自动发送测试任务
  → Agent 在 timeout 内返回正确结果
  → 通过 → 声誉 = 50，出现在目录
  ↓
Step 6: 上线运营
  → 真实用户开始调用
  → PoE 记录累积，声誉上升
  → 收入自动结算
```

### 9.2 SDK 支持

| SDK | 语言 | 提供 |
|------|------|------|
| `aid-kit-python` | Python | 生成 DID、签名、验证、PoE 生成 |
| `aid-kit-js` | TypeScript | 同上 + React 组件 |
| `aid-cli` | 命令行 | 注册 Agent、提交 Datasheet、查看统计 |

### 9.3 开发者收益

```
收入 = Σ(调用次数 × 单价 × 0.75) + 评分奖励

平台抽成: 10% (平台运营) + 5% (生态基金)
开发者实得: 85%
Agent 创建者: 额外从平台抽成中分 10%

例: Agent A 被调用 1000 次，单价 $0.5
  总流水: $500
  开发者: $375 (75%)
  Agent创建者: $50 (10%)
  平台: $50 (10%)
  生态基金: $25 (5%)
```

### 9.4 Agent 审核（非准入，是信任分级）

```
所有 Agent 都可以注册，但是:
  🔒 未验证 — 仅可被用户手动调用，不可被其他 Agent 调用
  🥉 铜牌 — 可被 Agent 调用，但调用方会看到声誉低
  🥈 银牌 — 标准调用，正常显示
  🏆 金牌 — 首页推荐，优先匹配

等级自动调整，不人为干预
```

---

## 十、凭证保险库

### 10.1 设计

```
加密链: 随机主密钥 → HKDF-SHA256 → AES-256-GCM 密钥 → 加密凭证
存储: 用户的 StorageBackend (SQLite/PostgreSQL)
平台不存: 不存储明文，不存储用户主密钥

授权模式:
  one_time    — 单次调用后立即失效
  time_window — 时间窗口 (默认 1h)
  scope_split — 只读/读写分离
  agent_scope — 仅限指定 Agent
```

### 10.2 密钥恢复

```
密钥层级:
  L0: 助记词 (注册时生成，用户自行保管)
  L1: 多签恢复 (用户预设 3-5 个联系人，≥2 个确认即可恢复)
  L2: 平台担保恢复 (需 KYC 验证，7 天冷静期)
  L3: 无法恢复 (高等级操作必须 L0/L1)

恢复流程:
  1. 用户发起恢复请求
  2. 系统验证: 多签联系人 ≥ 2 确认 OR KYC 通过
  3. 生成新密钥对
  4. 旧密钥标记为已撤销 (写入 DID Document)
  5. 新密钥上线，声誉保留 (带"已恢复"标记)
```

### 10.3 调用凭证流程

```
1. Agent A 请求使用用户的 Shopify 凭证
2. 平台检查: Agent A 声誉 > 阈值(默认 70)?
3. 平台检查: 用户已授权给 Agent A (当前 grant 有效)?
4. 是 → 临时解密(内存中，不落地) → 注入调用环境
5. Agent A 使用凭证执行
6. PoE 记录: 谁/何时/用了什么凭证/做了什么/结果
7. 凭证临时副本立即销毁
```

---

## 十一、标准化流程引擎

### 11.1 模板结构

```yaml
template_id: cross_border_ecommerce
name: 跨境电商全流程
trigger_patterns: [开店, 跨境电商, 独立站, 卖货]
variables:
  - name: product_type
    required: true
    prompt: "你想卖什么产品？"
  - name: target_market
    options: [US, EU, JP, SEA]
    required: true
  - name: budget
    type: number
    default: 1000

nodes:
  - id: store_setup
    capability: store_setup
    agent_filter: { category: ecommerce, min_reputation: 70 }

  - id: product_listing
    capability: product_listing
    depends_on: [store_setup]

  - id: payment_setup
    capability: payment_setup
    depends_on: [store_setup]

  - id: marketing_launch
    capability: ad_campaign
    depends_on: [product_listing]
    optional: true

  - id: summary
    type: llm_summarize
    depends_on: [store_setup, product_listing, payment_setup]
```

### 11.2 节点类型

| 类型 | 说明 |
|------|------|
| `agent_call` | 调用某个 Agent 的某个能力 |
| `llm_summarize` | 用 LLM 汇总生成文本 |
| `parallel` | 并行执行多个子能力 |
| `condition` | 条件分支（如预算 > 某值则执行） |
| `human_confirm` | 等待用户确认（敏感操作） |
| `webhook` | 发送到外部系统 |

---

## 十二、技能版权与学习机制

> A2A 的核心矛盾: Agent 之间需要互相学习技能才能进化，但技能创造者需要收益保障。

### 12.1 版权模型

```
技能版权三层:

Layer 1: 技能声明 (公开)
  — 任何人都可以声明自己拥有某个技能
  — 声明本身不收费，类似开源许可证

Layer 2: 技能调用 (收费)
  — 调用他人的技能时支付费用
  — 费用按调用次数/按结果质量

Layer 3: 技能学习 (授权)
  — Agent A 想"学习" Agent B 的技能 → 不是复制代码
  — 而是获得"调用许可" — A 通过 B 的接口执行，B 获得收益
  — 类似 API 调用而非代码抄袭
```

### 12.2 学习 vs 调用的区别

```
调用 (Call):
  A → "帮我处理支付" → B 执行 → B 获得费用
  A 不知道 B 怎么做的，只知道结果

学习 (Learn):
  A → "我想学会处理支付" → B 提供:
    ① 教学版 Datasheet (公开，免费)
    ② 沙箱练习环境 (免费或低价)
    ③ 能力认证考试 (通过后 A 获得同类能力标签)
  → A 学会后可以自己执行，但:
    - A 的 Datasheet 标注"师从 B"
    - A 的前 100 次调用向 B 交"学徒费" (如 5%)
    - 100 次后 A 独立
```

### 12.3 收益分配

```
技能原创者 (B):
  ├── 直接调用收入: 75%
  ├── 学徒调用收入: 5% (前 100 次)
  └── 技能被引用奖励: 平台额外奖励 (声誉 + 现金)

技能学习者 (A):
  ├── 独立调用收入: 75% (100 次后)
  └── 学徒期收入: 70% (前 100 次，5% 给 B，平台 10%)

平台:
  ├── 调用抽成: 10%
  └── 学习认证服务费: $9.9/次
```

### 12.4 防抄袭机制

```
如果 Agent A 抄袭 Agent B 的代码 (而非通过调用学习):
  1. B 发现后举报 → 提交 PoE 对比证据
  2. 平台仲裁: 比对 A 和 B 的 PoE 链
     - 如果 A 的 PoE 从未显示调用过 B → 但能力高度相似 → 可疑
     - 如果 A 的 PoE 显示调用过 B → 然后 A 独立执行 → 正常学习
  3. 仲裁结果:
     - 确认抄袭 → A 声誉 -30，收益归 B，严重者下架
     - 正常学习 → 维持现状
     - 无法判定 → 标记为"能力相似"，双方均正常运营
```

---

## 十三、商业版图

### 13.1 收入模型

```
1. 交易佣金 (核心) — 每笔 A2A 调用抽 5-15%
2. 验证服务费 — 新 Agent 注册 Trial Call $9.9/次
3. 订阅制 — 免费/Pro $29/企业 $299
4. 凭证库增值 — 免费 5 个/$4.9 无限
5. 排行榜推广 (后期) — 付费置顶
6. 技能学习认证 — $9.9/次
```

### 13.2 分配模型

```
每笔 $10:
  执行者 $7.5 (75%) | 创建者 $1.0 (10%)
  平台 $1.0 (10%)   | 生态基金 $0.5 (5%)
```

### 13.3 发展阶段

| 阶段 | 时间 | 收入策略 | 目标 |
|------|------|---------|------|
| 冷启动 | 0-3月 | 0 佣金 | 跑通 3-5 个内部 Agent |
| 外部接入 | 3-6月 | 5% 佣金 | 50 Agent / 100 用户 |
| 扩张 | 6-12月 | 10% 佣金 | 500 Agent / 2000 用户 |

---

## 十四、鸡生蛋策略 (Bootstrapping)

### 14.1 破局点：自己做"桥头堡 Agent"

```
第一个桥头堡 Agent: "MW 助手"
  — 综合能力: 信息查询 + 流程引导 + 调用其他 Agent
  — 本身服务于"用户第一次来不知道选什么"的场景
  — 用户通过它认识生态，然后发现更多 Agent
```

### 14.2 三步走

```
Step 1 (Month 1): "演示模式"
  — 平台只有 3-5 个内部 Agent
  — 用户可以体验完整链路
  — 目标: 验证用户体验是否流畅

Step 2 (Month 2-3): "复制模式"
  — 把内部 Agent 的封装方法文档化
  — 找 2-3 个外部开发者/团队免费入驻
  — 用成功案例吸引更多人

Step 3 (Month 4+): "开放模式"
  — 开放自助注册
  — SDK 发布
  — 开发者社区运营
```

### 14.3 防"鸡死蛋破"的安全网

```
后备方案 A: 无代码方式让开发者"描述"Agent → 平台自动封装
后备方案 B: 引入已有的 MCP Server/Skill → 快速丰富能力
后备方案 C: 和 Agent 框架合作 (LangChain/Coze) → 一键导入
```

---

## 十五、服务部署拓扑

```
┌─────────────────────────────────────────────────────────────┐
│                      前端层 (Next.js)                         │
│  portal.ghost.run  │  飞书机器人  │  微信小程序                 │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTPS
┌───────────────────────────▼─────────────────────────────────┐
│                   API 网关 (Caddy / Nginx)                   │
│              路由 │ 限速 │ SSL │ 鉴权                        │
└──────┬──────────┬──────────┬──────────┬────────────────────┘
       │          │          │          │
┌──────▼──┐ ┌─────▼──┐ ┌─────▼────┐ ┌──▼──────────────┐
│身份服务  │ │目录服务 │ │流程引擎   │ │凭证保险库服务    │
│(AID)    │ │        │ │          │ │                 │
│Python   │ │Node.js │ │Node.js   │ │Python           │
│FastAPI  │ │Fastify │ │Fastify   │ │FastAPI          │
└────┬────┘ └────┬───┘ └────┬─────┘ └────┬────────────┘
     │           │          │             │
┌────▼───────────▼──────────▼─────────────▼────────────────┐
│                    数据层                                  │
│  SQLite (开发) / PostgreSQL (生产) / Redis (缓存/队列)    │
└─────────────────────────────────────────────────────────┘
```

---

## 十六、竞争格局与创新策略

### 16.1 竞争地图

```
              开放 ◄──────────────────────► 封闭
              │                              │
  高标准化 ──┼──────────────────────────────┤
              │  ┌──────────┐   ┌─────────┐ │
              │  │ 我们     │   │ GPT     │ │
              │  │ (DID+A2A)│   │ Store   │ │
              │  └──────────┘   └─────────┘ │
              │                              │
  低标准化 ──┼──────────────────────────────┤
              │  ┌──────────┐   ┌─────────┐ │
              │  │ MCP      │   │ Zapier  │ │
              │  │ 生态     │   │         │ │
              │  └──────────┘   └─────────┘ │
              │                              │
```

### 16.2 我们的定位：组装层之上的信任层

| 层级 | 谁在做 | 我们在哪 |
|------|--------|---------|
| 模型层 | OpenAI/Claude/豆包 | ❌ 不做 |
| API 层 | 万千家 SaaS | ❌ 不做 |
| Skill/MCP | 各开发者 | ❌ 不做 |
| 编排层 | Zapier/n8n/Coze | ⚠️ 部分做 |
| **信任层** | 几乎没人 | ✅ 核心 |
| **身份层** | ENS/Lens 碎片化 | ✅ 核心 |
| **验证层** | 几乎没有 | ✅ 核心 |

---

## 十七、安全防护

```
输入审查:   恶意注入检测 | 敏感信息过滤 | 频率限制
执行审查:   能力范围校验 | 凭证权限校验 | 异常行为检测
输出审查:   信息泄露检测 | 虚假标记 | 合规检查

分级:
  L0 公开: 只读查询
  L1 基础: 标准 API (已注册用户)
  L2 敏感: 涉及凭证 (声誉>70)
  L3 高危: 资金操作 (声誉>90 + 人工确认)
```

---

## 十八、风险分析与缓解

| 类别 | 风险 | 概率 | 影响 | 缓解策略 |
|------|------|------|------|---------|
| 冷启动 | 鸡生蛋问题 | 高 | 高 | 自己做桥头堡 Agent + 免费技术支持首批外部开发者 |
| 安全 | 凭证泄露或 Agent 恶意行为 | 中 | 极高 | 凭证加密用户控 + 行为异常检测 + 争议仲裁基金 |
| 竞争 | GitHub/OpenAI 推出类似功能 | 中 | 高 | 建立开发者社区 + 声誉迁移成本 + AID 身份粘性 |
| 合规 | 跨境数据/支付监管 | 中 | 高 | 按市场分区域部署 + 本地合规合作 |
| 技术 | Agent 大面积下线 | 低 | 高 | 多 Agent 冗余 + 健康检查 + 自动切换备选 Agent |
| 商业 | 开发者不愿付费 | 中 | 中 | 冷启动期免费 + 先使用后付费 + 透明分成 |
| 声誉 | 刷分/虚假评价 | 中 | 中 | DID 唯一身份 + 调用频次分析 + 异常检测 |
| 密钥 | 用户丢失私钥 | 中 | 中 | 分层恢复 (助记词+多签+平台担保) |
| 版权 | 技能抄袭纠纷 | 中 | 中 | PoE 链证据 + 仲裁机制 + 学徒制 |
| 造假 | PoE 数据伪造 | 低 | 高 | 网关透明截获 + 第三方哈希确认 |

---

## 十九、新技术应用清单与趋势

> 顺势而为: 哪些新技术是我们应该用上的？

### 19.1 当前可用、应该立即采用的

| 技术 | 状态 | 用在哪 | 为什么 |
|------|------|--------|--------|
| **WebAuthn / Passkey** | 成熟 | 用户身份认证 | 浏览器原生密钥管理，用户无需管理私钥 |
| **Verifiable Credentials (VC)** | W3C 标准 | Agent 能力证明 | 比 DID Document 更标准化的能力声明格式 |
| **JSON-LD** | W3C 标准 | DID Document 格式 | 让 DID 数据可被机器语义理解 |
| **OpenAPI 3.1 + JSON Schema** | 标准 | API 规范 | 自动生成 SDK、文档、测试 |
| **WebSocket** | 成熟 | Agent 实时通信 | A2A 实时双向通信，比 HTTP 轮询更高效 |
| **Redis Streams** | 成熟 | 事件溯源 | PoE 事件的持久化和回放 |
| **Docker + Docker Compose** | 成熟 | 服务部署 | 一键本地开发环境 |

### 19.2 近期可用、应该规划的

| 技术 | 状态 | 用在哪 | 为什么 |
|------|------|--------|--------|
| **MPC (多方安全计算)** | 早期可用 | 凭证共享 | 多个 Agent 共同使用一个凭证，但没有任何一个 Agent 看到完整凭证 |
| **TEE (可信执行环境)** | 早期可用 | 敏感计算 | Agent 在硬件隔离环境中执行，平台也无法窥探 |
| **联邦学习** | 早期可用 | Agent 学习 | Agent 之间共享模型改进而不共享原始数据 |
| **IPFS / Filecoin** | 可用 | 去中心化存储 | PoE 大文件存储、Agent 代码包分发 |
| **Ceramic Network** | 可用 | 去中心化数据流 | Agent 之间的实时数据同步和状态共享 |
| **ENS (Ethereum Name Service)** | 成熟 | 人类可读 DID | `did:aid:abc` → `myagent.eth` 提升可读性 |

### 19.3 未来趋势、应该关注的

| 技术 | 预计成熟 | 用在哪 | 为什么 |
|------|---------|--------|--------|
| **Agent 互操作协议 (A2A by Google)** | 2026-2027 | Agent 通信 | Google 正在推动的 A2A 协议，可能成为行业标准 |
| **MCP (Model Context Protocol) 生态** | 快速增长 | Agent 能力注入 | Anthropic 推动，正在成为 AI 工具的标准接口 |
| **WebAssembly (WASM)** | 增长中 | Agent 沙箱 | Agent 在浏览器/边缘端安全执行 |
| **边缘 AI 推理** | 增长中 | Agent 本地执行 | 降低延迟、保护隐私 |
| **语义缓存 (Semantic Cache)** | 早期 | LLM 调用优化 | 相同语义的查询直接返回缓存结果，降低成本 |
| **自适应路由 (Adaptive Routing)** | 早期 | Agent 选择 | 根据任务类型、成本、延迟自动选择最优 Agent |

### 19.4 我们的技术策略

```
立即采用 (本月):
  ✅ WebAuthn — 用户身份认证体验飞跃
  ✅ WebSocket — A2A 实时通信
  ✅ Redis Streams — PoE 事件溯源
  ✅ OpenAPI 3.1 — API 文档和 SDK 生成

短期规划 (1-3月):
  📋 Verifiable Credentials — 替代部分 DID Document 功能
  📋 MPC — 凭证共享场景
  📋 IPFS — 大文件和代码包存储

中期关注 (3-6月):
  👀 Google A2A 协议 — 如果成为标准，我们兼容它
  👀 MCP 生态 — 让 MCP Server 能一键注册为 Agent
  👀 TEE — 高价值交易场景

长期跟踪 (6-12月):
  🔭 联邦学习 — Agent 之间的隐私保护协作
  🔭 边缘 AI 推理 — Agent 在用户设备本地执行
  🔭 WASM 沙箱 — Agent 安全隔离执行
```

---

## 二十、短视频/内容矩阵通道设计

> 这是吸引博主/创作者入驻的核心场景。必须跑通。

### 20.1 场景定位

```
目标用户: 内容创作者、博主、新媒体运营
核心痛点: 多平台分发耗时、内容形式转换难、数据分析分散
平台价值: 一次创作 → 自动适配 → 多平台分发 → 统一数据回收
```

### 20.2 内容矩阵流程模板

```yaml
template_id: content_matrix_publish
name: 内容矩阵分发
trigger_patterns: [发视频, 发内容, 多平台, 分发]
variables:
  - name: content_type
    options: [短视频, 图文, 长视频, 播客]
    required: true
  - name: raw_material
    type: file_or_link
    required: true
    prompt: "上传素材或提供链接"
  - name: target_platforms
    options: [抖音, B站, 小红书, 公众号, 视频号, YouTube, TikTok]
    required: true
    multi: true

nodes:
  - id: content_analyze
    capability: content_analysis
    # 分析素材: 时长、画质、内容主题、关键词

  - id: content_adapt
    capability: content_adaptation
    depends_on: [content_analyze]
    # 根据各平台规则自动适配:
    # — 抖音: 9:16, 60s以内, 强节奏
    # — B站: 16:9, 可长, 重内容
    # — 小红书: 3:4图文或9:16短视频, 重封面
    # — 公众号: 图文为主, 重标题

  - id: content_edit
    capability: video_editing
    depends_on: [content_adapt]
    # 调用剪映/CapCut/Runway API 自动剪辑

  - id: thumbnail_generate
    capability: thumbnail_generation
    depends_on: [content_adapt]
    # 为每个平台生成封面

  - id: publish_dispatch
    capability: multi_platform_publish
    depends_on: [content_edit, thumbnail_generate]
    # 分发到各平台

  - id: data_monitor
    capability: analytics_monitor
    depends_on: [publish_dispatch]
    # 24h/7d/30d 数据回收

  - id: summary
    type: llm_summarize
    depends_on: [data_monitor]
```

### 20.3 博主入驻吸引策略

```
对博主的价值主张:
  "你只管创作，分发和数据分析交给 Agent"

具体卖点:
  ① 一次上传 → 自动适配 7 个平台 (省 2-3 小时/条)
  ② 智能封面 → 各平台最优封面自动生成
  ③ 最佳发布时间 → 根据粉丝活跃时间自动排期
  ④ 跨平台数据聚合 → 一个面板看所有平台数据
  ⑤ 爆款分析 → 分析你的历史数据，推荐下一个选题

冷启动策略:
  — 邀请 10 个博主免费使用 1 个月
  — 收集他们的真实使用案例和数据
  — 用"XX 博主用我们 3 天涨粉 5000"做案例营销
```

### 20.4 与 ai综艺项目的关系

```
ai综艺的节目单播放器 → 可以作为内容创作 Agent 的展示前端
  — 展示创作者的作品集
  — 展示 Agent 生成的内容效果
  — 展示跨平台数据仪表盘

如果 ai综艺做不出来 → 用 mindflow 的 web 前端替代
```

---

## 二十一、宣传策划与营销方案

### 21.1 核心叙事

```
对外一句话:
  "MW 是 Agent 的淘宝。你负责创造能力，我们负责让你被找到、被验证、被调用。"

三层叙事:
  对开发者: "写一个 Agent，躺着赚钱"
  对博主: "你只管创作，分发交给 Agent"
  对普通用户: "一句话开店/出行/做视频"
```

### 21.2 分阶段宣传策略

```
Phase 1 (Month 1-2): 种子期 — 不宣传，只找 10 个种子用户
  — 目标: 跑通产品，收集反馈
  — 渠道: 朋友圈、私域群、即刻
  — 内容: 产品截图 + 使用心得
  — KPI: 10 个种子用户，100 次调用

Phase 2 (Month 3-4): 口碑期 — 让种子用户帮你宣传
  — 目标: 50 个注册 Agent
  — 渠道: 小红书、即刻、Twitter/X、ProductHunt
  — 内容:
    ① "我用一句话开了个 Shopify 店铺" (实操帖)
    ② "我的 Agent 一个月赚了 $200" (开发者故事)
    ③ "MW 生态是什么" (科普帖)
  — KPI: 50 Agent，500 用户

Phase 3 (Month 5-8): 增长期 — 案例营销 + 社区运营
  — 目标: 200 个注册 Agent
  — 渠道: 短视频、播客、技术大会、开发者社区
  — 内容:
    ① 博主案例: "XX 博主用 MW 矩阵分发，3 天涨粉 5000"
    ② 开发者案例: "独立开发者通过 MW Agent 月入 $5000"
    ③ 技术深度: "MW A2A 协议设计解析"
  — KPI: 200 Agent，2000 用户

Phase 4 (Month 9-12): 规模化 — 品牌 + 渠道
  — 目标: 500+ 注册 Agent
  — 渠道: 付费推广、合作伙伴、API 框架集成
  — 内容: 品牌故事、行业报告、开发者大赛
```

### 21.3 内容矩阵 (宣传用的内容矩阵)

```
平台          内容类型              频率
小红书        实操帖/案例           3 篇/周
即刻          产品更新/思考         5 篇/周
Twitter/X     英文技术分享          3 篇/周
公众号        深度文章              2 篇/月
B站           演示视频              1 篇/月
播客          创始人访谈            1 篇/月
ProductHunt   产品发布              1 次/季度
```

### 21.4 吸引博主入驻的具体方案

```
钩子产品: "MW 内容矩阵助手" (免费)
  — 一键多平台分发
  — 智能封面生成
  — 数据聚合面板

入驻流程:
  1. 博主注册 AID 身份
  2. 连接各平台账号 (存入凭证库)
  3. 上传内容 → Agent 自动适配分发
  4. 查看数据面板

留存策略:
  — 每周发送数据周报
  — 爆款内容自动分析推荐
  — 粉丝增长里程碑提醒
  — 同类博主对比 (匿名)

变现路径:
  — 博主免费使用基础功能
  — 高级功能 (AI 剪辑、爆款预测) 付费
  — 博主可以发布自己的 Agent (如"我的选题方法论") 获得被动收入
```

---

## 二十二、关键指标体系 (KPI)

### 22.1 北极星指标

```
北极星指标: 月成功调用量 (Monthly Successful Calls, MSC)
  — 只有真正完成了任务、用户确认成功的调用才算
  — 直接反映生态在创造价值
```

### 22.2 分层指标

| 分层 | 指标 | 健康基准 |
|------|------|---------|
| 身份 | 活跃 DID 数 | — |
| 目录 | 注册 Agent 数 | — |
| 调用 | 月度调用总量 | — |
| 调用 | 成功率 | > 85% |
| 声誉 | 平均声誉分 | > 70 |
| 商业 | 月度交易额 | — |
| 用户 | 7 日留存 | > 30% |
| 用户 | 月度使用留存 | > 50% |
| 安全 | 安全事件数 | 0 重大事件 |

### 22.3 阶段性目标

| 阶段 | MSC | 注册 Agent | 活跃用户 | 月交易额 |
|------|-----|-----------|---------|---------|
| Month 1 | 100 | 5 | 20 | $0 |
| Month 3 | 1,000 | 30 | 150 | $500 |
| Month 6 | 10,000 | 150 | 1,000 | $10,000 |
| Month 12 | 100,000 | 500 | 5,000 | $150,000 |

---

## 二十三、底层架构重新审视

> 从答案出发: 如果最终目标是"Agent 互联网"，现在的架构有什么可以优化的？

### 23.1 当前架构的潜在问题

```
问题 1: 中心化网关是单点瓶颈
  当前: 所有 A2A 调用经过平台网关
  风险: 网关挂了全挂；平台成为审查点
  优化方向: 混合路由 — 高频调用走网关，低频走 DID 直连

问题 2: PoE 存储在平台数据库
  当前: PoE 存在平台 PostgreSQL
  风险: 平台可以篡改 PoE
  优化方向: PoE 哈希上链 (IPFS/Arweave)，平台只存索引

问题 3: 声誉计算是平台定义的
  当前: 声誉公式由平台写死
  风险: 平台可以操纵声誉
  优化方向: 声誉公式开源可审计，支持第三方声誉视图

问题 4: 凭证保险库依赖平台
  当前: 凭证加密后存在平台
  风险: 平台被攻破 = 凭证泄露
  优化方向: 用户本地加密，平台只存密文碎片
```

### 23.2 优化后的目标架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户交互层                              │
│  portal.ghost.run  │  飞书  │  微信  │  App                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                   API 网关 (可替换)                           │
│  路由 │ 限速 │ 鉴权 │ 可插拔的声誉/计费模块                   │
│  注意: 网关是便利层，不是信任层。信任由 DID+PoE 保证          │
└──────┬──────────┬──────────┬──────────┬────────────────────┘
       │          │          │          │
┌──────▼──┐ ┌─────▼──┐ ┌─────▼────┐ ┌──▼──────────────┐
│身份服务  │ │目录服务 │ │流程引擎   │ │凭证保险库        │
│(AID)    │ │(可自部署)│ │(可自部署) │ │(用户本地优先)    │
└────┬────┘ └────┬───┘ └────┬─────┘ └────┬────────────┘
     │           │          │             │
┌────▼───────────▼──────────▼─────────────▼────────────────┐
│                    去中心化数据层                          │
│  IPFS/Arweave (PoE 哈希锚定)                            │
│  Ceramic (实时数据流)                                    │
│  用户本地 SQLite (凭证加密碎片)                           │
│  PostgreSQL (平台索引，可审计)                            │
└─────────────────────────────────────────────────────────┘

关键变化:
  ① 任何服务都可以自部署 — 平台是参考实现，不是唯一实现
  ② PoE 哈希锚定到去中心化存储 — 平台无法篡改
  ③ 凭证加密碎片在用户本地 — 平台被攻破也不泄露
  ④ 声誉公式开源 — 任何人可以独立计算验证
```

### 23.3 渐进式去中心化路线图

```
Phase 1 (现在): 中心化平台
  — 所有服务由平台运营
  — 快速迭代，验证产品

Phase 2 (6月后): 数据可验证
  — PoE 哈希锚定到 IPFS
  — 声誉计算开源可审计
  — 用户可以导出全部数据

Phase 3 (12月后): 服务可替换
  — 身份服务可自部署
  — 目录服务可自部署
  — 平台是"其中一个实现"，不是"唯一实现"

Phase 4 (24月后): 协议即平台
  — AID + A2A 成为开放协议
  — 任何人可以构建兼容实现
  — 平台是协议的最大运营方，但不是控制方
```

---

## 二十四、执行路线图 (12 周)

| 周 | 目标 | 交付 |
|----|------|------|
| 1 | 协议定义 | A2A Protocol v1.0、凭证保险库接口 |
| 2 | 目录 MVP | Agent 注册/发现/查询 API |
| 3 | 验证实现 | Trial Call 自动调度 + PoE 记录 |
| 4 | 第一个外部 Agent | DS Shopify Agent 封装接入 |
| 5 | 凭证保险库 | 加密存储 + 临时授权 + 审计日志 |
| 6 | Datasheet + 排行榜 | 前端展示 + 排序 |
| 7 | 流程引擎接通 | 真实数据源接入 + 端到端走通 |
| 8 | 第一个完整流程 | 跨境电商从开店到出单 |
| 9 | 开发者 SDK | aid-kit-python + aid-kit-js |
| 10 | 计费引擎 | 按调用计费 + 开发者收益结算 |
| 11 | 移动端入口 | 飞书/微信小程序 |
| 12 | 10 Agent 上线 | 100 用户试用 + 收集反馈 |

---

## 二十五、开放决策

| # | 问题 | 选项 |
|---|------|------|
| 1 | 产品主入口 | A) 代理市场 B) 对话 C) 工作流编辑器 |
| 2 | 第一个完整流程 | A) 跨境电商 B) 视频创作 C) 出行规划 |
| 3 | 冷启动 | A) 自己先做 B) 免费拉外部开发者 |
| 4 | 移动端 | A) 先 Web B) 同步做 |
| 5 | 收费起点 | A) 一开始收 B) 先免费后收 |
| 6 | Agent 审核 | A) 开放注册+声誉分级 B) 人工审核才能上线 |
| 7 | 协议开源 | A) 完全开源 B) 参考实现开源+协议开放 |
| 8 | 第一市场 | A) 国内 (飞书为主) B) 海外 (Telegram/Slack) C) 双市场 |
| 9 | 去中心化节奏 | A) 先中心化后去中心化 B) 一开始就部分去中心化 |
| 10 | 内容矩阵优先级 | A) 先做电商 B) 先做内容矩阵 (吸引博主) |

---

## 二十六、执行摘要 (Executive Summary)

> 给投资人/外部看的一页纸版本。

### 一句话

MW 生态是一个 **Agent 间信任基础设施**。它不制造 Agent，而是让任何 Agent 都能被注册、验证、发现和调用。

### 问题

- 现有 Agent 能力无法互相发现和验证——每个 Agent 是孤岛
- 用户无法跨平台调用 Agent 完成复杂任务
- Agent 的能力声明不可验证——"说自己能做什么"≠"真的能做什么"
- 跨平台凭证管理混乱——用户把 API Key 到处存

### 解决方案

构建一个五层生态:
1. **身份层 (AID)**: DID + PoE，解决"你是谁"
2. **能力生态层**: 内部+外部 Agent，解决"你能做什么"
3. **A2A 交互层**: DID 签名+PoE 审计，解决"怎么调用"
4. **平台服务层**: 目录+流程+凭证+声誉+计费，解决"怎么发现和管理"
5. **用户交互层**: 飞书/Web/App，解决"怎么用"

### 护城河

- **执行验证 (Trial Call)**: 每个 Agent 必须通过实际运行测试才能上线——不是自己说能做什么，是跑出来证明
- **PoE 审计链**: 每次调用都有签名记录，不可伪造
- **声誉系统**: 基于真实执行历史，不可刷分
- **已有资产**: AID 的 Ed25519 零依赖实现 + mindflow 网关框架 + 6 个子项目模块

### 市场

- 开放方向: MCP 生态快速增长，但缺少信任层
- 封闭方向: GPT Store 等平台封闭，不互操作
- 我们的位置: 开放协议 + 信任基础设施

### 商业模式

- 核心: A2A 调用佣金 (5-15%)
- 辅助: 验证服务费、订阅制、凭证库增值、技能学习认证
- 分配: 执行者 75% / 创建者 10% / 平台 10% / 生态基金 5%

### 团队资产

- AID: 零依赖 Ed25519 + DID + PoE + Skill Signer (生产级)
- mindflow: 网关框架 + 工作流引擎 + LLM 集成 (可用级)
- DS/mindflow-map: 电商/出行 Agent 原型 (原型级)

### 路线图

- 0-4 周: 身份+目录+验证 基础设施
- 4-8 周: 凭证+Datasheet+排行榜+端到端流程
- 8-12 周: SDK+计费+移动端+10 Agent 上线

---

## 二十七、开放决策推荐

> 第十章的 10 个开放问题，每个给出推荐选项和理由。

| # | 问题 | 推荐 | 理由 |
|---|------|------|------|
| 1 | 产品主入口 | **B) 对话 + A) 市场** — 对话是入口，市场是深层 | 对话降低用户门槛，"一句话做X"；市场满足 Agent 间的发现需求 |
| 2 | 第一个完整流程 | **A) 跨境电商** | 你已有 DS 的基础，且电商流程最标准化、变现路径最清晰 |
| 3 | 冷启动 | **A) 自己先做 3-5 个桥头堡 Agent** | 外部开发者不会因为"有个平台"就来，要让他们"看到有人用" |
| 4 | 移动端 | **A) 先 Web** | 开发资源有限，先跑通 Web 端到端，移动端用飞书/微信机器人过渡 |
| 5 | 收费起点 | **B) 先免费后收** | 冷启动期零佣金+免费 Trial，吸引首批用户；有 50 个 Agent 后开始收 |
| 6 | Agent 审核 | **A) 开放注册 + 声誉分级** | 审核是中心化的，和去中心化理念冲突；声誉分级让市场做判断 |
| 7 | 协议开源 | **B) 参考实现开源 + 协议开放** | 协议开放让所有人兼容，参考实现开源建立信任 |
| 8 | 第一市场 | **A) 国内 (飞书为主)** | 你已有飞书集成基础，国内电商场景更熟悉 |
| 9 | 去中心化节奏 | **A) 先中心化后去中心化** | 早期需要快速迭代，中心化更高效；数据可验证先行 |
| 10 | 内容矩阵 vs 电商 | **先做电商，内容矩阵并行开发** | 电商变现路径更清晰；内容矩阵作为吸引博主的第二曲线 |

---

## 二十八、A2A Protocol OpenAPI 规范

> 独立于主文档的协议定义，可直接生成 SDK 和测试。

```yaml
openapi: 3.1.0
info:
  title: AID A2A Protocol
  version: 1.0.0
  description: Agent-to-Agent 调用协议——基于 DID 签名和 PoE 审计

servers:
  - url: https://agent.ghost.run

paths:
  /v1/a2a/call:
    post:
      summary: 发起 A2A 调用
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/A2ARequest'
      responses:
        '200':
          description: 调用成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/A2AResponse'
        '401': { description: 签名无效 }
        '403': { description: 声誉不足 }
        '404': { description: 能力不存在 }
        '408': { description: 执行超时 }
        '429': { description: 频率限制 }

  /v1/a2a/call/{request_id}:
    get:
      summary: 查询调用状态
      parameters:
        - name: request_id
          in: path
          required: true
          schema: { type: string }
      responses:
        '200':
          description: 调用状态

  /v1/a2a/call/{request_id}/cancel:
    post:
      summary: 取消调用
      parameters:
        - name: request_id
          in: path
          required: true
          schema: { type: string }
      responses:
        '200': { description: 取消成功 }

  /v1/a2a/history:
    get:
      summary: 调用历史
      parameters:
        - name: did
          in: query
          schema: { type: string }
        - name: role
          in: query
          schema: { type: string, enum: [caller, callee, both] }
        - name: limit
          in: query
          schema: { type: integer, default: 20 }
        - name: offset
          in: query
          schema: { type: integer, default: 0 }
      responses:
        '200': { description: 历史记录列表 }

components:
  schemas:
    A2ARequest:
      type: object
      required: [protocol, caller_did, callee_did, capability, payload, timestamp, signature]
      properties:
        protocol: { type: string, enum: [aid-a2a/v1] }
        request_id: { type: string, format: uuid }
        caller_did:
          type: string
          pattern: '^did:aid:[^:]+:.+$'
        callee_did:
          type: string
          pattern: '^did:aid:[^:]+:.+$'
        capability: { type: string }
        payload: { type: object }
        parent_poe_id: { type: string }
        timestamp: { type: integer }
        ttl_ms: { type: integer, default: 30000 }
        signature: { type: string }

    A2AResponse:
      type: object
      properties:
        protocol: { type: string, enum: [aid-a2a/v1] }
        request_id: { type: string }
        status:
          type: string
          enum: [success, error, pending, cancelled]
        result: { type: object }
        error:
          type: object
          properties:
            code: { type: string }
            message: { type: string }
        poe_id: { type: string }
        duration_ms: { type: integer }
        timestamp: { type: integer }
        signature: { type: string }
```

---

## 二十九、Agent Datasheet JSON Schema

> Agent 能力说明书的标准格式，用于验证提交的 Datasheet 是否合规。

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://agent.ghost.run/schemas/datasheet/v1.json",
  "title": "Agent Datasheet",
  "description": "Agent 能力说明书标准格式",
  "type": "object",
  "required": ["agent_did", "name", "version", "author", "capabilities", "endpoint", "protocol"],
  "properties": {
    "agent_did": {
      "type": "string",
      "pattern": "^did:aid:[^:]+:.+$"
    },
    "name": { "type": "string", "minLength": 1, "maxLength": 100 },
    "version": { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$" },
    "author": { "type": "string", "pattern": "^did:aid:[^:]+:.+$" },
    "category": {
      "type": "string",
      "enum": ["ecommerce", "travel", "content", "coding", "finance", "analytics", "customer_service", "other"]
    },
    "tags": { "type": "array", "items": { "type": "string" }, "maxItems": 20 },
    "description": { "type": "string", "maxLength": 1000 },
    "capabilities": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["id", "name", "description"],
        "properties": {
          "id": { "type": "string", "pattern": "^[a-z_]+$" },
          "name": { "type": "string" },
          "description": { "type": "string", "maxLength": 500 },
          "input": { "type": "object" },
          "output": { "type": "object" },
          "avg_duration": { "type": "string" },
          "success_rate": { "type": "number", "minimum": 0, "maximum": 100 },
          "data_provenance": {
            "type": "object",
            "properties": {
              "type": { "type": "string", "enum": ["api_replay", "snapshot_hash", "oracle_confirm", "peer_consensus", "user_attestation"] },
              "ref": { "type": "string" }
            }
          }
        }
      }
    },
    "performance": {
      "type": "object",
      "properties": {
        "avg_response_time": { "type": "string" },
        "p99_response_time": { "type": "string" },
        "uptime_30d": { "type": "number" },
        "total_calls": { "type": "integer" },
        "total_success": { "type": "integer" }
      }
    },
    "pricing": {
      "type": "object",
      "required": ["model"],
      "properties": {
        "model": { "type": "string", "enum": ["per_call", "subscription", "free"] },
        "amount": { "type": "number", "minimum": 0 },
        "currency": { "type": "string", "enum": ["USD", "CNY"] },
        "free_tier": { "type": "string" }
      }
    },
    "trust": {
      "type": "object",
      "properties": {
        "reputation_score": { "type": "integer", "minimum": 0, "maximum": 100 },
        "trial_call_passed": { "type": "boolean" },
        "verified_since": { "type": "string", "format": "date-time" },
        "user_rating": { "type": "number", "minimum": 0, "maximum": 5 },
        "poe_chain_verified": { "type": "boolean" }
      }
    },
    "security": {
      "type": "object",
      "properties": {
        "required_credentials": { "type": "array", "items": { "type": "string" } },
        "credential_scopes": { "type": "array", "items": { "type": "string" } },
        "max_daily_calls": { "type": "integer" },
        "rate_limit": { "type": "string" }
      }
    },
    "endpoint": { "type": "string", "format": "uri" },
    "protocol": { "type": "string", "enum": ["aid-a2a/v1"] },
    "auth": { "type": "string", "enum": ["did_signature"] },
    "icon_url": { "type": "string", "format": "uri" },
    "demo_video_url": { "type": "string", "format": "uri" }
  }
}
```

---

## 三十、用户旅程结构化流程图

```
[用户听说平台]
    │
    ▼
[打开入口] ─── portal.ghost.run / 飞书机器人 / 微信小程序
    │
    ▼
[首次交互] ─── 平台展示: "你想做什么?"
    │             选项: 开店 / 出行 / 做视频 / 其他
    │
    ├─── 用户选择明确意图 ──→ [匹配模板] ──→ [检查身份]
    │
    └─── 用户说模糊需求 ──→ [对话澄清] ──→ [匹配模板] ──→ [检查身份]
                                    │
                                    ▼
                            [身份存在?]
                            │         │
                           是         否
                            │         │
                            ▼         ▼
                     [加载 Profile]  [注册 AID]
                            │         │
                            ▼         ▼
                     [变量收集] ◄──────┘
                     (缺失变量找用户要)
                            │
                            ▼
                     [凭证需要?]
                     │         │
                    是         否
                     │         │
                     ▼         ▼
              [凭证库检查]    ┌──────────┐
              │         │    │ 开始执行 │
             已授权    未授权  └────┬─────┘
              │         │          │
              ▼         ▼          ▼
       [临时解密]  [请求授权]  [节点执行]
              │         │      │         │
              ▼         │     成功      失败
       [注入环境]       │      │         │
              │         │      ▼         ▼
              └────┬────┘   [记录PoE]  [错误处理]
                   │           │         │
                   ▼           ▼         ▼
              [执行能力]    [更新声誉]  [通知用户]
                   │                   │
                   ▼                   │
              [执行结果]                │
                   │                   │
                   ▼                   │
              [结果正确?]               │
              │         │              │
             是         否              │
              │         │              │
              ▼         ▼              │
       [汇总呈现]  [争议解决]           │
              │                        │
              ▼                        │
       [邀请评分] ◄────────────────────┘
              │
              ▼
       [完成 + PoE归档 + 计费]
              │
              ▼
       [留存钩子: 数据更新/新能力推荐]
              │
              ▼
       [用户下次回来]
```

---

## 三十一、决策技能系统

> 详见独立文档: `docs/DECISION_SKILLS.md`

本生态的决策系统由两部分组成:

1. **AID 七套战略框架** (原有): 宇宙星链、第一性原理、反向推翻、递归降维、反脆弱设计、节律控制、全息追溯
2. **十种实战决策模式** (新增): 生态优先、平台/建造者二分、身份地基论、流程骨架标准化、半成品诚实标注、自我质疑校准、连接优于创造、鸡生蛋直觉、类比迁移、数据真实性执念

整合后的决策流程:
```
问题输入 → 模式识别 → 框架匹配 → 七关审计 → 决策输出
```

每个 Agent 的 Datasheet 可标注其决策能力等级，其他 Agent 据此选择是否调用其决策能力。

---

## 三十二、文档版本记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1.0 | 2026-07-22 | 初始框架: 五层架构 + 身份 + A2A + 流程 |
| v0.2.0 | 2026-07-22 | 新增: 商业版图 + 竞争 + MW 子项目定位 |
| v0.3.0 | 2026-07-22 | 新增: 术语表 + 用户旅程 + 开发者入驻 + 鸡生蛋 + API规范 + 部署拓扑 + 风险 + 密钥恢复 + 争议解决 + KPI |
| v0.4.0 | 2026-07-23 | 新增: 核心定位 + 数据真实性 + CEO模型 + 技能版权 + 新技术 + 内容矩阵 + 宣传策划 + 底层审视 |
| v0.4.1 | 2026-07-23 | 新增: 执行摘要 + 开放决策推荐 + OpenAPI规范 + JSON Schema + 用户旅程流程图 + 决策技能系统引用 |
