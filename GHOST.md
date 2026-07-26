# Ghost 项目 -- 完整框架与现状实录

> **版本 2.0** | **2026-07-25**
> **项目宪法：** 不做单点AI工具、不做工作流编排、不局限于技能市场。打造**国内合规、以人为核心的Web4.0人机共生基础设施**。
> **核心载体：** Alpha-ID（个人终身DID身份）
> **总纲：** 身份->记忆->调度->网关->通信，五层地基打通后才是业务和商业。

---

## 项目基调（来自基准文档 Ghost Web4.0.md）

### 核心理念
| 维度 | 定位 |
|:-----|:------|
| 做什么 | 让人类与AI智能体共同成为互联网原生网络公民，收回个人数字数据主权 |
| 不做什么 | 不碰区块链/虚拟币/NFT，不发代币，所有数据部署国内服务器，遵循《个人信息保护法》 |
| 最终形态 | 一人一生唯一Alpha-ID + 双大脑架构 + 机器可读资讯生态 + MCP技能统一适配 + Obsidian知识闭环 + 合规双边商业生态 |

### 四代互联网定位
| 时代 | 痛点 | Ghost 的突破 |
|:-----|:------|:-------------|
| Web1.0 | 人单向浏览，无交互 | - |
| Web2.0 | 账号/数据归属平台，网页充斥广告机器难解析 | 搭建脱离Web2杂乱网页的机器可读内容生态 |
| Web3.0 | 侧重链上资产，缺AI自动化 | 以DID身份为根基，叠加A2A智能体协同 |
| Web4.0 | 工具孤岛、权限混乱、记忆碎片化 | Alpha-ID + 双链记忆 + A2A + 标准工作流 + 商业生态 |

---

## 三个入口的衔接关系

### 你的日常使用流程

你平时的工作流是这样的：

`
                    [你]
                      |
         +------------+-------------+
         |            |              |
      [豆包]        [飞书]       [Ghost.html]
     日常聊天      总对话助理       Web展示
     知识输出      & 平台对接
         |            |              |
         v            v              v
  +-----------+/+-----------+\  +----------+
  | Obsidian  ||  整个平台   |  | 仪表盘   |
  | 知识沉淀   || 身份/记忆  |  | 注册/聊天|
  | (P1)      || 业务/查询  |  | 知识浏览 |
  +-----------+| 调用任何能力|  +----------+
               +-------------+
                     |
          +----------+----------+
          |          |          |
          v          v          v
      [alphaid]  [nebula]   [flow/api]
      身份/记忆   工作流     注册链路
      AgentLoop  飞书对接
`

### 每个入口做什么

| 入口 | 本质 | 你的使用方式 |
|:----:|:-----|:------------|
| **豆包** | 知识输入 | 日常聊天输出思想、碎片知识 -> 豆包自身LLM整理 -> Obsidian知识卡片 |
| **飞书** | 总对话助理 | 自然语言对话 -> Gateway -> 调整个平台能力（身份/记忆/业务/聊天/查询） |
| Ghost.html | Web展示 | 浏览器打开看仪表盘、注册Alpha-ID、对话聊天、浏览知识库 |

### 关键理解

**飞书不只是工作指令。** 它是你的总助理，你平时想查什么、想做什么、想去哪里，直接跟飞书机器人说就行。它背后对接的是整个 Ghost 平台——身份、记忆、业务、工具，全部通过对话调用。

**豆包不只是聊天。** 它是你的知识入口。你跟豆包聊过的内容、输出的思考、碎片信息，豆包自己整理后写到 Obsidian，变成可查询的知识卡片。

**Ghost.html 不是主入口。** 它是 Web 展示界面，方便你在电脑上操作注册、看数据、浏览知识。

> 三个入口各司其职：豆包管进（知识沉淀），飞书调用（平台能力），Ghost管看（统一展示）。数据全部通过 Gateway 路由到后端。

---

## 目录## 目录

1. [架构全景](#1-架构全景)
2. [项目整体状态速览](#2-项目整体状态速览)
3. [飞书机器人（总对话助理） -- 现状->目标->路径](#3-飞书机器人)
4. [豆包管道 -- 现状->目标->路径](#4-豆包管道)
5. [Ghost.html 官网 -- 现状->目标->路径](#5-ghosthtml-官网)
6. [Alpha-ID 身份层 -- 现状->目标->路径](#6-alpha-id-身份层)
7. [Gateway 网关 -- 现状->目标->路径](#7-gateway-网关)
8. [Nebula 工作流 -- 现状->目标->路径](#8-nebula-工作流)
9. [Flow/API 注册链路 -- 现状->目标->路径](#9-flowapi-注册链路)
10. [六层架构代码映射（完整版）](#10-六层架构代码映射完整版)
11. [架构审查 -- 做对的 vs 做错的](#11-架构审查)
12. [P0 任务清单（立即执行）](#12-p0-任务清单)
13. [P1 任务清单（本周执行）](#13-p1-任务清单)
14. [P2 任务清单（两周内）](#14-p2-任务清单)
15. [根目录清理计划](#15-根目录清理计划)
16. [已确认决策（不反复问）](#16-已确认决策)
17. [启动指南](#17-启动指南)
18. [参考文档 & 旧档说明](#18-参考文档)

---
## 1. 架构全景

> 图例：✅ 可用 | ⚠️ 半通 | ❌ 未实现 | 箭头 ↓ = 上层调用下层

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  🖥️  L1  用户交互层                                     ~5.6K 行               │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐  │
│  │ Ghost.html  3.5K     │  │ 飞书 WS长连接        │  │ 微信适配器  483L     │  │
│  │ ⚠️ 0次fetch 假数据   │  │ ⚠️ 只能地图导航      │  │ ⚠️ 代码有 未接入     │  │
│  └──────────────────────┘  └──────────────────────┘  └──────────────────────┘  │
│  ┌──────────────────────┐  ┌──────────────────────┐                           │
│  │ 豆包入口             │  │ MindFlow代理 1.8K    │                           │
│  │ ❌ 完全未接入         │  │ ⚠️ 路径未通          │                           │
│  └──────────────────────┘  └──────────────────────┘                           │
├────────────────────────────────┬────────────────────────────────────────────────┤
│  🆔  L2  身份管理层 — Alpha-ID │  ~8.2K 行 / 41文件                            │
│  ┌──────────────────────────┐  │  ┌──────────────────────────────────────────┐  │
│  │ DID核心 + 签名  ~2.1K    │  │  │ JWT认证  295L  ✅                         │  │
│  │ ✅ 完整可用              │  │  │ 采集器×9  ~1.2K  ⚠️                      │  │
│  └──────────────────────────┘  │  │ CLI×7    ~1.5K    ✅                     │  │
│  ┌──────────────────────────┐  │  │ 用户画像  ~800     ✅                     │  │
│  │ Agent网络  ~1.5K         │  │  │ Skill仓库 ~800     ⚠️                     │  │
│  │ ⚠️ 本地模拟 A2A          │  │  └──────────────────────────────────────────┘  │
│  └──────────────────────────┘  │                                               │
│  ┌──────────────────────────┐  │  ┌──────────────────────────────────────────┐  │
│  │ 支付宝人脸+短信          │  │  │ Agent SDK入口  ~500L  ✅                  │  │
│  │ ⚠️ 代码完整 未启动       │  │  └──────────────────────────────────────────┘  │
│  └──────────────────────────┘  │                                               │
├────────────────────────────────┴────────────────────────────────────────────────┤
│  🧠  L3  记忆知识库层                                   ~1.6K 行               │
│  ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────────────┐│
│  │ 双链记忆  413L  ✅  │ │ TwinBrain 685L  ✅  │ │ Coala记忆 507L  ⚠️         ││
│  │ 私链+知链 SQLite    │ │ 状态机+可见度+生命  │ │ 记忆防御  461L  ⚠️         ││
│  └─────────────────────┘ └─────────────────────┘ │ 双后端存储 601L  ✅         ││
│                                                  │ JSON + SQLite + Postgres    ││
│                                                  └─────────────────────────────┘│
│  ┌─────────────────────┐ ┌─────────────────────┐                               │
│  │ 知识整理引擎        │ │ Obsidian写入        │                               │
│  │ ❌ 未开发           │ │ ❌ 未开发           │                               │
│  └─────────────────────┘ └─────────────────────┘                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ⚙️  L4  Agent调度层                                    ~7.4K 行 / 32文件       │
│  ┌───────────────────────────────────┐  ┌─────────────────────────────────────┐  │
│  │       核心运行时                   │  │       横切能力                      │  │
│  │  AgentLoop 754L  ✅  主循环       │  │  风控引擎   358L  ✅                 │  │
│  │  MasterOrch   304L  ✅  调度中心  │  │  信誉系统   310L  ✅                 │  │
│  │  事件总线     261L  ✅  解耦      │  │  故障恢复   534L  ✅                 │  │
│  │  A2A协议     410L  ⚠️ 本地模拟   │  │  可观测性   553L  ✅                 │  │
│  │  多租户      281L  ✅  隔离+配额  │  │  基准测试   418L  ⚠️                 │  │
│  └───────────────────────────────────┘  └─────────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  ┌─────────────────────────────────────┐  │
│  │       行动引擎                     │  │       Skill体系                     │  │
│  │  approval + engine + adapters     │  │  skill_repository  ⚠️               │  │
│  │  ~1.1K  ✅   console+微信        │  │  skill_signer      ⚠️               │  │
│  └───────────────────────────────────┘  └─────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────────────┤
│  🚪  L5  网关管控层 — Gateway :18080                    638 行 / 5文件          │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │  /v1/identity  ✅   /v1/chat  ✅(限流)   /v1/brain/*  ✅   /v1/network  ✅ │   │
│  │  /v1/workflow  ✅   /v1/intent/parse  ✅(关键词)   /v1/register  ❌未启动  │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │  基础设施: CORS白名单 | Correlation ID | 滑动窗口限流 | 统一信封           │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────────────────┤
│  📡  L6  底层通信层                                                             │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │  AI Mesh libp2p  ❌ 未开发 — 先不碰                                       │   │
│  └──────────────────────────────────────────────────────────────────────────┐   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 数据流图

```
    [你]
     │
     ├──── 日常对话 ──→ 豆包 ──────────────────────────→ ❌ 未接入
     │
     ├──── 消息 ────→ 飞书 ──→ nebula工作流(地图) ──────→ ⚠️ 只走旧引擎
     │                         │
     │                         └── 应改走 ──→ ✅ Gateway :18080
     │
     ├──── 浏览器 ──→ Ghost.html ──(P0待加fetch)───────→ ⚠️ 假数据
     │
     └──── 微信 ──→ 微信适配器 ──(未接入)───────────────→ ⚠️ 代码有


                              ┌─────────────────────────────────────┐
                              │     Gateway :18080                   │
                              │     14路由 + 限流 + CORS             │
                              └───┬─────────────┬─────────────┬─────┘
                                  │             │             │
                    ┌─────────────┘             │             └─────────────┐
                    ▼                           ▼                           ▼
        ┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
        │  alphaid :8000    │     │  nebula :2002     │     │  flow/api :3001   │
        │  ~22K 行          │     │  ~6.1K 行         │     │  ~4.4K TS         │
        │                   │     │                   │     │                   │
        │  ✅ 身份(DID)     │     │  ✅ 工作流引擎    │     │  ❌ 未启动        │
        │  ✅ 双链记忆      │     │  ✅ 百度地图      │     │  注册:手机→短信   │
        │  ✅ TwinBrain     │     │  ✅ AI网关        │     │  →人脸→DID       │
        │  ✅ AgentLoop     │     │  ✅ 中间件×6     │     │  支付宝人脸       │
        │  ✅ 风控/恢复     │     │  ✅ 插件SDK      │     │  阿里云短信       │
        │  ⚠️ 多租户(已写)  │     │  ⚠️ 自动化       │     │                   │
        └───────────────────┘     └───────────────────┘     └───────────────────┘
```

### 1.3 六层概览

| 层 | 名称 | 代码量 | 核心组件 | 状态 |
|:--:|:-----|:------:|:---------|:----:|
| L6 | 底层通信层 | 0 | AI Mesh libp2p | ❌ 未开发 |
| L5 | 网关管控层 | 650L / 5文件 | Gateway :18080 14路由 + CORS + 限流 + 统一信封 | ✅ 注册路由已通 |
| L4 | Agent调度层 | ~7.4K / 32文件 | AgentLoop, Orchestrator, Tenant, Risk, Recovery, Observability, A2A | ⚠️ 基本完整 |
| L3 | 记忆知识库层 | ~1.6K | 双链记忆(统一SQLite), TwinBrain, Coala记忆, 记忆防御 | ⚠️ 缺知识引擎 |
| L2 | 身份管理层 | ~8.2K / 41文件 | DID, 签名, Agent网络, JWT, Profile, 挖矿采集, CLI | ✅ 最完整 |
| L1 | 用户交互层 | ~5.6K | Ghost.html, 飞书WS, 微信适配器, MindFlow代理, 官网 | ⚠️ 半通 |

### 1.4 三条对话路径

| 路径 | 入口 | 调用链路 | 工具数 | 能做什么 | 缺什么 |
|:----:|:-----|:---------|:------:|:---------|:-------|
| A | Ghost.html | TwinBrain → AgentLoop | 14 | 有记忆/身份/业务能力 | 0次fetch全是mock |
| B | 飞书 | feishu.py → _llm_decide_and_act | 3 | 只能地图导航 | 没接身份/记忆/AgentLoop |
| C | 豆包 | 无路径 | 0 | 无 | 完全没入口 |

### 1.5 完整组件清单（按模块分）

#### alphaid/projects/src/core/ — 7,403 行 / 32 文件

| 文件 | 行数 | 职责 | 状态 |
|:-----|:----:|:-----|:----:|
| agent.py | 754 | AgentLoop — 智能体主循环 | ✅ 可运行 |
| a2a.py | 410 | A2A 协议 — Agent间通信 | ⚠️ 本地模拟 |
| dual_chain.py | 413 | 双链记忆 — 私链+知链分离 | ✅ 可用 |
| twin_brain.py | 685 | TwinBrain — 状态机+可见度+生命周期 | ✅ 可用 |
| event_bus.py | 261 | 事件总线 — 模块间解耦 | ✅ 已写 |
| orchestrator.py | 304 | MasterOrchestrator — 中央调度+后台循环 | ✅ 已写 未接入 |
| tenant.py | 281 | 多租户引擎 — 数据隔离+配额 | ✅ 已写 |
| storage_factory.py | 65 | 存储工厂 — 自动选择 Postgres/JSON | ✅ 可用 |
| memory_store.py | 413 | 记忆存储 — CRUD+搜索 | ✅ 可用 |
| risk_engine.py | 358 | 风控引擎 — 风险评估规则 | ✅ 已写 |
| reputation.py | 310 | 信誉系统 — 信誉分管理 | ✅ 已写 |
| observability.py | 553 | 可观测性 — 日志/指标/追踪 | ✅ 已写 |
| recovery.py | 534 | 故障恢复 — 重试/降级/熔断 | ✅ 已写 |
| coala_memory.py | 507 | Coala记忆 — 语义记忆层 | ⚠️ 已写 |
| memory_poisoning_defense.py | 461 | 记忆防御 — 防投毒过滤 | ⚠️ 已写 |
| user_identity.py | 283 | 用户身份 — 注册/登录/设备绑定 | ✅ 可用 |
| interfaces.py | 90 | 接口定义 — 抽象协议 | ✅ |
| message.py | 93 | 消息模型 — 统一消息结构 | ✅ |
| benchmark_adapter.py | 418 | 基准测试适配器 | ⚠️ 已写 |
| storage.py / storage_sqlite.py / storage_postgres.py | 601 | 存储后端 — JSON+SQLite+Postgres | ✅ 三后端 |
| action_engine/ (7文件) | ~1,128 | 行动引擎 — approval+engine+adapters | ✅ 已写 |

#### alphaid/projects/src/alpha_id/ — 8,164 行 / 41 文件

| 文件 | 行数 | 职责 | 状态 |
|:-----|:----:|:-----|:----:|
| did.py | ~1,200 | DID 生成/解析/验证 | ✅ 完整 |
| signer.py | ~900 | 数字签名 ed25519 | ✅ 完整 |
| agent_network.py | ~1,500 | Agent网络 — 社交+PoE+Skill | ⚠️ 本地模拟 |
| web.py | ~600 | FastAPI Web 应用 — 13条路由 | ⚠️ Demo数据 |
| poe.py | ~400 | PoE — 证明存在协议 | ⚠️ |
| profile_schema.py / profile_wizard.py | ~800 | 用户画像 — Schema+引导 | ✅ 可用 |
| skill_repository.py | ~500 | Skill仓库 — 存储+检索 | ⚠️ 已写 |
| skill_signer.py | ~300 | Skill签名 — 安全校验 | ⚠️ 已写 |
| collectors/ (9文件) | ~1,200 | 采集器 — Browser/ChatGPT/Claude/Cursor/Git/Trae/Local | ⚠️ 部分可用 |
| mining/ (3文件) | ~400 | 挖矿 — 扫描+提取+推断 | ⚠️ |
| identity_cli.py / network_cli.py / brain_cli.py / social_cli.py / repo_cli.py / scaffold_cli.py / suggest_cli.py | ~1,500 | 各类 CLI 工具 | ✅ 可用 |

#### alphaid/projects/src/auth/ + entrypoints/ + api/ + tools/ + mindflow/ + feishu_bot/

| 模块 | 文件数 | 行数 | 职责 | 状态 |
|:-----|:------:|:----:|:-----|:----:|
| auth/ | 4 | 295 | JWT + 中间件 + Token存储 | ✅ 已写 |
| entrypoints/api.py + daemon.py + aid_mcp_server.py + shortdrama_service.py | 5 | 2,229 | 入口 — API/守护进程/MCP/短剧 | ⚠️ daemon待删 |
| api/ (REST路由) | 7 | 540 | 路由 — identity/risk/shortdrama/social | ⚠️ |
| tools/ | 8 | 1,698 | 工具 — OCR/截屏/安全/窗口/身份 | ⚠️ 已写 |
| mindflow/ | 12 | 1,822 | 工作流 — engine/intent/onboarding/agents | ⚠️ 路径未通 |
| feishu_bot/ | 2 | 304 | 飞书 — bot.py (重复) | ⚠️ 待删 |
| templates/ghost.html | 1 | 3,507 | Ghost.html 官网前端 | ⚠️ 0次fetch |

#### nebula/src/mindflow_map/ — 6,108 行 / 64 文件

| 子模块 | 文件数 | 行数 | 职责 | 状态 |
|:------|:------:|:----:|:-----|:----:|
| api/ (12文件) | 12 | ~1,800 | 路由 — feishu/webhook/map/workflow/automation/health/streaming/shortdramas/wechat/events/approvals/openapi | ⚠️ feishu绑旧引擎 |
| ai/ (5文件) | 5 | ~600 | AI网关 — intent/llm/circuit_breaker/fallback/health | ✅ 已写 |
| core/ (5文件) | 5 | ~700 | 核心 — engine_registry/events/metrics/auth/cache | ✅ 已写 |
| identity/ | 1 | 200 | AlphaIDClient — 重试+并发+缓存 | ✅ 已写 |
| middleware/ (6文件) | 6 | ~800 | 中间件 — rate_limit/auth/audit/prometheus/correlation_id/error_handler | ✅ 已写 |
| models/ (5文件) | 5 | ~500 | 数据模型 — database/session/auth/audit/approval | ✅ 已写 |
| plugins/ (2文件) | 2 | ~200 | 插件SDK — registry+@tool装饰器 | ✅ 已写 |
| schemas/ (5文件) | 5 | ~400 | Schema — map/audit/approval/events/auth | ✅ 已写 |
| tools/ (baidu_map.py) | 1 | ~200 | 百度地图 — 搜索+路线 | ✅ 可用 |
| workflows/engine.py | 1 | ~300 | 工作流引擎 — Tool基类+MapNav | ⚠️ 仅地图 |
| automation/ (3文件) | 3 | ~400 | 自动化 — 抖音/Shopify/脚本生成 | ⚠️ |

#### ghost-main/gateway/ — 638 行 / 5 文件

| 文件 | 行数 | 职责 | 状态 |
|:-----|:----:|:-----|:----:|
| app.py | ~400 | FastAPI 网关 — 14路由+CORS+限流+统一信封 | ✅ 结构好 |
| tests/ (4文件) | ~238 | 测试 — health/rate_limit | ✅ |
## 项目全景版图（六大板块 + 三条主线）

### 六大板块现状

#### 板块1: Alpha-ID身份体系
- DID核心: did.py 9813L + signer.py 7577L 完整可用（生成/签名/验证）
- AgentLoop: agent.py 7567L 14工具完整可运行
- 双脑: twin_brain.py 24K 记忆+推理分离
- 双链记忆: dual_chain.py 15K SQLite私链+知链分离
- 事件总线: event_bus.py 7.9K 已实现
- A2A协议: a2a.py 13K W 本地模拟（非真实网络）
- Agent网络: agent_network.py 13K W 本地模拟
- 支付宝人脸+短信: 代码完整但flow未启动已修复（P0-2已在:3001运行）
- 文件分布: alpha_id/ 8164L/41文件 + core/ 多个模块
- 状态: V 核心完整，A2A和Agent网络待升级

#### 板块2: Gateway网关
- 文件: ghost-main/gateway/app.py 638L/5文件
- 路由: 14条已配（10通/4不通）
- 已通: identity/chat/memory/workflow/health/brain/network/register(部分已通)
- 不通: /v1/intent/parse（框架有但未完整实现）/ 内容审核/限流（未实现）
- flow/api注册路由6条已于2026-07-26迁移至alphaid :8000，Gateway代理已更新。Flow/API不再承载注册职责。
- 状态: V 基本骨架完整，LLM分流和审核限流待补

#### 板块3: 飞书总对话助理
- 文件: nebula/mindflow_map/api/feishu.py 234L WS长连接（心跳已修复）
- 当前路径（P0-4修复后）: 飞书消息 -> feishu.py -> httpx POST Gateway /v1/chat -> alphaid TwinBrain+AgentLoop
- 原路径（P0前）: feishu.py -> workflows/engine.execute() -> 只配了MapNavigationTool+IntentParser -> 只有3工具 -> 匹配不到=报错
- 已清理: alphaid/feishu_bot/整目录删了（重复代码）+ callback_server.py（旧引擎）
- 现在能: 身份查询/记忆查询/地图导航/通用对话
- 待修: feishu.py L22-23硬编码凭证移入环境变量（P1）
- 状态: V 已通Gateway，能调全平台能力

#### 板块4: Ghost展示层
- 文件: alphaid/templates/ghost.html 2515L（已删除重复 Mindflow 面板）
- UI: TailwindCSS编译 两视图架构（A2A 生态区 + Mindflow 协作台）
- 已加: fetchDashboard()调Gateway /v1/dashboard + sendChatMessage()调/v1/chat + 注册UI调Gateway→alphaid
- 当前: 注册流程（SMS→人脸→DID）已通过Gateway→alphaid打通，浏览器可操作完整注册

#### 板块5: 豆包知识沉淀（整块新建）
- 现状: 完全未接入。豆包内容和Ghost系统隔离
- 方案（用户确认）: 豆包自身LLM做拆分/分类/摘要/链接 -> 直接输出结构化知识卡片 -> Obsidian
- 明确不做: 不在中间写知识整理引擎，豆包就是引擎
- 待调研: 豆包导出/API接入方案（P1）
- 状态: X 未开发

#### 板块6: Obsidian知识库（整块新建）
- 现状: 不存在
- 方案: 接收豆包输出的结构化知识 -> 生成MD文件 -> 按主题分类 -> 带标签/链接/时间戳
- 查询: Ghost.html和飞书可搜索查询（P2）
- 状态: X 不存在

### 三条使用主线

主线A（知识进）: 豆包聊天 -> 豆包自身LLM做拆分/分类/摘要 -> Obsidian卡片
主线B（能力用）: 对话飞书 -> feishu.py -> Gateway :18080 -> alphaid/nebula/flow
主线C（统一看）: 打开Ghost.html -> fetchDashboard/sendChatMessage -> Gateway -> 后端

### 已解决的方向错误

| 错误 | 之前怎么写的 | 纠正为 | 来源 |
|:-----|:------------|:-------|:-----|
| 飞书定位 | 工作指令入口 | 自然语言总对话助理，跟大平台对接 | 用户纠正 |
| 豆包定位 | 次要入口，先打通飞书 | 主入口，知识沉淀核心 | 用户纠正 |
| 知识整理方式 | 写一个知识整理引擎 | 豆包自身LLM做整理，不做引擎层 | 用户纠正 |
| 三个入口关系 | 分散描述无衔接 | 豆包管进/飞书调用/Ghost管看 | 本文档 |
| 文档记录方式 | 泛化的V基本完整 | 具体的文件行数/路径/代码状态 | 用户纠正 |

### 现在不要碰的

| 模块 | 原因 |
|:-----|:------|
| L6 AI Mesh libp2p | MVP跑通前不碰 |
| Skill自进化 | 概念阶段 |
| A2A真实网络通信 | 本地模拟够用 |
| 商业生态/技能市场/分账 | 一个人维护太重 |
| 多租户隔离 | 单用户先跑通 |
| 电商/短视频/出行独立模块 | 通过AgentLoop工具调用即可 |
## 2. 项目整体状态速览

### 2.1 当前在跑的3个服务

| 服务 | 端口 | 状态 | 行数 | 本质 |
|:-----|:----:|:----:|:----:|:------|
| alphaid | 8000 | Demo模式 | ~22K Python + 3.5K HTML | 身份+记忆+双脑+AgentLoop+采集+CLI 全栈核心 |
| nebula | 2002 | 运行中 | ~6.1K Python / 64文件 | 工作流引擎+飞书WS+AI网关+中间件+插件SDK |
| gateway | 18080 | 运行中 | 638 Python / 5文件 | 统一网关 14路由+CORS+限流+统一信封 |

### 2.2 写完了但没启动的

| 服务 | 端口 | 行数 | 说明 |
|:-----|:----:|:----:|:------|
| flow/api | 3001 | ~4.4K TS | AI 路由/Computer Use（注册已迁至alphaid :8000） |

### 2.3 核心问题一句话

代码很多（~32K行）但关键路径断了 -- 飞书只认地图、Ghost是假官网、豆包进不来、注册链路没启动、大量已写能力（Orchestrator/多租户/风控/恢复）未被任何入口调用。需要的是打通而不是加功能。

---
## 3. 飞书机器人（总对话助理） -- 现状->目标->路径

### 3.1 现状（P0修复后）

P0-4 已修复：飞书不再走旧 workflow 引擎，改为调 Gateway /v1/chat。

| 能力 | 状态 | 说明 |
|:-----|:----:|:------|
| 接收飞书消息（WS长连接） | V 正常 | nebula/feishu.py 心跳已修复 |
| 地图导航（搜索/导航/保存） | V 正常 | 通过Gateway调nebula |
| 身份查询（我是谁） | V 已通 | 通过Gateway /v1/chat -> alphaid |
| 记忆查询（上次项目计划） | V 已通 | 通过Gateway /v1/chat -> TwinBrain |
| 通用对话 | V 已通 | Gateway /v1/chat -> TwinBrain+AgentLoop |
| 凭证硬编码 | W 待移入环境变量 | P1任务 |

**当前代码路径：**
飞书消息 -> nebula/api/feishu.py (234行 WS长连接)
         -> httpx POST Gateway :18080 /v1/chat
         -> Gateway -> alphaid TwinBrain + AgentLoop
         -> 返回结果 -> 飞书

**已清理：**
- alphaid/feishu_bot/ 目录已删（P0-1）
- callback_server.py 旧引擎路径已删
- 凭证移入环境变量（待P1）

### 3.2 衔接关系

飞书在整个系统中的位置：

```
你对话飞书
  -> feishu.py (WS长连接)
    -> Gateway :18080 /v1/chat
      -> alphaid :8000 (身份/记忆/AgentLoop/注册)
      -> nebula :2002 (工作流/地图)
      -> flow/api :3001 (注册链路)
    <- 返回结果
  <- 飞书回复你
```

飞书是你的总对话助理，通过Gateway跟整个平台对接。你想做什么（查身份、查记忆、地图导航、执行业务、通用聊天）直接对话就行。

### 3.3 目标形态

飞书能做的事：身份查询、记忆读写、地图导航、业务工具、通用对话、知识查询（Obsidian，P2）

| 步骤 | 做什么 | 优先级 |
|:-----|:-------|:------:|
| 1 | Gateway加 /v1/intent/parse | P0 DONE |
| 2 | feishu.py改调Gateway不走workflow | P0 DONE |
| 3 | 删alphaid/feishu_bot/ | P0 DONE |
| 4 | feishu.py凭证移入环境变量 | P1 |
| 5 | 加记忆查询工具 | P1 |
| 6 | 加身份查询工具 | P1 |

## 4. 豆包管道 -- 现状->目标->路径

### 4.1 现状
**完全没有接入。** 豆包内容和Ghost项目完全隔离。

### 4.2 需求确认
1. 豆包是主要输入源 -- 日常很多对话输出
2. 不要手动导入 -- 要自动同步
3. 豆包自己会整理 -- LLM把零散对话拆成知识
4. 沉淀到Obsidian -- 可浏览可搜索的知识卡片
5. 飞书/Ghost可查询

### 4.3 目标形态
豆包对话 -> 知识整理引擎(P1开发)
         (LLM拆分/分类/交叉链接/去重/摘要)
         -> Obsidian知识库(MD文件+标签+链接)
         -> Ghost/飞书查询接口

### 4.4 中间步骤
| 步骤 | 做什么 | 优先级 |
|:
### 4.5 衔接关系

豆包在整个系统中是**知识入口**。你跟豆包聊天的内容，由豆包自身LLM整理后写入Obsidian。沉淀的知识可以被飞书和Ghost.html查询调用。

豆包 -> (自身整理) -> Obsidian知识库 -> 飞书/Ghost查询

-----|:-------|:------:|
| 1 | 调研豆包导出方案 | P1 |
| 2 | 豆包直连Obsidian方案（豆包自己整理） | P1 |
| 3 | Obsidian写入 | P1 |
| 4 | Ghost加知识搜索 | P2 |
| 5 | 飞书加知识查询 | P2 |

注意：豆包不是P0先打通飞书和注册链路再搞。

---
## 5. Ghost.html 官网 -- 现状->目标->路径

### 5.1 现状
路径: D:\MW\alphaid\projects\src\alpha_id\templates\ghost.html

| 指标 | 值 |
|:-----|:---:|
| 行数 | 2515行 |
| UI | TailwindCSS编译 两视图架构（A2A 生态区 + Mindflow 协作台） |
| 真实API调用 | 注册/健康检查/记忆统计 接通 |
| 注册/登录 | ✅ DID + 短信 + 人脸 + 落库 |
| 对话 | 界面有 + ChatGPT 记忆导入 |

注册链路已端到端跑通，工作台统计数据从 Gateway 实时拉取。

> 注：已删除重复的 4 个 Mindflow 面板，workbenchView 聚焦 A2A 生态，mindflowView 为唯一人机协作台。

### 5.2 目标形态
Ghost.html -> 仪表盘(从Gateway拉真实数据)
           -> 注册/登录(手机号->短信->人脸->DID)
           -> 聊天面板(POST /v1/chat + SSE流式)
           -> 知识浏览(P2)

### 5.3 中间步骤
| 步骤 | 做什么 | 优先级 |
|:
### 5.4 衔接关系

Ghost.html是**Web展示层**，不是主入口。它通过Gateway调后端接口。页面已加入fetchDashboard()和sendChatMessage()，启动后可看到真实数据。

Ghost.html -> Gateway :18080 -> alphaid :8000 / flow/api :3001

-----|:-------|:------:|
| 1 | 加fetchDashboard调Gateway | P0 |
| 2 | 加注册页面 | P0 |
| 3 | 加聊天面板 | P0 |
| 4 | 统一命名去掉Web4.0 | P1 |

---
## 6. Alpha-ID 身份层 -- 现状->目标->路径

### 6.1 现状
这是项目中最完整的部分。分两个大目录：

**alpha_id/** (8,164行/41文件) — 身份+社交+采集+CLI

| 模块 | 文件 | 行数 | 状态 |
|:-----|:-----|:----:|:----:|
| DID生成/签名/验证 | did.py + signer.py | ~2,100 | ✅ 完整 |
| Agent网络 A2A | agent_network.py | ~1,500 | ⚠️ 本地模拟 |
| Web入口 FastAPI | web.py | ~600 | ⚠️ Demo数据 |
| PoE存在证明 | poe.py | ~400 | ⚠️ |
| 用户画像 | profile_schema.py + profile_wizard.py | ~800 | ✅ |
| Skill仓库/签名 | skill_repository.py + skill_signer.py | ~800 | ⚠️ |
| 采集器 (9个子采集) | collectors/ | ~1,200 | ⚠️ 部分可用 |
| 挖矿 | mining/ (扫描+提取+推断) | ~400 | ⚠️ |
| CLI工具 (7个) | identity/network/brain/social/repo/scaffold/suggest | ~1,500 | ✅ 可用 |

**core/** (7,403行/32文件) — 核心引擎层（见§1.5完整表）

**入口混乱问题：** 4个入口（api.py / daemon.py / aid_mcp_server.py / shortdrama_service.py）+ alphaid/feishu_bot 重复

### 6.2 目标
核心层保持干净(身份+记忆+AgentLoop+事件总线) 删冗余 只留api.py + aid_mcp_server.py

### 6.3 中间步骤
| 步骤 | 做什么 | 优先级 |
|:
### 6.4 衔接关系

Alpha-ID是**身份根基**，所有入口（豆包/飞书/Ghost）最终都要通过它。飞书通过Gateway查身份，Ghost通过Gateway注册身份。注册链路的短信验证和人脸识别已由alphaid（Python）接管，不再依赖flow/api。

飞书/Ghost -> Gateway -> alphaid DID (身份查询/注册)

-----|:-------|:------:|
| 1 | 删短剧 shortdrama_service.py | P0 |
| 2 | 删桌面精灵 daemon.py | P0 |
| 3 | 删 alphaid/feishu_bot/ (与 nebula 重复) | P0 |
| 4 | 清理 main.py入口 | P0 |
| 5 | 统一入口只留 api.py + aid_mcp_server.py | P0 |

---
## 7. Gateway 网关 -- 现状->目标->路径

路径: `D:\MW\ghost-main\gateway\app.py`
行数: ~400 (总638含测试) 路由数: 14条

当前路由:
| 路由 | 后端 | 状态 |
|:-----|:-----|:----:|
| GET /health | 本地 三后端健康检查 | ✅ |
| GET /v1/identity | alphaid :8000 | ✅ |
| GET /v1/profile | alphaid :8000 | ✅ |
| GET /v1/brain/status + POST /v1/brain/awake | alphaid :8000 | ✅ |
| GET /v1/network/topology | alphaid :8000 | ✅ |
| POST /v1/chat (限流10/60s) | alphaid :8000 | ✅ |
| POST /v1/intent/parse (关键词分流) | alphaid :8000 | ✅ 已实现 |
| GET /v1/workflows + POST /v1/workflows/execute | nebula :2002 | ✅ |
| /v1/register/* | alphaid :8000（原 flow/api :3001） | ✅ 已迁移并打通 |

基础设施: CORS白名单 / Correlation ID / 滑动窗口限流(5/60s) / 统一信封 {success,data,ts,request_id}

目标: 全部14条路由可用 + LLM智能分流(现仅关键词) + 内容审核

---
## 8. Nebula 工作流 -- 现状->目标->路径

路径: `D:\MW\nebula\src\mindflow_map\` 64文件 / 6,108行
入口: `mindflow_map/main.py`
核心: 工作流引擎 + AI网关(intent/llm/circuit_breaker) + 中间件(rate_limit/auth/audit/prometheus) + 插件SDK(@tool装饰器) + 自动化(抖音/Shopify)
飞书绑在上面 未来应走Gateway
目标: 飞书走Gateway Nebula退回纯工作流引擎

| 步骤 | 做什么 | 优先级 |
|:-----|:-------|:------:|
| 1 | feishu.py改调Gateway | P0 |
| 2 | 修正ci.yml | P1 |

---
## 9. Flow/API 注册链路 -- 现状->目标->路径

路径: D:\MW\flow\apps\api\ TS+Fastify ~4.4K行
注册路由完整(手机号->短信->人脸->DID)
支付宝人脸代码已写 短信验证有真实阿里云Key
.env有真实配置 但从未启动过

目标: npm install -> 启动 -> 接入Gateway

| 步骤 | 做什么 | 优先级 |
|:-----|:-------|:------:|
| 1 | npm install | P0 |
| 2 | npx tsx src/index.ts | P0 |
| 3 | 验证:3001/api/health | P0 |

---
## 10. 六层架构代码映射（完整版）

> 详细到文件级别的映射见 §1.5 完整组件清单。本节为精简速查版。

### L1 用户交互层 (~5,600行)
| 文件 | 真实路径 | 行数 | 状态 |
|:-----|:---------|:----:|:----:|
| Ghost.html | `alphaid/projects/src/templates/ghost.html` | 3,507 | ⚠️ 0次fetch |
| 飞书机器人 | `nebula/src/mindflow_map/api/feishu.py` | ~200 | ⚠️ 只能地图 |
| 飞书Webhook | `nebula/src/mindflow_map/api/feishu_webhook.py` | ~150 | ⚠️ 备选 |
| 微信适配器 | `alphaid/projects/src/core/action_engine/adapters/wechat.py` | 483 | ⚠️ 已写未接 |
| MindFlow代理 | `nebula/src/mindflow_map/api/` | ~1,800 | ⚠️ 路径未通 |

### L2 身份管理层 (~8,200行)
| 文件 | 真实路径 | 行数 | 状态 |
|:-----|:---------|:----:|:----:|
| DID核心 | `alphaid/projects/src/alpha_id/did.py` | ~1,200 | ✅ 完整 |
| 签名器 | `alphaid/projects/src/alpha_id/signer.py` | ~900 | ✅ 完整 |
| Agent SDK | `alphaid/projects/src/alpha_id/agent.py` | ~500 | ✅ SDK入口 |
| Agent网络 | `alphaid/projects/src/alpha_id/agent_network.py` | ~1,500 | ⚠️ 本地模拟 |
| JWT认证 | `alphaid/projects/src/auth/` | 295 | ✅ 已写 |
| 采集器(9个) | `alphaid/projects/src/alpha_id/collectors/` | ~1,200 | ⚠️ 部分可用 |
| CLI(7个) | `alphaid/projects/src/alpha_id/*_cli.py` | ~1,500 | ✅ 可用 |
| 注册路由TS | `flow/apps/api/src/routes/register.ts` | 311 | ❌ 未启动 |

### L3 记忆知识库层 (~1,600行)
| 文件 | 真实路径 | 行数 | 状态 |
|:-----|:---------|:----:|:----:|
| 双链记忆 | `alphaid/projects/src/core/dual_chain.py` | 413 | ✅ SQLite私链+知链 |
| 双脑 | `alphaid/projects/src/core/twin_brain.py` | 685 | ✅ 状态机+可见度 |
| Coala记忆 | `alphaid/projects/src/core/coala_memory.py` | 507 | ⚠️ 已写 |
| 记忆防御 | `alphaid/projects/src/core/memory_poisoning_defense.py` | 461 | ⚠️ 已写 |
| 存储双后端 | `alphaid/projects/src/core/storage*.py` | 601 | ✅ JSON+SQLite+Postgres |

### L4 Agent调度层 (~7,400行)
| 文件 | 真实路径 | 行数 | 状态 |
|:-----|:---------|:----:|:----:|
| AgentLoop | `alphaid/projects/src/core/agent.py` | 754 | ✅ 可运行 |
| 事件总线 | `alphaid/projects/src/core/event_bus.py` | 261 | ✅ 已写 |
| A2A协议 | `alphaid/projects/src/core/a2a.py` | 410 | ⚠️ 本地模拟 |
| MasterOrchestrator | `alphaid/projects/src/core/orchestrator.py` | 304 | ✅ 已写未接 |
| 多租户 | `alphaid/projects/src/core/tenant.py` | 281 | ✅ 已写 |
| 风控引擎 | `alphaid/projects/src/core/risk_engine.py` | 358 | ✅ 已写 |
| 信誉系统 | `alphaid/projects/src/core/reputation.py` | 310 | ✅ 已写 |
| 故障恢复 | `alphaid/projects/src/core/recovery.py` | 534 | ✅ 已写 |
| 可观测性 | `alphaid/projects/src/core/observability.py` | 553 | ✅ 已写 |
| 行动引擎 | `alphaid/projects/src/core/action_engine/` | ~1,128 | ✅ 已写 |

### L5 网关管控层 (638行)
| 文件 | 真实路径 | 行数 | 状态 |
|:-----|:---------|:----:|:----:|
| Gateway | `ghost-main/gateway/app.py` | ~400 | ✅ 14路由+限流+信封 |
| 测试 | `ghost-main/gateway/tests/` | ~238 | ✅ |

### L6 底层通信层 (0行)
| 模块 | 路径 | 状态 |
|:-----|:-----|:----:|
| AI Mesh libp2p | 未开发 | ❌ 先不碰 |

---
## 11. 架构审查 -- 做对的 vs 做错的

### 11.1 做对了的
| # | 决策 | 为什么对 |
|---|------|---------|
| 1 | Alpha-ID身份根 did.py+signer.py | 所有数据归一个身份是基石 |
| 2 | Gateway统一入口 14路由 | 架构清晰，限流+CORS+统一信封 |
| 3 | 双链记忆私链+知链分离 | 隐私不出本地 |
| 4 | 3个独立服务(alphaid/nebula/gateway) | 模块解耦 |
| 5 | 支付宝人脸+短信验证 | 国内合规 |
| 6 | AgentLoop+MasterOrchestrator+TwinBrain | 核心智能体能力完整 |
| 7 | 存储双后端(JSON+Postgres) | 开发生产无缝切换 |
| 8 | 多租户引擎(tenant.py) | 为多用户做准备 |
| 9 | 故障恢复(recovery.py)+可观测性(observability.py) | 生产级稳定性 |
| 10 | 行动引擎(action_engine) | approval+adapter模式解耦 |

### 11.2 做错了的(必须改)
| # | 错误 | 表现 | 正确做法 |
|---|------|------|---------|
| 1 | 飞书走错路 | feishu.py→workflows/engine只地图 | 飞书→Gateway→LLM分流 |
| 2 | alphaid入口混乱 | 4入口(api/daemon/mcp/shortdrama)+feishu_bot重复 | 只留api.py+aid_mcp_server.py |
| 3 | Ghost假官网 | 3507行0次fetch | 加fetch调Gateway |
| 4 | 豆包无入口 | 核心输入进不了Ghost | 豆包→知识引擎→Obsidian |
| 5 | 飞书两套重复代码 | nebula/feishu+alphaid/feishu_bot | 只保留nebula |
| 6 | flow/api从未启动 | 注册链路代码完整但6条路由不通 | npm install→启动 |
| 7 | 微信适配器写了没接 | wechat.py 483L在action_engine里 | 接入Gateway或删除 |

### 11.3 冗余待删
| 项 | 位置 | 大小 | 原因 |
|:---|:-----|:----:|:-----|
| 短剧服务 | entrypoints/shortdrama_service.py | ~800L | 无关 |
| 桌面精灵 | entrypoints/daemon.py | ~700L | 空壳 |
| feishu_bot重复 | feishu_bot/ | 304L | nebula已有 |
| flow双链记忆TS版 | flow/.../dual-chain.ts | ~5K | 有Python版 |
| flow旧路由 | workflow.ts+map.ts | ~3K | 不再用 |

---
## 12. P0 任务清单(立即执行)

### P0-1 删冗余代码
删除: shortdrama_service.py + daemon.py + alphaid/feishu_bot/ + flow重复模块(dual-chain.ts/workflow.ts/map.ts)
然后在main.py删掉shortdrama_router import 重启alphaid

### P0-2 启动flow/api注册链路
cd D:\MW\flow\apps\api && npm install && npx tsx src/index.ts
验证 http://localhost:3001/api/health

### P0-3 Ghost.html加真实API
加fetchDashboard调GET /v1/dashboard
加注册页面UI(手机号->短信->人脸->DID)
加聊天面板(输入->POST /v1/chat->SSE流式)

### P0-4 飞书改走Gateway+LLM分流
Gateway加/v1/intent/parse路由
feishu.py改调Gateway
删alphaid/feishu_bot/

---
## 13. P1 任务清单(本周)
| # | 任务 | 工作量 |
|---|------|:------:|
| 1 | 飞书凭证移入环境变量 | 0.5h |
| 2 | FOUNDER身份移入环境变量 | 0.5h |
| 3 | 修正CI路径 | 0.5h |
| 4 | 调研豆包直连Obsidian方案（豆包自身做知识整理） | 3h |
| 5 | 豆包知识自动同步到Obsidian | 4h |
| 6 | Obsidian知识卡片查询接口 | 3h |
| 7 | alphaid目录重构 | 2h |

---
## 14. P2 任务清单(两周内)
| # | 任务 | 说明 |
|---|------|------|
| 1 | Ghost知识搜索 | 搜索浏览卡片 |
| 2 | 飞书知识查询 | 查记忆/卡片 |
| 3 | 内容审核中间件 | Gateway做 |
| 4 | 限流中间件 | Token Bucket |
| 5 | 监控Trace | 链路追踪 |
| 6 | 多租户隔离 | 多用户准备 |
| 7 | A2A真实通信 | HTTP/WS升级 |

---
## 15. 根目录清理计划
| 文件 | 处理 |
|:-----|:-----|
| GHOST.md | 保留 |
| ARCHITECTURE_DIAGRAM.md | 已整合进GHOST.md 删除 |
| ARCHITECTURE_REVIEW.md | 同上 删除 |
| FRAMEWORK.md | 同上 删除 |
| TRUTH.md | 同上 删除 |
| README.md | 保留 |
| archive/md_old/ | 保留不动 |

---
## 16. 已确认决策（项目宪法）

以下决策是项目基石，后续所有开发必须遵循，不反复确认：

| 决策 | 来源 | 影响 |
|:-----|:------|:-----|
| 唯一官网 = Ghost.html（不是其他任何页面） | 用户明确 | 所有用户界面统一走Ghost |
| 豆包 = 知识输入主入口 + 自己就是整理引擎 | 用户明确 | 不做中间层，豆包直连Obsidian |
| 飞书 = 工作指令辅助入口 | 用户明确 | 指令走Gateway查身份/记忆/业务 |
| 不用微信、不用Claude Code | 用户明确 | 删除相关代码 |
| 飞书不走工作流引擎，走Gateway+LLM分流 | 默认同意 | feishu.py已改 |
| 文档只留GHOST.md + archive/md_old/ | 已执行 | 根目录只保留3项 |
| 已删：短剧/daemon/微信/feishu_bot/DS/flow重复 | P0已执行 | 13项冗余已清理 |
| 对话中没反驳的 = 默认同意 | 用户明确 | 不需要反复确认 |
| 不要做的：AI Mesh libp2p / Skill自进化 / A2A真实网络通信 | 架构审查 | L6和部分L4功能先不碰 |## 17. 启动指南

``已清理。``

验证: :8000 → Ghost.html | :18080/health → 网关状态 | 飞书发消息 → 只能地图(P0前)

---
## 18. 参考文档&旧档说明
旧文档在archive/md_old/保留不动: ARCHITECTURE.md ECOSYSTEM_ARCHITECTURE.md ROOT_AUDIT.md PLATFORM_VISION.md PROJECT_AUDIT.md AID_FULL_INTEGRATION.md 繁星计划申请材料.md

根目录只保留: GHOST.md + README.md + archive/

---
## 变更记录
| 日期 | 版本 | 变更 |
|:-----|:----|:------|
| 2026-07-25 | 3.0 | 全面审计:修正全部行数/路径/状态标记 新增§1.5完整组件清单 修复Mermaid→ASCII框图 统一✅⚠️❌ |
| 2026-07-25 | 2.0 | 完整重写:整合5份旧文档+全部审计+今日决策 每组件写现状→目标→路径 |
| 2026-07-25 | 1.0 | 初始整合版 |
### 7.4 衔接关系

Gateway是**统一入口**，所有外部请求（飞书/Ghost）都经过它路由到后端服务。飞书调/v1/chat，Ghost调/v1/dashboard和/v1/chat，注册流程调/v1/register/*。

飞书 -> Gateway -> alphaid/nebula/flow
Ghost -> Gateway -> alphaid/flow


### 8.3 衔接关系

Nebula是**工作流引擎**，负责飞书WS长连接和地图导航等业务。它通过Gateway与alphaid对接，不直接调用后端。

飞书 -> feishu.py -> Gateway -> nebula（工作流/地图）


### 9.4 衔接关系

Flow/API提供**注册链路**（短信->人脸->DID），是Alpha-ID身份注册的后端服务。Gateway的/v1/register/*路由代理到它。已在:3001运行。

Ghost注册页 -> Gateway /v1/register/* -> flow/api :3001


