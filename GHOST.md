# Ghost 项目 -- 完整框架与现状实录

> **版本 4.0** | **2026-07-27**
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

```
                    [你]
                      |
         +------------+-------------+-------------+
         |            |              |             |
      [豆包]        [飞书]       [Ghost.html]   [NURO]
     日常聊天      总对话助理      Web展示       桌面精灵
     知识输出      & 平台对接     注册/聊天      本地AI
         |            |              |             |
         v            v              v             v
  +-----------+/+-----------+\  +----------+  +---------+
  | Obsidian  ||  整个平台   |  | 仪表盘   |  | 本地Ollama
  | 知识沉淀   || 身份/记忆  |  | 注册/聊天|  | 双链记忆
  |           || 业务/查询  |  | 知识浏览 |  | MCP工具  |
  +-----------+| 调用任何能力|  +----------+  +---------+
               +-------------+
                     |
          +----------+----------+
          |          |          |
          v          v          v
      [alphaid]  [nebula]   [flow/api]
      身份/记忆   工作流     注册链路
      AgentLoop  飞书对接
```

### 每个入口做什么

| 入口 | 本质 | 你的使用方式 |
|:----:|:-----|:------------|
| **豆包** | 知识输入 | 日常聊天 -> LevelDB自动扫描 -> 精炼 -> Obsidian知识卡片 |
| **飞书** | 总对话助理 | 自然语言对话 -> Gateway -> 调整个平台能力（身份/记忆/业务/聊天/查询） |
| **Ghost.html** | Web展示 | 浏览器打开看仪表盘、注册Alpha-ID、对话聊天、浏览知识库 |
| **NURO** | 桌面精灵 | Windows悬浮精灵，本地AI贾维斯，语音/视觉/观察/每日总结 |

### 关键理解

**飞书不只是工作指令。** 它是你的总助理，你平时想查什么、想做什么、想去哪里，直接跟飞书机器人说就行。它背后对接的是整个 Ghost 平台——身份、记忆、业务、工具，全部通过对话调用。

**豆包不只是聊天。** 它是你的知识入口。你跟豆包聊过的内容通过LevelDB自动扫描捕获，精炼后写入Obsidian，变成可查询的知识卡片。

**Ghost.html 不是主入口。** 它是 Web 展示界面，方便你在电脑上操作注册、看数据、浏览知识。

**NURO是纯本地AI。** 不依赖Gateway，直接调用本地Ollama+双链记忆+MCP工具。断网也能用。

> 四个入口各司其职：豆包管进（知识沉淀），飞书调用（平台能力），Ghost管看（统一展示），NURO陪伴（本地AI）。数据通过 Gateway 路由到后端（NURO除外，纯本地）。

---

## 目录

1. [架构全景](#1-架构全景)
2. [项目整体状态速览](#2-项目整体状态速览)
3. [飞书机器人（总对话助理） -- 现状->目标->路径](#3-飞书机器人)
4. [豆包管道 -- 现状->目标->路径](#4-豆包管道)
5. [Ghost.html 官网 -- 现状->目标->路径](#5-ghosthtml-官网)
6. [Alpha-ID 身份层 -- 现状->目标->路径](#6-alpha-id-身份层)
7. [Gateway 网关 -- 现状->目标->路径](#7-gateway-网关)
8. [NURO 桌面精灵 -- 现状->目标->路径](#8-nuro-桌面精灵)
9. [豆包知识管道 -- 现状->目标->路径](#9-豆包知识管道)
10. [Nebula 工作流 -- 现状->目标->路径](#10-nebula-工作流)
11. [Flow/API 注册链路 -- 现状->目标->路径](#11-flowapi-注册链路)
12. [六层架构代码映射（完整版）](#12-六层架构代码映射完整版)
13. [架构审查 -- 做对的 vs 做错的](#13-架构审查)
14. [P0 任务清单（立即执行）](#14-p0-任务清单)
15. [P1 任务清单（本周执行）](#15-p1-任务清单)
16. [P2 任务清单（两周内）](#16-p2-任务清单)
17. [根目录清理计划](#17-根目录清理计划)
18. [已确认决策（不反复问）](#18-已确认决策)
19. [启动指南](#19-启动指南)
20. [参考文档 & 旧档说明](#20-参考文档)

---
## 1. 架构全景

> 图例：✅ 可用 | ⚠️ 半通 | ❌ 未实现 | 箭头 ↓ = 上层调用下层

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  🖥️  L1  用户交互层                                     ~7.3K 行 / 9文件        │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐  │
│  │ Ghost.html  2.5K     │  │ 飞书 WS长连接        │  │ NURO 桌宠  1.7K      │  │
│  │ ✅ 注册+仪表盘+聊天  │  │ ✅ 全平台能力        │  │ ✅ 本地AI贾维斯      │  │
│  └──────────────────────┘  └──────────────────────┘  └──────────────────────┘  │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐  │
│  │ 豆包阅读器 1.1K      │  │ MindFlow代理 1.8K    │  │ 微信适配器  483L     │  │
│  │ ✅ LevelDB→Obsidian  │  │ ⚠️ 路径未通          │  │ ⚠️ 代码有 未接入     │  │
│  └──────────────────────┘  └──────────────────────┘  └──────────────────────┘  │
├────────────────────────────────┬────────────────────────────────────────────────┤
│  🆔  L2  身份管理层 — Alpha-ID │  ~32.6K 行 / 141文件                          │
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
│  │ ✅ 已迁移至alphaid :8000 │  │  └──────────────────────────────────────────┘  │
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
│  │ ✅ Gateway内已实现  │ │ ✅ Gateway+豆包     │                               │
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
│  🚪  L5  网关管控层 — Gateway :18080                    1,857 行 / 17文件       │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │  /v1/human/*  ✅   /v1/agent/*  ✅   /v1/internal/*  ✅   /v1/net/*  ✅  │   │
│  │  四层路由: human(用户) agent(生态) internal(内部) net(网络)               │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │  基础设施: CORS白名单 | Correlation ID | 滑动窗口限流 | 统一信封 | 指标  │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────────────────┤
│  📡  L6  底层通信层                                                             │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │  AI Mesh libp2p  ❌ 未开发 — 先不碰                                       │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 数据流图

```
    [你]
     │
     ├──── 日常对话 ──→ 豆包 ──→ LevelDB扫描 ──→ 豆包阅读器 ──→ ✅ Gateway /v1/internal/doubao/capture
     │                                                                            │
     │                                                                            ▼
     │                                                         Alpha-ID 双链记忆(知链) + Obsidian
     │
     ├──── 消息 ────→ 飞书 ──→ feishu.py ──→ ✅ Gateway :18080 /v1/human/chat
     │                                             │
     │                                             ▼
     │                                     alphaid TwinBrain + AgentLoop
     │
     ├──── 浏览器 ──→ Ghost.html ──→ ✅ Gateway /v1/human/dashboard + /v1/human/chat
     │
     ├──── 桌面 ──→ NURO 桌宠 ──→ ✅ 本地 Ollama + 双链记忆 + MCP 后台
     │
     └──── 微信 ──→ 微信适配器 ──(未接入)───────────────→ ⚠️ 代码有


                              ┌─────────────────────────────────────┐
                              │     Gateway :18080                   │
                              │     四层路由 + 限流 + CORS + 指标    │
                              └───┬─────────────┬─────────────┬─────┘
                                  │             │             │
                    ┌─────────────┘             │             └─────────────┐
                    ▼                           ▼                           ▼
        ┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
        │  alphaid :8000    │     │  nebula :2002     │     │  flow/api :3036   │
        │  ~32.6K 行        │     │  ~7.7K 行         │     │  ~4.4K TS         │
        │                   │     │                   │     │                   │
        │  ✅ 身份(DID)     │     │  ✅ 工作流引擎    │     │  ✅ 注册链路      │
        │  ✅ 双链记忆      │     │  ✅ 百度地图      │     │  手机→短信→人脸   │
        │  ✅ TwinBrain     │     │  ✅ AI网关        │     │  →DID            │
        │  ✅ AgentLoop     │     │  ✅ 中间件×6     │     │  支付宝人脸       │
        │  ✅ 风控/恢复     │     │  ✅ 插件SDK      │     │  阿里云短信       │
        │  ⚠️ 多租户(已写)  │     │  ⚠️ 自动化       │     │                   │
        └───────────────────┘     └───────────────────┘     └───────────────────┘
```

### 1.3 六层概览

| 层 | 名称 | 代码量 | 核心组件 | 状态 |
|:--:|:-----|:------:|:---------|:----:|
| L6 | 底层通信层 | 0 | AI Mesh libp2p | ❌ 未开发 |
| L5 | 网关管控层 | 1,857L / 17文件 | Gateway :18080 四层路由(human/agent/internal/net) + CORS + 限流 + 统一信封 + 指标 | ✅ 全路由可用 |
| L4 | Agent调度层 | ~7.4K / 32文件 | AgentLoop, Orchestrator, Tenant, Risk, Recovery, Observability, A2A | ⚠️ 基本完整 |
| L3 | 记忆知识库层 | ~1.6K | 双链记忆(统一SQLite), TwinBrain, Coala记忆, 记忆防御 | ⚠️ 知识引擎已迁入Gateway |
| L2 | 身份管理层 | ~32.6K / 141文件 | DID, 签名, Agent网络, JWT, Profile, 挖矿采集, CLI, NURO桌宠 | ✅ 最完整 |
| L1 | 用户交互层 | ~7.3K / 9文件 | Ghost.html, 飞书WS, NURO桌宠, 豆包阅读器, 微信适配器, MindFlow代理 | ⚠️ 半通 |

### 1.4 四条对话路径

| 路径 | 入口 | 调用链路 | 工具数 | 能做什么 | 缺什么 |
|:----:|:-----|:---------|:------:|:---------|:-------|
| A | Ghost.html | Gateway /v1/human/* → TwinBrain → AgentLoop | 14 | 注册/仪表盘/聊天/身份/记忆 | 知识浏览(P2) |
| B | 飞书 | feishu.py → Gateway /v1/human/chat → AgentLoop | 14 | 全平台能力(身份/记忆/地图/对话) | 知识查询(P2) |
| C | 豆包 | LevelDB → 豆包阅读器 → Gateway /v1/internal/doubao/capture | 5 | 知识自动沉淀到Obsidian | 知识查询接口(P2) |
| D | NURO | 本地 Ollama + 双链记忆 + MCP | 7+ | 桌面悬浮精灵/语音/视觉/观察 | 多模态调优 |

### 1.5 完整组件清单（按模块分）

#### alphaid/projects/src/core/ — 8,741 行 / 38 文件

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

#### alphaid/projects/src/alpha_id/ — ~11.3K 行 / 44 文件

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

#### alphaid/projects/src/auth/ + entrypoints/ + api/ + tools/ + mindflow/

| 模块 | 文件数 | 行数 | 职责 | 状态 |
|:-----|:------:|:----:|:-----|:----:|
| auth/ | 5 | 443 | JWT + 中间件 + Token存储 | ✅ 已写 |
| entrypoints/ | 9 | 2,716 | NURO桌宠(1.7K) + API(217) + MCP(3,109) | ✅ NURO运行中 |
| api/ (REST路由) | 10 | 1,304 | 路由 — identity/risk/shortdrama/social | ⚠️ |
| tools/ | 7 | 1,479 | 工具 — OCR/截屏/安全/窗口/身份 | ⚠️ 已写 |
| mindflow/ | 10 | 2,478 | 工作流 — engine/intent/onboarding/agents | ⚠️ 路径未通 |
| templates/ghost.html | 1 | 2,515 | Ghost.html 官网前端 | ✅ 注册+仪表盘+聊天 |

#### nebula/src/mindflow_map/ — 7,708 行 / 67 文件

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

#### ghost-main/gateway/ — 1,857 行 / 17 文件 (不含测试)

| 文件 | 行数 | 职责 | 状态 |
|:-----|:----:|:-----|:----:|
| app.py | 426 | FastAPI 网关主入口 — 四层路由+生命周期+豆包扫描器 | ✅ 结构好 |
| config.py | 57 | 集中配置 — 服务URL/端口/限流/CORS | ✅ |
| routes/human.py | 294 | /v1/human/* — 用户接口(identity/profile/brain/chat/memory/obsidian) | ✅ |
| routes/agent.py | 52 | /v1/agent/* — A2A拓扑+信息订阅 | ✅ |
| routes/flow.py | 235 | /v1/agent/flow/* — 工作流模板+AID会话+地图+Computer Use | ✅ |
| routes/internal.py | 152 | /v1/internal/* — 豆包捕获+Obsidian+健康检查 | ✅ |
| routes/net.py | 36 | /v1/net/* — Net-Agent 代理 | ✅ |
| services/proxy.py | 111 | HTTP代理 — 连接池+统一信封+错误处理 | ✅ |
| services/obsidian.py | 184 | Obsidian 服务 — 写入+搜索+整理触发 | ✅ |
| services/memory_graph.py | 119 | 记忆图谱 — 双链记忆查询 | ✅ |
| services/metrics.py | 107 | 指标收集 — 请求计数+后端健康 | ✅ |
| middleware/correlation.py | 30 | Correlation ID 中间件 | ✅ |
| middleware/rate_limit.py | 41 | 滑动窗口限流中间件 | ✅ |
| tests/ (6文件) | 938 | 测试 — health/rate_limit/integration_routing/e2e | ✅ |
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
- 文件: ghost-main/gateway/ 1,857L/17文件 (不含测试)
- 路由: 四层架构 — /v1/human/* /v1/agent/* /v1/internal/* /v1/net/*
- 已通: human(identity/profile/brain/chat/memory/obsidian) + agent(A2A/feeds/flow) + internal(doubao/obsidian/health) + net(代理)
- 基础设施: CORS白名单 / Correlation ID / 滑动窗口限流 / 统一信封 / 指标收集
- 豆包扫描器: Gateway启动时自动启用，扫描豆包桌面LevelDB
- 状态: V 四层路由全通，生产级基础设施完整

#### 板块3: 飞书总对话助理
- 文件: nebula/mindflow_map/api/feishu.py 234L WS长连接（心跳已修复）
- 当前路径（P0-4修复后）: 飞书消息 -> feishu.py -> httpx POST Gateway /v1/chat -> alphaid TwinBrain+AgentLoop
- 原路径（P0前）: feishu.py -> workflows/engine.execute() -> 只配了MapNavigationTool+IntentParser -> 只有3工具 -> 匹配不到=报错
- 已清理: alphaid/feishu_bot/整目录删了（重复代码）+ callback_server.py（旧引擎）
- 现在能: 身份查询/记忆查询/地图导航/通用对话
- 待修: feishu.py L22-23硬编码凭证移入环境变量（P1）
- 状态: V 已通Gateway，能调全平台能力

#### 板块4: Ghost展示层
- 文件: alphaid/templates/ghost.html 2,515L（已删除重复 Mindflow 面板）
- UI: TailwindCSS编译 两视图架构（A2A 生态区 + Mindflow 协作台）
- 已加: fetchDashboard()调Gateway /v1/human/dashboard + sendChatMessage()调/v1/human/chat + 注册UI调Gateway→alphaid
- 当前: 注册流程（SMS→人脸→DID）已通过Gateway→alphaid打通，浏览器可操作完整注册
- 状态: V 注册+仪表盘+聊天全通

#### 板块5: 豆包知识管道（已开发）
- 文件: ghost-main/doubao_reader/ 1,055L/5文件
- 现状: 已开发完成。LevelDB扫描→精炼→Obsidian写入全自动
- 模块: log_reader(239L) + knowledge_refiner(204L) + obsidian_writer(208L) + obsidian_organizer(306L) + reader_daemon(98L)
- 数据流: 豆包桌面LevelDB → LogReader解析 → KnowledgeRefiner精炼 → Gateway /v1/internal/doubao/capture → Alpha-ID双链记忆 + Obsidian
- 守护进程: reader_daemon 60秒间隔自动扫描
- 状态: V 已开发，Gateway集成完成

#### 板块6: Obsidian知识库（已接入）
- 现状: Gateway services/obsidian.py(184L) + doubao_reader/obsidian_writer.py(208L) + obsidian_organizer.py(306L)
- 方案: 接收豆包精炼后的结构化知识 -> 生成MD文件 -> 按主题分类 -> 带YAML frontmatter(标签/链接/时间戳)
- 自动整理: wiki-links生成 + 日报 + 标签索引
- 查询: Gateway /v1/human/obsidian/search 已可用
- 状态: V 写入+整理+查询全通

#### 板块7: NURO 桌面精灵（已开发）
- 文件: alphaid/projects/src/entrypoints/ 1,719L/7文件
- 定位: 纯本地 AI 贾维斯，Windows 桌面悬浮精灵
- 模块: app.py(1,047L主类) + cli.py(190L入口) + feature_flags.py(171L) + daily_summary.py(95L) + acrylic.py(56L) + palette.py(24L) + daemon.py(136L兼容层)
- 语音链路: Whisper STT → Ollama LLM → Coqui TTS
- 视觉: MiniCPM-o-4.5 多模态
- VRAM预算: RTX 5070 Ti 16GB 实测 ~10.3GB
- MCP后台服务器: 提供外部工具调用接口
- 隐私模式: blind(不截图)/deaf(不监听)
- 安装: install_deskpet.bat 一键安装
- 状态: V 已开发完成

### 四条使用主线

主线A（知识进）: 豆包聊天 -> LevelDB扫描 -> 豆包阅读器 -> Gateway -> Alpha-ID双链记忆 + Obsidian卡片
主线B（能力用）: 对话飞书 -> feishu.py -> Gateway :18080 -> alphaid/nebula/flow
主线C（统一看）: 打开Ghost.html -> fetchDashboard/sendChatMessage -> Gateway -> 后端
主线D（桌面伴）: NURO桌宠 -> 本地Ollama + 双链记忆 + MCP -> 语音/视觉/观察

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
| alphaid | 8000 | 运行中 | ~32.6K Python / 141文件 + 2.5K HTML | 身份+记忆+双脑+AgentLoop+采集+CLI+NURO 全栈核心 |
| nebula | 2002 | 运行中 | ~7.7K Python / 67文件 | 工作流引擎+飞书WS+AI网关+中间件+插件SDK |
| gateway | 18080 | 运行中 | 1,857 Python / 17文件 | 统一网关 四层路由+CORS+限流+统一信封+指标 |

### 2.2 写完了但没启动的

| 服务 | 端口 | 行数 | 说明 |
|:-----|:----:|:----:|:------|
| flow/api | 3001 | ~4.4K TS | AI 路由/Computer Use（注册已迁至alphaid :8000） |

### 2.3 核心问题一句话

代码很多（~45K行）且关键路径已打通 -- 飞书走Gateway全平台可用、Ghost注册+仪表盘+聊天全通、豆包LevelDB自动沉淀、NURO桌宠独立运行。当前短板：知识查询接口(P2)、多租户隔离、A2A真实通信。需要的是打磨而不是加功能。

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
Ghost.html -> 仪表盘(从Gateway拉真实数据) ✅
           -> 注册/登录(手机号->短信->人脸->DID) ✅
           -> 聊天面板(POST /v1/human/chat) ✅
           -> 知识浏览(P2)

### 5.3 中间步骤
| 步骤 | 做什么 | 优先级 | 状态 |
|:-----|:-------|:------:|:----:|
| 1 | 加fetchDashboard调Gateway | P0 | ✅ DONE |
| 2 | 加注册页面 | P0 | ✅ DONE |
| 3 | 加聊天面板 | P0 | ✅ DONE |
| 4 | 知识浏览 | P2 | ⚠️ 待做 |

### 5.4 衔接关系

Ghost.html是**Web展示层**，不是主入口。它通过Gateway调后端接口。页面已加入fetchDashboard()和sendChatMessage()，启动后可看到真实数据。

Ghost.html -> Gateway :18080 -> alphaid :8000 / flow/api :3036

---
## 6. Alpha-ID 身份层 -- 现状->目标->路径

### 6.1 现状
这是项目中最完整的部分。总分三个大目录 + 入口模块：

**alpha_id/** (~11.3K行/44文件) — 身份+社交+采集+CLI

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

**core/** (8,741行/38文件) — 核心引擎层（见§1.5完整表）

**entrypoints/** (2,716行/9文件) — NURO桌宠 + API + MCP

**入口已清理：** 短剧已删，feishu_bot已删，daemon.py改为兼容shim

### 6.2 目标
核心层保持干净(身份+记忆+AgentLoop+事件总线) 删冗余 只留api.py + aid_mcp_server.py + NURO模块

### 6.3 中间步骤
| 步骤 | 做什么 | 优先级 | 状态 |
|:-----|:-------|:------:|:----:|
| 1 | 删短剧 shortdrama_service.py | P0 | ✅ DONE |
| 2 | 删 alphaid/feishu_bot/ | P0 | ✅ DONE |
| 3 | 清理 main.py入口 | P0 | ✅ DONE |
| 4 | 统一入口只留 api.py + aid_mcp_server.py | P0 | ✅ DONE |

### 6.4 衔接关系

Alpha-ID是**身份根基**，所有入口（豆包/飞书/Ghost/NURO）最终都要通过它。飞书通过Gateway查身份，Ghost通过Gateway注册身份，NURO本地调用身份API。注册链路的短信验证和人脸识别已由alphaid（Python）接管，不再依赖flow/api。

飞书/Ghost -> Gateway -> alphaid DID (身份查询/注册)
NURO -> alphaid (本地身份/记忆)

---
## 7. Gateway 网关 -- 现状->目标->路径

路径: `D:\MW\ghost-main\gateway/` 1,857行 / 17文件
入口: `gateway/app.py` (426行)
架构: 四层路由 — human / agent / internal / net

当前路由:
| 层级 | 路由 | 后端 | 状态 |
|:-----|:-----|:-----|:----:|
| human | GET /v1/human/identity | alphaid :8000 | ✅ |
| human | GET /v1/human/profile | alphaid :8000 | ✅ |
| human | GET /v1/human/brain/status + POST /v1/human/brain/awake | alphaid :8000 | ✅ |
| human | POST /v1/human/chat (限流5/60s) | alphaid :8000 | ✅ |
| human | GET /v1/human/memory/graph | alphaid :8000 | ✅ |
| human | GET /v1/human/obsidian/search | 本地Obsidian | ✅ |
| agent | GET /v1/agent/interact/topology | alphaid :8000 | ✅ |
| agent | GET /v1/agent/feeds/latest | 本地 | ✅ |
| agent | /v1/agent/flow/* | flow :3036 | ✅ |
| internal | POST /v1/internal/doubao/capture | alphaid :8000 | ✅ |
| internal | GET /v1/internal/obsidian/status | 本地 | ✅ |
| internal | GET /v1/internal/health | 本地 | ✅ |
| net | /v1/net/* | net-agent :18180 | ✅ |

基础设施: CORS白名单 / Correlation ID / 滑动窗口限流(5/60s) / 统一信封 {success,data,ts,request_id} / 指标收集

目标: 四层路由全通(已完成) + 内容审核(P2) + 监控Trace(P2)

### 7.4 衔接关系

Gateway是**统一入口**，所有外部请求（飞书/Ghost/NURO）都经过它路由到后端服务。飞书调/v1/human/chat，Ghost调/v1/human/dashboard和/v1/human/chat，注册流程调/v1/human/*，豆包调/v1/internal/doubao/capture。

飞书 -> Gateway -> alphaid/nebula/flow
Ghost -> Gateway -> alphaid/flow
NURO -> Gateway -> alphaid(身份/记忆)

---
## 8. NURO 桌面精灵 -- 现状->目标->路径

### 8.1 现状
路径: `D:\MW\alphaid\projects\src/entrypoints/` (NURO模块 1,719行 / 7文件，不含api.py和aid_mcp_server.py)

| 模块 | 行数 | 职责 | 状态 |
|:-----|:----:|:-----|:----:|
| app.py | 1,047 | AidNuro 主类 — 14步启动序列 | ✅ 可运行 |
| cli.py | 190 | CLI 入口 — 参数解析+环境检测+启动 | ✅ |
| feature_flags.py | 171 | 功能标志 — 所有 _HAS_* 能力检测 | ✅ |
| daily_summary.py | 95 | 每日总结调度 — 22:00自动+手动触发 | ✅ |
| acrylic.py | 56 | DWM 亚克力效果 — Win10/11 窗口模糊 | ✅ |
| palette.py | 24 | UI 调色板 — 深色主题配色 | ✅ |
| daemon.py | 136 | 向后兼容 re-export shim | ✅ |

### 8.2 核心能力

**14步启动序列:**
1. 身份初始化（FOUNDER → NURO DID）
2. 记忆接入（双链记忆）
3. 大脑（MiniCPM-o + Ollama）
4. 语音（Whisper + Coqui TTS）
5. 通知气泡
6. 主动观察器
7. 每日总结
8. Tkinter 角色窗口
9. 2D 角色（FairyCharacter 或降级为 emoji）
10. 右键菜单
11. 语音唤醒监听
12. MCP 后台服务器
13. 启动观察循环
14. 气泡绑定 + 呼吸动画 + 每日总结定时器

**语音链路:** Whisper STT → Ollama LLM → Coqui TTS
**视觉:** MiniCPM-o-4.5 多模态
**VRAM预算（RTX 5070 Ti 16GB）:**
- MiniCPM-o Q4_K_M: ~5.5GB
- Whisper tiny: ~0.5GB（CPU模式）
- Coqui TTS: ~1.5GB
- CUDA + 系统: ~2.5GB
- Tkinter + 角色: ~0.3GB
- 总计: ~10.3GB（剩余 5.7GB）

**隐私模式:** blind(不截图) / deaf(不监听)
**安装:** `install_deskpet.bat` 一键安装

### 8.3 目标
NURO成为完整的本地AI助手：语音对话、视觉理解、主动观察、每日总结、MCP工具调用全部可用。

### 8.4 衔接关系
NURO是**纯本地AI贾维斯**，不依赖Gateway。它直接调用Ollama(本地LLM)、双链记忆(本地SQLite)、MCP工具。可选通过Gateway与Alpha-ID同步身份和记忆。

你 -> 语音/文字 -> NURO -> Ollama LLM -> 双链记忆
                  -> MiniCPM-o(视觉)
                  -> MCP工具(截屏/窗口/OCR)

### 8.5 中间步骤
| 步骤 | 做什么 | 优先级 |
|:-----|:-------|:------:|
| 1 | 完成14步启动序列 | P0 DONE |
| 2 | Whisper+Ollama+Coqui语音链路 | P0 DONE |
| 3 | MiniCPM-o多模态接入 | P1 |
| 4 | MCP后台服务器 | P1 |
| 5 | 主动观察循环优化 | P2 |

---
## 9. 豆包知识管道 -- 现状->目标->路径

### 9.1 现状
路径: `D:\MW\ghost-main\doubao_reader\` 1,055行 / 5文件

| 模块 | 行数 | 职责 | 状态 |
|:-----|:----:|:-----|:----:|
| log_reader.py | 239 | LevelDB解析 — 读取豆包桌面IndexedDB | ✅ 可用 |
| knowledge_refiner.py | 204 | 知识精炼 — 去噪/去重/自动标签 | ✅ 可用 |
| obsidian_writer.py | 208 | Obsidian写入 — YAML frontmatter+MD | ✅ 可用 |
| obsidian_organizer.py | 306 | 自动整理 — wiki-links+日报+索引 | ✅ 可用 |
| reader_daemon.py | 98 | 守护进程 — 60秒间隔自动扫描 | ✅ 可用 |

### 9.2 数据流
```
豆包桌面App (IndexedDB LevelDB)
    → LogReader.parse_log_file() 解析会话
    → 去重+结构化处理
    → KnowledgeRefiner 精炼(去噪/去重/自动标签)
    → Gateway /v1/internal/doubao/capture (仅本地IP)
    → Alpha-ID /memory/store → 双链记忆(知链)
    → ObsidianWriter 写入 D:\Obsidian\Ghost知识库
    → ObsidianOrganizer 自动整理(wiki-links+日报+索引)
```

### 9.3 目标
豆包对话全自动沉淀到Obsidian知识库，零人工干预，飞书/Ghost可查询。

### 9.4 衔接关系
豆包是**知识入口**。日常对话通过LevelDB扫描自动捕获，精炼后写入Obsidian。沉淀的知识可通过Gateway查询。

豆包 -> LevelDB -> 豆包阅读器 -> Gateway -> Alpha-ID双链记忆 + Obsidian
Ghost/飞书 -> Gateway /v1/human/obsidian/search -> 查询知识

### 9.5 中间步骤
| 步骤 | 做什么 | 优先级 |
|:-----|:-------|:------:|
| 1 | LevelDB解析器 | P0 DONE |
| 2 | 知识精炼引擎 | P0 DONE |
| 3 | Gateway /v1/internal/doubao/capture 集成 | P0 DONE |
| 4 | Obsidian写入+整理 | P0 DONE |
| 5 | 守护进程自动扫描 | P0 DONE |
| 6 | 飞书/Ghost知识查询接口 | P2 |

---
## 10. Nebula 工作流 -- 现状->目标->路径

路径: `D:\MW\nebula\src\mindflow_map\` 67文件 / 7,708行
入口: `mindflow_map/main.py`
核心: 工作流引擎 + AI网关(intent/llm/circuit_breaker) + 中间件(rate_limit/auth/audit/prometheus) + 插件SDK(@tool装饰器) + 自动化(抖音/Shopify)
飞书已改走Gateway Nebula退回纯工作流引擎
目标: 飞书走Gateway Nebula专注工作流/地图/自动化

| 步骤 | 做什么 | 优先级 |
|:-----|:-------|:------:|
| 1 | feishu.py改调Gateway | P0 DONE |
| 2 | 修正ci.yml | P1 |

### 10.3 衔接关系

Nebula是**工作流引擎**，负责飞书WS长连接和地图导航等业务。它通过Gateway与alphaid对接，不直接调用后端。

飞书 -> feishu.py -> Gateway -> nebula（工作流/地图）

---
## 11. Flow/API 注册链路 -- 现状->目标->路径

路径: D:\MW\flow\apps\api\ TS+Fastify ~4.4K行
注册路由完整(手机号->短信->人脸->DID)
支付宝人脸代码已写 短信验证有真实阿里云Key
注册路由已迁移至alphaid :8000

目标: 注册由alphaid承接，Flow/API专注工作流/地图/Computer Use

| 步骤 | 做什么 | 优先级 |
|:-----|:-------|:------:|
| 1 | npm install | P0 DONE |
| 2 | 注册路由迁移至alphaid | P0 DONE |
| 3 | Gateway /v1/agent/flow/* 代理 | P0 DONE |

### 11.4 衔接关系

Flow/API提供**工作流/地图/Computer Use**服务（原注册职责已迁至alphaid）。Gateway的/v1/agent/flow/*路由代理到它。

Ghost/飞书 -> Gateway /v1/agent/flow/* -> flow/api :3036

---
## 12. 六层架构代码映射（完整版）

> 详细到文件级别的映射见 §1.5 完整组件清单。本节为精简速查版。

### L1 用户交互层 (~7,300行)
| 文件 | 真实路径 | 行数 | 状态 |
|:-----|:---------|:----:|:----:|
| Ghost.html | `alphaid/projects/src/alpha_id/templates/ghost.html` | 2,515 | ✅ 注册+仪表盘+聊天 |
| 飞书机器人 | `nebula/src/mindflow_map/api/feishu.py` | ~200 | ✅ 全平台能力 |
| 飞书Webhook | `nebula/src/mindflow_map/api/feishu_webhook.py` | ~150 | ⚠️ 备选 |
| NURO桌宠 | `alphaid/projects/src/entrypoints/` | 1,719 | ✅ 本地AI贾维斯 |
| 豆包阅读器 | `ghost-main/doubao_reader/` | 1,055 | ✅ LevelDB→Obsidian |
| 微信适配器 | `alphaid/projects/src/core/action_engine/adapters/wechat.py` | 483 | ⚠️ 已写未接 |
| MindFlow代理 | `nebula/src/mindflow_map/api/` | ~1,800 | ⚠️ 路径未通 |

### L2 身份管理层 (~32,600行)
| 文件 | 真实路径 | 行数 | 状态 |
|:-----|:---------|:----:|:----:|
| DID核心 | `alphaid/projects/src/alpha_id/did.py` | ~1,200 | ✅ 完整 |
| 签名器 | `alphaid/projects/src/alpha_id/signer.py` | ~900 | ✅ 完整 |
| Agent SDK | `alphaid/projects/src/alpha_id/agent.py` | ~500 | ✅ SDK入口 |
| Agent网络 | `alphaid/projects/src/alpha_id/agent_network.py` | ~1,500 | ⚠️ 本地模拟 |
| JWT认证 | `alphaid/projects/src/auth/` | 295 | ✅ 已写 |
| 采集器(9个) | `alphaid/projects/src/alpha_id/collectors/` | ~1,200 | ⚠️ 部分可用 |
| CLI(7个) | `alphaid/projects/src/alpha_id/*_cli.py` | ~1,500 | ✅ 可用 |
| 注册路由 | `alphaid/projects/src/alpha_id/web.py` | ~600 | ✅ 已迁移至alphaid |

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

### L5 网关管控层 (1,857行)
| 文件 | 真实路径 | 行数 | 状态 |
|:-----|:---------|:----:|:----:|
| Gateway | `ghost-main/gateway/app.py` | 426 | ✅ 四层路由+限流+信封+指标 |
| 路由 | `ghost-main/gateway/routes/` | 777 | ✅ human/agent/flow/internal/net |
| 服务 | `ghost-main/gateway/services/` | 525 | ✅ proxy/obsidian/memory/metrics |
| 中间件 | `ghost-main/gateway/middleware/` | 72 | ✅ correlation/rate_limit |
| 配置 | `ghost-main/gateway/config.py` | 57 | ✅ 集中配置 |
| 测试 | `ghost-main/gateway/tests/` | 938 | ✅ health/rate_limit/integration/e2e |

### L6 底层通信层 (0行)
| 模块 | 路径 | 状态 |
|:-----|:-----|:----:|
| AI Mesh libp2p | 未开发 | ❌ 先不碰 |

---
## 13. 架构审查 -- 做对的 vs 做错的

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

### 13.2 做错了的(已修正)
| # | 错误 | 表现 | 纠正 | 状态 |
|---|------|------|------|:----:|
| 1 | 飞书走错路 | feishu.py→workflows/engine只地图 | 飞书→Gateway→LLM分流 | ✅ 已修正 |
| 2 | alphaid入口混乱 | 4入口(api/daemon/mcp/shortdrama)+feishu_bot重复 | 只留api.py+aid_mcp_server.py | ✅ 已修正 |
| 3 | Ghost假官网 | 3507行0次fetch | 加fetch调Gateway | ✅ 已修正 |
| 4 | 豆包无入口 | 核心输入进不了Ghost | 豆包→LevelDB→阅读器→Gateway→Obsidian | ✅ 已修正 |
| 5 | 飞书两套重复代码 | nebula/feishu+alphaid/feishu_bot | 只保留nebula | ✅ 已修正 |
| 6 | flow/api注册未启动 | 注册链路代码完整但路由不通 | 注册迁移至alphaid :8000 | ✅ 已修正 |
| 7 | 微信适配器写了没接 | wechat.py 483L在action_engine里 | 接入Gateway或删除 | ⚠️ 待处理 |

### 13.3 冗余待删
| 项 | 位置 | 大小 | 原因 | 状态 |
|:---|:-----|:----:|:-----|:----:|
| 短剧服务 | entrypoints/shortdrama_service.py | ~800L | 无关 | ✅ 已删 |
| 桌面精灵 | entrypoints/daemon.py | ~700L | 空壳 | ✅ 改为兼容shim |
| feishu_bot重复 | feishu_bot/ | 304L | nebula已有 | ✅ 已删 |
| flow双链记忆TS版 | flow/.../dual-chain.ts | ~5K | 有Python版 | ✅ 已删 |
| flow旧路由 | workflow.ts+map.ts | ~3K | 不再用 | ✅ 已删 |

---
## 14. P0 任务清单(立即执行)

### P0-1 删冗余代码 ✅ DONE (2026-07-25)
删除: shortdrama_service.py + alphaid/feishu_bot/ + flow重复模块(dual-chain.ts/workflow.ts/map.ts)
daemon.py 保留为向后兼容 re-export shim

### P0-2 启动flow/api注册链路 ✅ DONE (2026-07-26)
注册路由6条已迁移至alphaid :8000，Gateway代理已更新。
Flow/API不再承载注册职责，转为工作流/地图/Computer Use服务。

### P0-3 Ghost.html加真实API ✅ DONE (2026-07-26)
已加: fetchDashboard()调Gateway /v1/human/dashboard
已加: 注册页面UI(手机号->短信->人脸->DID) 通过Gateway→alphaid打通
已加: 聊天面板(输入->POST /v1/human/chat)

### P0-4 飞书改走Gateway+LLM分流 ✅ DONE (2026-07-26)
Gateway已加四层路由(含/v1/human/chat)
feishu.py已改调Gateway /v1/human/chat
alphaid/feishu_bot/已删

---
## 15. P1 任务清单(本周)
| # | 任务 | 工作量 | 状态 |
|---|------|:------:|:----:|
| 1 | 飞书凭证移入环境变量 | 0.5h | ⚠️ 待做 |
| 2 | FOUNDER身份移入环境变量 | 0.5h | ⚠️ 待做 |
| 3 | 修正CI路径 | 0.5h | ⚠️ 待做 |
| 4 | 调研豆包直连Obsidian方案 | 3h | ✅ 已做(LevelDB方案) |
| 5 | 豆包知识自动同步到Obsidian | 4h | ✅ 已做 |
| 6 | Obsidian知识卡片查询接口 | 3h | ⚠️ 待做 |
| 7 | alphaid目录重构 | 2h | ⚠️ 待做 |

---
## 16. P2 任务清单(两周内)
| # | 任务 | 说明 |
|---|------|------|
| 1 | Ghost知识搜索 | 搜索浏览卡片 |
| 2 | 飞书知识查询 | 查记忆/卡片 |
| 3 | 内容审核中间件 | Gateway做 |
| 4 | 限流中间件升级 | Token Bucket |
| 5 | 监控Trace | 链路追踪 |
| 6 | 多租户隔离 | 多用户准备 |
| 7 | A2A真实通信 | HTTP/WS升级 |
| 8 | NURO多模态优化 | MiniCPM-o调优 |

---
## 17. 根目录清理计划
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
## 18. 已确认决策（项目宪法）

以下决策是项目基石，后续所有开发必须遵循，不反复确认：

| 决策 | 来源 | 影响 |
|:-----|:------|:-----|
| 唯一官网 = Ghost.html（不是其他任何页面） | 用户明确 | 所有用户界面统一走Ghost |
| 豆包 = 知识输入主入口 + 自己就是整理引擎 | 用户明确 | 不做中间层，豆包直连Obsidian |
| 飞书 = 总对话助理 | 用户明确 | 自然语言对话走Gateway调全平台能力 |
| 不用微信、不用Claude Code | 用户明确 | 删除相关代码 |
| 飞书不走工作流引擎，走Gateway+LLM分流 | 默认同意 | feishu.py已改 |
| 文档只留GHOST.md + archive/md_old/ | 已执行 | 根目录只保留3项 |
| 已删：短剧/feishu_bot/DS/flow重复 | P0已执行 | 冗余已清理 |
| 豆包 = LevelDB扫描方案（非API） | 技术决策 | 零API依赖，离线工作 |
| NURO = 纯本地AI（不依赖Gateway） | 架构决策 | 本地Ollama+双链记忆 |
| 对话中没反驳的 = 默认同意 | 用户明确 | 不需要反复确认 |
| 不要做的：AI Mesh libp2p / Skill自进化 / A2A真实网络通信 | 架构审查 | L6和部分L4功能先不碰 |

---
## 19. 启动指南

### 三个核心服务

```bash
# 1. Alpha-ID (身份+记忆+AgentLoop+NURO)
cd D:\MW\alphaid\projects
python -m uvicorn entrypoints.api:app --host 0.0.0.0 --port 8000

# 2. Nebula (工作流+飞书WS)
cd D:\MW\nebula
python -m uvicorn src.mindflow_map.main:app --host 0.0.0.0 --port 2002

# 3. Gateway (统一网关)
cd D:\MW\ghost-main\gateway
python -m uvicorn app:app --host 0.0.0.0 --port 18080
```

### 验证

| 验证项 | 命令/URL | 期望 |
|:-------|:---------|:-----|
| Alpha-ID | http://localhost:8000/api/health | ✅ 200 |
| Nebula | http://localhost:2002/health | ✅ 200 |
| Gateway | http://localhost:18080/v1/internal/health | ✅ 200 |
| Ghost.html | 浏览器打开 alphaid/projects/src/alpha_id/templates/ghost.html | 注册/仪表盘/聊天 |
| 飞书 | 发消息给飞书机器人 | 全平台能力响应 |
| NURO | `python -m entrypoints.cli` 或 `aid-daemon` | 桌面精灵启动 |
| 豆包 | 自动扫描（Gateway启动后自动启用） | LevelDB→Obsidian |

### NURO 桌宠单独启动

```bash
cd D:\MW\alphaid\projects
python -m entrypoints.cli          # 正常启动
python -m entrypoints.cli --check  # 环境检测
install_deskpet.bat                # 一键安装
```

---
## 20. 参考文档&旧档说明
旧文档在archive/md_old/保留不动: ARCHITECTURE.md ECOSYSTEM_ARCHITECTURE.md ROOT_AUDIT.md PLATFORM_VISION.md PROJECT_AUDIT.md AID_FULL_INTEGRATION.md 繁星计划申请材料.md

根目录只保留: GHOST.md + README.md + archive/

详细组件文档:
- NURO桌宠: `alphaid/projects/docs/nuro-desktop-pet.md`
- Ghost.html前端: `alphaid/projects/docs/ghost-frontend.md`
- 豆包阅读器: `ghost-main/docs/doubao-reader.md`

---
## 变更记录
| 日期 | 版本 | 变更 |
|:-----|:----|:------|
| 2026-07-27 | 4.0 | 全面大修:版本升至4.0 修正全部行数(Gateway 1,857L/17F, Alpha-ID 32.6K/141F, Nebula 7.7K/67F) P0-1~P0-4标记DONE 新增§8 NURO桌面精灵(1,719L/7F) 新增§9豆包知识管道(1,055L/5F) 架构图加入NURO+豆包 启动指南更新为实际命令 |
| 2026-07-25 | 3.0 | 全面审计:修正全部行数/路径/状态标记 新增§1.5完整组件清单 修复Mermaid→ASCII框图 统一✅⚠️❌ |
| 2026-07-25 | 2.0 | 完整重写:整合5份旧文档+全部审计+今日决策 每组件写现状→目标→路径 |
| 2026-07-25 | 1.0 | 初始整合版 |


