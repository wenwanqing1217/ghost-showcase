# Ghost 项目 -- 完整框架与现状实录

> **版本 5.0** | **2026-08-04**  
> **项目宪法：** 不做单点AI工具、不做工作流编排、不局限于技能市场。打造**国内合规、以人为核心的Web4.0人机共生基础设施**。  
> **终极定位：** Web4.0 AtoA（Agent-to-Anything）全域自主智能体操作系统  
> **核心载体：** Alpha-ID（个人终身DID身份 + AI外置大脑调度中枢）  
> **底层网络：** Ghost（A2A万物互联协议层）  
> **MVP场景：** 跨境电商全自动铺货履约（验证自动化闭环）  
> **总纲：** 身份→记忆→调度→网关→通信，五层地基打通后才是业务和商业。

---

## 项目基调（来自基准文档 Ghost Web4.0.md + 终版架构复盘 1.md & 2.md）

### 核心理念
| 维度 | 定位 |
|:-----|:------|
| **做什么** | 搭建一套「可以替人类自动上网、自动对接一切系统、自动执行全流程、自动决策、多智能体互联协作的Web4.0操作系统」 |
| **不做什么** | 不碰区块链/虚拟币/NFT，不发代币，所有数据部署国内服务器，遵循《个人信息保护法》 |
| **电商的定位** | 不是项目主体，是验证「人机自动化商业闭环」的最小MVP场景。货源→铺货→售卖→履约→数据协同闭环 |
| **最终形态** | 一人一生唯一Alpha-ID + 双链记忆 + A2A智能体协同 + Skill插件生态 + Obsidian知识闭环 + 合规双边商业生态 |

### 四代互联网定位
| 时代 | 痛点 | Ghost 的突破 |
|:-----|:------|:-------------|
| Web1.0 | 人单向浏览，无交互 | - |
| Web2.0 | 账号/数据归属平台，网页充斥广告机器难解析 | 搭建脱离Web2杂乱网页的机器可读内容生态 |
| Web3.0 | 侧重链上资产，缺AI自动化 | 以DID身份为根基，叠加A2A智能体协同 |
| Web4.0 | 工具孤岛、权限混乱、记忆碎片化 | Alpha-ID + 双链记忆 + A2A + 标准工作流 + 商业生态 |

### 三层终极堆栈
| 层 | 名称 | 本质 |
|:--:|:-----|:-----|
| 顶层 | **理念层：Denny AI外置大脑范式** | 人类只做顶层目标决策，99%信息处理/执行/迭代/运营交给AI智能体集群 |
| 中层 | **系统中枢：AlphaID 多智能体操作系统** | 租户隔离 + Skill生态市场 + 智能任务编排 + 业务场景层 + 数据中台 |
| 底层 | **Web4.0基建：Ghost AtoA 万物互联层** | 全网穿透接入 + 浏览器自主Agent执行 + 分布式微服务网关 + 所有外部系统统一接入总线 |

### 三条主线
| 主线 | 入口 | 调用链路 | 工具数 |
|:----:|:-----|:---------|:------:|
| A | 知识进 | 豆包聊天 → LevelDB扫描 → 豆包阅读器 → Gateway → Alpha-ID双链记忆 + Obsidian卡片 | 5 |
| B | 能力用 | 对话飞书 → feishu.py → Gateway → 调整个平台能力（身份/记忆/业务/聊天/查询） | 14 |
| C | 统一看 | Ghost.html / Ghost DS → Gateway → 后端 | - |
| D | 桌面伴 | NURO桌宠 → 本地Ollama + 双链记忆 + MCP | 7+ |
| E | 自进化 | Orchestrator → Feed + Capture + Evolution + Obsidian + NURO | 18+ |

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
## 1. 架构全景（7层架构 · 终版定稿）

> 图例：✅ 可用 | ⚠️ 半通 | ❌ 未实现 | 🔄 进行中  
> 参考：`ARCHITECTURE.md`（详细架构）、`SYSTEM_MAP.md`（系统全景+调用链）

### 1.1 七层架构总览

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  L7 知识协同层 — 企业协同 + 知识闭环                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────────────┐   │
│  │ 飞书多维表格  │  │ Obsidian Vault│  │ Ghost DS 电商看板                    │   │
│  │ 全域数据同步  │  │ 8类知识卡片   │  │ (Next.js :3001)                     │   │
│  │ ✅ 飞书Consumer│  │ ✅ 豆包→Obs  │  │ 🔄 全面重写中                        │   │
│  └──────────────┘  └──────────────┘  └──────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────────────────┤
│  L6 业务展现层 — 双模电商 + 展示                                                 │
│  ┌──────────────────────────┐  ┌──────────────────────────────────────────┐     │
│  │ Ghost DS (电商看板)       │  │ Ghost.html (品牌展示)                    │     │
│  │ 🔄 商品/订单/同步/履约    │  │ ✅ 注册+仪表盘+聊天                      │     │
│  │ 17 API路由 + Prisma      │  │ 2,515行 TailwindCSS                      │     │
│  │ 事件总线 + 履约中台       │  │ 2视图(A2A生态+Mindflow)                  │     │
│  └──────────────────────────┘  └──────────────────────────────────────────┘     │
├─────────────────────────────────────────────────────────────────────────────────┤
│  L5 网关管控层 — Gateway :18080 统一入口                                         │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │  human(364L) agent(129L) ecom(249L) flow(236L) net(37L)                │   │
│  │  notify(229L) obsidian_bridge(257L) internal(335L)                      │   │
│  │  中间件: CORS→关联ID→限流→租户提取→Prometheus                            │   │
│  │  代理: httpx连接池+重试+超时+统一信封                                     │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────────────────┤
│  L4 智能调度层 — Alpha-ID Agent调度 + Orchestrator                              │
│  ┌───────────────────────────────────┐  ┌─────────────────────────────────────┐  │
│  │ Alpha-ID 核心 (~35K行/150+文件)   │  │ Orchestrator (:19090)               │  │
│  │ AgentLoop + TwinBrain + 双链记忆  │  │ ⚠️ 骨架（TaskA/ToolB为stub）         │  │
│  │ 多租户引擎 + 风控 + 故障恢复       │  │ ThreadPool + 内存任务存储            │  │
│  │ 事件总线 + A2A协议 + Skill生态    │  │ 网关记忆同步                         │  │
│  └───────────────────────────────────┘  └─────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────────────┤
│  L3 工作流层 — Nebula + Flow                                                   │
│  ┌──────────────────────────┐  ┌──────────────────────────────────────────┐     │
│  │ Nebula (:2002)           │  │ Flow (:3036)                             │     │
│  │ 工作流引擎 + AI网关       │  │ Fastify 前端门户                         │     │
│  │ 7层中间件 + 插件SDK       │  │ 工作流/AID会话/地图/Computer Use          │     │
│  │ 飞书WS + 百度地图 + 抖音  │  │ 无数据库（状态不持久化）                  │     │
│  │ 货源适配器(1688+CJ)       │  │                                          │     │
│  └──────────────────────────┘  └──────────────────────────────────────────┘     │
├─────────────────────────────────────────────────────────────────────────────────┤
│  L2 身份层 — Alpha-ID :8000                                                   │
│  DID生成(Ed25519) + JWT认证 + 双链记忆(AES-256-GCM) + 24个MCP工具 + NURO桌宠    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  L1 感知层 — 数据采集入口                                                       │
│  豆包(LevelDB) → 飞书(WS) → Ghost.html → NURO(本地) → Net-Agent(路由器)        │
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
| L4 | Agent调度层 | ~7.4K+ / 32+文件 | AgentLoop, MasterOrchestrator(24K), AgentFeed, SmartCapture, SelfEvolution, Tenant, Risk, Recovery, A2A | ✅ 基本完整 |
| L3 | 记忆知识库层 | ~1.6K+ | 双链记忆, TwinBrain, ObsidianBridge(10K), Coala记忆, 记忆防御 | ⚠️ Obsidian双向同步已完成 |
| L2 | 身份管理层 | ~35K+ / 150+文件 | DID, 签名, Agent网络, JWT, Profile, 新模块(120K+), CLI, NURO桌宠 | ✅ 最完整 |
| L1 | 用户交互层 | ~7.3K / 9文件 | Ghost.html, 飞书WS, NURO桌宠, 豆包阅读器, 微信适配器, MindFlow代理 | ⚠️ 半通 |

### 1.4 四条对话路径 + 自进化循环

| 路径 | 入口 | 调用链路 | 工具数 | 能做什么 | 缺什么 |
|:----:|:-----|:---------|:------:|:---------|:-------|
| A | Ghost.html | Gateway /v1/human/* → TwinBrain → AgentLoop | 14 | 注册/仪表盘/聊天/身份/记忆 | 知识浏览(P2) |
| B | 飞书 | feishu.py → Gateway /v1/human/chat → AgentLoop | 14 | 全平台能力(身份/记忆/地图/对话) | 知识查询(P2) |
| C | 豆包 | LevelDB → 豆包阅读器 → Gateway /v1/internal/doubao/capture | 5 | 知识自动沉淀到Obsidian | 知识查询接口(P2) |
| D | NURO | 本地 Ollama + 双链记忆 + MCP | 7+ | 桌面悬浮精灵/语音/视觉/观察 | 多模态调优 |
| E | Orchestrator | Feed + Capture + Evolution + Obsidian + NURO | 18+ | 资讯学习/智能采集/自进化/知识同步 | 偏好审视(P2) |

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

#### alphaid/projects/src/alpha_id/ — ~23K+ 行 / 50+ 文件

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
| **orchestrator.py** | **~24K** | **MasterOrchestrator 总调度器** | **✅ 运行中** |
| **feed.py** | **~12K** | **AgentFeed 资讯采集** | **✅ 可用** |
| **smart_capture.py** | **~15K** | **SmartCapture 智能采集** | **✅ 可用** |
| **self_evolution.py** | **~10K** | **SelfEvolution 自进化** | **✅ 可用** |
| **obsidian_bridge.py** | **~10K** | **ObsidianBridge 双向同步** | **✅ 可用** |
| **nuro_bridge.py** | **~7.6K** | **NUROBridge 桌宠连接** | **✅ 可用** |
| **feishu_bridge.py** | **~12K** | **FeishuBridge 飞书集成 + 代码模式（CodeRunner 3后端）** | **✅ 可用** |
| **mcp_tools.py** | **~14K** | **18个 MCP 工具** | **✅ 可用** |
| **orchestrate_cli.py** | **~11K** | **Orchestrator CLI** | **✅ 可用** |
| container.py | ~11K | 依赖注入容器（lazy init） | ✅ 可用 |

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

### 四条使用主线 + 自进化循环

主线A（知识进）: 豆包聊天 -> LevelDB扫描 -> 豆包阅读器 -> Gateway -> Alpha-ID双链记忆 + Obsidian卡片
主线B（能力用）: 对话飞书 -> feishu.py -> Gateway :18080 -> alphaid/nebula/flow
主线C（统一看）: 打开Ghost.html -> fetchDashboard/sendChatMessage -> Gateway -> 后端
主线D（桌面伴）: NURO桌宠 -> 本地Ollama + 双链记忆 + MCP -> 语音/视觉/观察
主线E（自进化）: Orchestrator -> Feed(资讯) + Capture(采集) + Evolution(进化) -> 持续学习

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

> **版本**: Web4.0 AtoA OS v5.0 | **三层终极堆栈**: 理念层(Denny) → 系统中枢(AlphaID) → 底层网络(Ghost AtoA)

### 2.1 三层终极堆栈

```
┌─────────────────────────────────────────────────────────────────┐
│  理念层 (外置大脑)                                                │
│  Denny AI ── 人机共生哲学、智能体行为规范、商业伦理               │
├─────────────────────────────────────────────────────────────────┤
│  系统中枢 (Alpha-ID)                                             │
│  个人终身DID身份 + 双链记忆 + Agent生态 + Skill市场               │
│  ~35K+ 行 Python / 150+ 文件                                     │
├─────────────────────────────────────────────────────────────────┤
│  底层网络 (Ghost AtoA)                                           │
│  Gateway + Nebula + Orchestrator + Net-Agent + Feishu Bot        │
│  + Ghost DS + 监控栈                                             │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Docker 运行状态

| 服务 | 端口 | 状态 | 说明 |
|:-----|:----:|:----:|:-----|
| Alpha-ID | 8000 | ✅ 运行 | 身份 + 双链记忆 + AgentLoop |
| Gateway | 18080 | ✅ 运行 | 统一网关 + 9 路由 |
| Nebula | 2002 | ✅ 运行 | 工作流引擎 + 7层中间件 |
| Orchestrator | 19090 | ✅ 运行 | 任务调度 (骨架阶段) |
| Net-Agent | 18180 | ✅ 运行 | 路由器管理 |
| Ghost DS | 3004 | ✅ 运行 | 电商看板 (Next.js) |
| MindFlow | 3036 | ✅ 运行 | 前端门户 |
| Feishu Bot | 通过 GW | ⚠️ Unhealthy | 飞书 4合1 通道 |
| PostgreSQL | 5432 | ✅ 运行 | 主数据库 |
| Redis | 6379 | ✅ 运行 | 缓存 + 事件总线 |
| Prometheus | 9090 | ✅ 运行 | 指标采集 |
| Grafana | 3000 | ✅ 运行 | 可视化看板 |

> 12 容器运行中，2 个 Unhealthy (Feishu Bot + 可能其他)

### 2.3 服务功能度评分

| 服务 | 功能度 | 测试覆盖 | 状态 |
|:-----|:------:|:--------:|:----:|
| Alpha-ID | 95% | 839+ 用例 | ✅ 生产可用 |
| Gateway | 95% | 22 用例 | ✅ 生产可用 |
| Nebula | 85% | 153 用例 | ✅ 生产可用 |
| Ghost DS | 90% | 0 用例 | ⚠️ 功能完整，缺测试 |
| Net-Agent | 60% | 0 用例 | ⚠️ 基础功能可用 |
| Orchestrator | 20% | 0 用例 | ⚠️ 骨架完成，核心待实现 |
| Feishu Bot | 80% | 0 用例 | ⚠️ 功能可用，Docker 不健康 |
| MindFlow | 70% | 0 用例 | ⚠️ 前端可用，部分后端待完善 |

### 2.4 三条主线

| 主线 | 入口 | 调用链路 | 功能 |
|:-----|:-----|:---------|:-----|
| A | 豆包 | LevelDB → 豆包阅读器 → Gateway → Alpha-ID + Obsidian | 知识自动沉淀 |
| B | 飞书 | WebSocket → Gateway → Alpha-ID / Nebula / Net-Agent | 总对话助理，调全平台能力 |
| C | Ghost DS | 浏览器 → Next.js → Prisma → PostgreSQL | 电商看板 + 订单/产品管理 |
| D | Ghost.html | 浏览器 → Gateway → Alpha-ID | 注册 + 仪表盘 + 聊天 |
| E | NURO | 本地 Ollama + 双链记忆 + MCP | 桌面精灵 (纯本地) |
| F | Orchestrator | Redis Streams → 任务队列 → 各服务 | 自动化调度 (待实现) |

### 2.5 核心现状一句话

代码总量 ~55K+ 行，12 个 Docker 容器运行中。关键路径已打通：飞书→Gateway→全平台、Ghost DS 电商全功能、豆包→Obsidian 知识沉淀、NURO 独立运行。当前最大短板：Orchestrator 核心调度未实现、Ghost DS 无测试、事件总线休眠、Feishu Bot Docker 不健康。需要的是打磨连通而不是加功能。

---
## 3. 飞书机器人（总对话助理） -- 现状->目标->路径

### 3.1 现状

**架构**: 飞书 Bot 作为独立服务部署 (ghost-main/feishu-bot/)，通过 WebSocket + HTTP 长轮询双通道接入。

| 能力 | 状态 | 说明 |
|:-----|:----:|:------|
| 接收飞书消息（WebSocket） | ✅ 正常 | 双通道：WebSocket 首选，HTTP 轮询备选 |
| 消息路由到 Gateway | ✅ 正常 | `/webhook/shoplazza` 端点 |
| 4合1 模式 (Chat/Execute/Notify/Approve) | ✅ 正常 | 通过消息内容判断模式 |
| 凭证管理 | ⚠️ 待改进 | 硬编码凭证需移入环境变量 |
| Docker 健康 | ⚠️ Unhealthy | 容器运行但不健康，需排查 |

**当前代码路径：**
```
飞书消息 -> feishu_bot (WebSocket/HTTP 双通道)
         -> httpx POST Gateway :18080 /webhook/shoplazza
         -> Gateway -> Alpha-ID :8000 (TwinBrain + AgentLoop)
         -> Gateway -> Nebula :2002 (工作流/地图/审批)
         -> Gateway -> Net-Agent :18180 (路由器管理)
         -> 返回结果 -> 飞书
```

**已清理：**
- alphaid/feishu_bot/ 旧目录已删除 (与 ghost-main/feishu-bot/ 重复)
- callback_server.py 旧引擎路径已删除
- 飞书不再走旧 workflow 引擎，直接走 Gateway

### 3.2 在系统中的位置

```
飞书用户
    │
    ▼
飞书开放平台
    │
    ├── WebSocket 事件 / HTTP 回调
    │       │
    │       ▼
    │   Gateway (:18080) ── /webhook/shoplazza
    │       │
    │       ▼
    │   Feishu Bot 服务
    │       │
    │       ├── [Chat] → 提取工作上下文 → Gateway → Alpha-ID
    │       ├── [Execute] → 执行工具 → 返回结果
    │       ├── [Notify] → 推送通知到飞书
    │       └── [Approve] → 审批确认 → 更新状态
    │       │
    ▼       ▼
飞书用户收到响应 / 状态更新
```

飞书是你的总对话助理，通过 Gateway 跟整个平台对接。你想做什么（查身份、查记忆、地图导航、执行业务、通用聊天）直接对话就行。

### 3.3 目标形态

| 能力 | 目标 | 优先级 |
|:-----|:-----|:------:|
| 身份查询 | 飞书对话查询 DID 信息 | P0 ✅ |
| 记忆查询 | 飞书对话查询历史记忆 | P0 ✅ |
| 地图导航 | 飞书对话搜索地点/路线 | P0 ✅ |
| 业务工具 | 电商订单/产品管理 | P1 |
| 知识查询 | 查询 Obsidian 知识库 | P2 |
| 代码执行 | CodeRunner 3 后端切换 | P1 |

| 步骤 | 做什么 | 优先级 |
|:-----|:-------|:------:|
| 1 | Gateway 加 /webhook 路由 | P0 ✅ |
| 2 | 飞书 Bot 独立部署 | P0 ✅ |
| 3 | 双通道 (WS + HTTP) | P0 ✅ |
| 4 | 4合1 模式 (Chat/Execute/Notify/Approve) | P0 ✅ |
| 5 | 凭证移入环境变量 | P1 |
| 6 | 修复 Docker Unhealthy | P1 |

## 4. 豆包管道 -- 现状->目标->路径

### 4.1 现状（已接入 ✅）

豆包内容已通过 `ghost-main/doubao_reader/` 接入系统。LevelDB 扫描 → 精炼 → Obsidian 写入全自动。

| 组件 | 文件 | 行数 | 功能 | 状态 |
|:-----|:-----|:----:|:-----|:----:|
| LogReader | `log_reader.py` | 239 | 扫描豆包桌面 LevelDB | ✅ |
| KnowledgeRefiner | `knowledge_refiner.py` | 204 | LLM 精炼对话内容 | ✅ |
| ObsidianWriter | `obsidian_writer.py` | 208 | 写入 Obsidian MD 文件 | ✅ |
| ObsidianOrganizer | `obsidian_organizer.py` | 306 | 自动整理 (标签/链接/日报) | ✅ |
| ReaderDaemon | `reader_daemon.py` | 98 | 60秒间隔守护进程 | ✅ |

**数据流**:
```
豆包桌面 LevelDB
    │
    ▼
LogReader (每60秒扫描)
    │
    ▼
KnowledgeRefiner (LLM精炼)
    │
    ▼
Gateway /v1/internal/doubao/capture
    │
    ▼
Alpha-ID 双链记忆 (知链) + Obsidian Vault
```

### 4.2 目标形态

| 能力 | 目标 | 优先级 |
|:-----|:-----|:------:|
| 自动知识沉淀 | 豆包对话 → Obsidian 知识卡片 | ✅ 已实现 |
| 知识查询 | 飞书/Ghost 查询 Obsidian | P1 |
| 知识分类 | LLM 自动分类 + 交叉链接 | P1 |
| 去重/摘要 | 自动去重 + 生成摘要 | P2 |

### 4.3 衔接关系

豆包在整个系统中是**知识入口**。你跟豆包聊天的内容，由豆包自身 LLM 整理后写入 Obsidian。沉淀的知识可以被飞书和 Ghost.html 查询调用。

```
豆包 -> (自身整理) -> Obsidian知识库 -> 飞书/Ghost查询
```

> 豆包管进（知识沉淀），飞书调用（平台能力），Ghost管看（统一展示），NURO陪伴（本地AI）。数据通过 Gateway 路由到后端。

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
路径: `D:\MW\alphaid\projects\src\alpha_id\templates\ghost.html`

| 指标 | 值 |
|:-----|:---:|
| 行数 | 2515行 |
| UI | TailwindCSS编译 两视图架构（A2A 生态区 + Mindflow 协作台） |
| 真实API调用 | 注册/健康检查/记忆统计 接通 |
| 注册/登录 | ✅ DID + 短信 + 人脸 + 落库 |
| 对话 | 界面有 + ChatGPT 记忆导入 |

注册链路已端到端跑通，工作台统计数据从 Gateway 实时拉取。

> 注：已删除重复的 4 个 Mindflow 面板，workbenchView 聚焦 A2A 生态，mindflowView 为唯一人机协作台。

> 注意：Ghost.html 是品牌展示 + 注册入口，**不是**电商看板。电商看板已迁移至 Ghost DS (Next.js :3004)。

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
架构: 九层路由 — human / agent / internal / net / webhook / sync / cron / orders / products

**当前路由**:
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
| webhook | /webhook/shoplazza | feishu-bot | ✅ |
| sync | /api/sync/* | DS / Nebula | ✅ |
| cron | /api/cron/sync | DS | ✅ |
| orders | /api/orders/* | DS | ✅ |
| products | /api/products/* | DS | ✅ |

基础设施: CORS白名单 / Correlation ID / 滑动窗口限流(5/60s) / 统一信封 {success,data,ts,request_id} / 指标收集

目标: 九层路由全通(已完成) + 电商路由覆盖完整(已完成) + 内容审核(P2) + 监控Trace(P2)

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
## 10. Nebula 工作流 -- 现状->目标->路径

路径: `D:\MW\nebula\src\mindflow_map\` 67文件 / 7,708行
入口: `mindflow_map/main.py`
核心: 工作流引擎 + AI网关(intent/llm/circuit_breaker) + 7层中间件 + 插件SDK(@tool装饰器) + 自动化(抖音/Shopify)
飞书已改走Gateway Nebula退回纯工作流引擎
目标: 飞书走Gateway Nebula专注工作流/地图/自动化

| 组件 | 路径 | 行数 | 状态 |
|:-----|:-----|:----:|:----:|
| FastAPI 主应用 | `main.py` | ~200 | ✅ |
| 路由 (7模块) | `routes/` | ~1,800 | ✅ 飞书/Webhook/地图/工作流/自动化/健康/流式 |
| 中间件 (7层) | `middleware/` | ~800 | ✅ 审计/限流/租户/策略/缓存/日志/异常 |
| AI 网关 | `ai/` | ~600 | ✅ intent/llm/circuit_breaker/fallback/health |
| 插件 SDK | `plugins/` | ~200 | ✅ registry+@tool装饰器 |
| 工作流引擎 | `workflows/engine.py` | ~300 | ⚠️ 仅地图导航 |
| 自动化 | `automation/` | ~400 | ⚠️ 抖音/Shopify/脚本生成 |
| 百度地图 | `tools/baidu_map.py` | ~200 | ✅ 搜索/路线/天气 |

### 10.1 七层中间件栈

| 层级 | 中间件 | 功能 |
|:-----|:-------|:-----|
| L1 | AuditMiddleware | 全链路审计日志 |
| L2 | RateLimitMiddleware | IP + 租户级限流 |
| L3 | TenantMiddleware | 租户上下文注入 |
| L4 | PolicyMiddleware | 策略引擎 (RBAC/ABAC) |
| L5 | CacheMiddleware | 响应缓存 + ETag |
| L6 | LoggingMiddleware | 结构化日志 |
| L7 | ExceptionMiddleware | 统一异常处理 |

### 10.2 适配器

| 适配器 | 功能 | 状态 |
|:-------|:-----|:----:|
| Shoplazza | 产品/订单/库存同步 | ✅ |
| 1688 | 货源接入 | ⚠️ 待完善 |
| 工作流模板 | YAML 定义 | ⚠️ 仅地图 |

### 10.3 衔接关系

Nebula是**工作流引擎**，负责工作流编排、思维导图、审批流、地图导航等业务。它通过Gateway与前端和Alpha-ID对接，不直接对外暴露。

前端/Gateway -> Nebula :2002 -> 工作流/地图/审批
                    -> Shoplazza 适配器 -> 产品/订单/库存同步

| 步骤 | 做什么 | 优先级 |
|:-----|:-------|:------:|
| 1 | feishu.py改调Gateway | P0 ✅ |
| 2 | 1688货源适配器完善 | P1 |
| 3 | 工作流模板引擎完善 | P1 |
| 4 | 电商履约引擎完善 | P1 |

---
## 11. Ghost DS 电商看板 -- 现状->目标->路径

路径: `D:\MW\DS\` Next.js 14 + Prisma + PostgreSQL
端口: 3004
核心: 电商数据管理 (产品/订单/库存/同步/履约)

| 组件 | 路径 | 状态 |
|:-----|:-----|:----:|
| 前端页面 | `src/app/` | ✅ App Router |
| API 路由 | `src/app/api/` | ✅ 17 路由 |
| 组件 | `src/components/` | ✅ FulfillModal/ProductAiDialog |
| Prisma 模型 | `prisma/schema.prisma` | ✅ 4 模型 |
| 数据库 | PostgreSQL | ✅ 运行中 |

**Prisma 数据模型**:
- `Shop` — 店铺 (tenantId + storeMode + platform + shopId)
- `Product` — 产品 (tenantId + shopId + title + price + inventory + variants)
- `Order` — 订单 (tenantId + shopId + productId + total + status + customer)
- `SyncLog` — 同步日志 (tenantId + resource + action + status + startedAt + completedAt)

**API 路由**:
| 路由 | 方法 | 功能 |
|:-----|:-----|:-----|
| `/api/shop` | GET/POST | 店铺注册/列表 |
| `/api/products` | GET/POST/PUT/DELETE | 产品 CRUD |
| `/api/orders` | GET | 订单列表 |
| `/api/orders/[id]/fulfill` | POST | 订单履约 |
| `/api/sync` | POST | 触发数据同步 |
| `/api/cron/sync` | POST | 定时同步 |
| `/api/stats` | GET | 统计看板 |
| `/api/health` | GET | 健康检查 |

### 11.1 衔接关系

Ghost DS 是**电商业务展现层**，通过 Next.js 前端 + Prisma ORM 直接操作 PostgreSQL。它通过 Gateway 与 Nebula 通信获取货源数据，通过 Gateway 与 Alpha-ID 通信获取身份认证。

用户浏览器 -> Ghost DS :3004 -> Prisma -> PostgreSQL
                       -> Gateway -> Nebula :2002 (货源同步)
                       -> Gateway -> Alpha-ID :8000 (身份认证)

### 11.2 中间步骤

| 步骤 | 做什么 | 优先级 |
|:-----|:-------|:------:|
| 1 | 电商 MVP 场景闭环 | P0 |
| 2 | 自动铺货任务 | P1 |
| 3 | 双渠道分发 | P1 |
| 4 | 飞书协同对接 | P2 |

---
## 12. 七层架构代码映射（完整版）

> 详细到文件级别的映射见 §1.5 完整组件清单。本节为精简速查版。

### L1 感知与接入层
| 组件 | 路径 | 行数 | 状态 |
|:-----|:-----|:----:|:----:|
| Docker Compose | `docker-compose.yml` | - | ✅ 12 服务编排 |
| 豆包 LevelDB | `ghost-main/doubao_reader/` | 1,055 | ✅ 自动扫描 |
| 飞书 WebSocket | `ghost-main/feishu-bot/` | ~300 | ⚠️ 双通道可用 |
| 路由器 HTTP | `ghost-main/net_agent_server/` | ~2K | ✅ 远程管理 |
| 开发工具 | Gateway /v1/internal/* | - | ✅ 采集入口 |

### L2 身份与权限层 (~35K+ 行)
| 组件 | 路径 | 行数 | 状态 |
|:-----|:-----|:----:|:----:|
| Alpha-ID | `alphaid/projects/src/` | ~35K | ✅ 身份+记忆+Agent |
| DID 生成 | `alpha_id/did.py` | ~1,200 | ✅ Ed25519 |
| JWT 认证 | `auth/` | 295 | ✅ HS256+HKDF |
| 双链记忆 | `core/dual_chain.py` | 413 | ✅ 私链+知链 |
| Net-Agent | `ghost-main/net_agent_server/` | ~2K | ⚠️ 60% 完成 |

### L3 工作流引擎层 (~7.7K 行)
| 组件 | 路径 | 行数 | 状态 |
|:-----|:-----|:----:|:----:|
| Nebula | `nebula/src/mindflow_map/` | 7,708 | ✅ 工作流+审批+地图 |
| 7层中间件 | `middleware/` | ~800 | ✅ 审计/限流/租户/策略/缓存/日志/异常 |
| Shoplazza 适配器 | `routes/` | - | ✅ 产品/订单/库存 |
| 1688 适配器 | `routes/` | - | ⚠️ 待完善 |

### L4 智能调度层
| 组件 | 路径 | 行数 | 状态 |
|:-----|:-----|:----:|:----:|
| Orchestrator | `orchestrator/` | ~3K | ⚠️ 20% 骨架 |
| Redis Streams | Docker Redis | - | ⚠️ 架构已定义，休眠 |
| EventBus | `core/event_bus.py` | 261 | ✅ 已写未接入 |

### L5 统一网关层 (1,857 行)
| 组件 | 路径 | 行数 | 状态 |
|:-----|:-----|:----:|:----:|
| Gateway | `ghost-main/gateway/` | 1,857 | ✅ 9 路由+代理+重试 |
| 路由 | `routes/` | 777 | ✅ human/agent/internal/net/webhook/sync/cron/orders/products |
| 代理服务 | `services/proxy.py` | 111 | ✅ httpx+重试+超时 |
| 中间件 | `middleware/` | 72 | ✅ CORS+限流+关联ID |

### L6 业务展现层
| 组件 | 路径 | 行数 | 状态 |
|:-----|:-----|:----:|:----:|
| Ghost DS | `DS/src/` | ~5K TS | ✅ 90% 电商看板 |
| Next.js 前端 | `DS/src/app/` | - | ✅ App Router |
| Prisma ORM | `DS/prisma/` | - | ✅ 4 模型 |
| Feishu Bot | `ghost-main/feishu-bot/` | ~300 | ⚠️ 80% Docker Unhealthy |

### L7 知识协同层
| 组件 | 路径 | 行数 | 状态 |
|:-----|:-----|:----:|:----:|
| Obsidian Vault | 本地 D:\Obsidian | - | ✅ 知识沉淀 |
| 豆包阅读器 | `ghost-main/doubao_reader/` | 1,055 | ✅ LevelDB→Obsidian |
| Gateway Obsidian | `services/obsidian.py` | 184 | ✅ 写入+搜索+整理 |
| 飞书多维表格 | 待接入 | - | ⚠️ 概念阶段 |
| Ghost DS 看板 | `DS/src/app/stats/page.tsx` | - | ✅ 统计可视化 |

---
## 13. 架构审查 -- 做对的 vs 做错的

### 13.1 做对了的
| # | 决策 | 为什么对 |
|---|------|---------|
| 1 | Alpha-ID身份根 did.py+signer.py | 所有数据归一个身份是基石 |
| 2 | Gateway统一入口 9路由 | 架构清晰，限流+CORS+统一信封 |
| 3 | 双链记忆私链+知链分离 | 隐私不出本地 |
| 4 | 三层终极堆栈 (理念层/系统中枢/底层网络) | 战略清晰，分层解耦 |
| 5 | 七层架构 (L1感知→L7知识协同) | 每层职责明确，可独立迭代 |
| 6 | 飞书总对话助理 (4合1模式) | 自然语言调用全平台能力 |
| 7 | 豆包LevelDB扫描方案 | 零API依赖，离线工作 |
| 8 | Ghost DS 电商看板 (Next.js+Prisma) | 现代化技术栈，功能完整 |
| 9 | 7层中间件栈 (Nebula) | 审计/限流/租户/策略/缓存/日志/异常 |
| 10 | 故障恢复(recovery.py)+可观测性(observability.py) | 生产级稳定性 |
| 11 | 行动引擎(action_engine) | approval+adapter模式解耦 |
| 12 | Docker Compose 12服务编排 | 一键启动，开发生产一致 |

### 13.2 做错了的(已修正)
| # | 错误 | 表现 | 纠正 | 状态 |
|---|------|------|------|:----:|
| 1 | 飞书走错路 | feishu.py→workflows/engine只地图 | 飞书→Gateway→LLM分流 | ✅ 已修正 |
| 2 | alphaid入口混乱 | 4入口(api/daemon/mcp/shortdrama)+feishu_bot重复 | 只留api.py+aid_mcp_server.py | ✅ 已修正 |
| 3 | Ghost假官网 | 3507行0次fetch | 加fetch调Gateway | ✅ 已修正 |
| 4 | 豆包无入口 | 核心输入进不了Ghost | 豆包→LevelDB→阅读器→Gateway→Obsidian | ✅ 已修正 |
| 5 | 飞书两套重复代码 | nebula/feishu+alphaid/feishu_bot | 只保留nebula | ✅ 已修正 |
| 6 | flow/api注册未启动 | 注册链路代码完整但路由不通 | 注册迁移至alphaid :8000 | ✅ 已修正 |
| 7 | 架构文档过时 | 6层架构，说Orchestrator是in-process | 更新为7层架构 | ✅ 已修正 |
| 8 | 电商看板位置错误 | 说电商在Ghost.html | 迁移至Ghost DS (Next.js) | ✅ 已修正 |

### 13.3 待处理
| # | 问题 | 优先级 |
|---|------|:------:|
| 1 | 微信适配器写了没接 | P2 |
| 2 | FulfillModal绕过Nebula直接写DB | P0 |
| 3 | DS重复路由定义 | P0 |
| 4 | 配置错误 (Gateway/DS/Orchestrator .env) | P0 |
| 5 | Feishu Bot Docker Unhealthy | P1 |

---
## 14. P0 任务清单（立即执行 · Phase 0 止血）

> 目标：修复 7 个已知 bug/配置错误，止血为先。

| # | 任务 | 影响 | 状态 |
|:---|:------|:------|:----:|
| 1 | 修复 FulfillModal 绕过 Nebula 直接写 DB | 订单履约数据不一致 | ⚠️ 待做 |
| 2 | 合并 DS 重复路由 (/api/shop 两处定义) | API 冲突 | ⚠️ 待做 |
| 3 | 修正 Gateway .env 端口配置 (DS 应为 3004 不是 3001) | 代理失败 | ⚠️ 待做 |
| 4 | 修正 DS .env PLATFORM_URL | 前端链接错误 | ⚠️ 待做 |
| 5 | 修复 Feishu Bot Docker Unhealthy | 飞书消息不处理 | ⚠️ 待做 |
| 6 | 修正 Nebula .env Redis 密码配置 | 缓存/事件总线不可用 | ⚠️ 待做 |
| 7 | 修正 Orchestrator Dockerfile 端口暴露 | 服务不可达 | ⚠️ 待做 |

---
## 15. P1 任务清单（本周 · Phase 1 连通）

> 目标：修复 4 条断裂的事件链，让系统真正连通。

| # | 任务 | 影响 | 状态 |
|:---|:------|:------|:----:|
| 1 | 连接 Redis Streams 事件总线 (调用 startConsuming) | 服务间异步通信 | ⚠️ 待做 |
| 2 | 修复飞书 → Feishu Bot → Gateway 链路 | 飞书消息无法到达后端 | ⚠️ 待做 |
| 3 | 实现 Ghost DS → Orchestrator 自动铺货任务 | 自动化铺货不触发 | ⚠️ 待做 |
| 4 | 实现 Feishu Bot → 飞书通知推送 | 履约/审批通知不发 | ⚠️ 待做 |
| 5 | 飞书凭证移入环境变量 | 安全风险 | ⚠️ 待做 |
| 6 | Obsidian 知识查询接口 | 飞书/Ghost 无法查知识 | ⚠️ 待做 |

---
## 16. P2 任务清单（两周内 · Phase 2 加固 + Phase 3 完善）

### Phase 2 加固

| # | 任务 | 说明 |
|:---|:------|:-----|
| 1 | Ghost DS 测试覆盖 | 当前 0 测试用例 |
| 2 | Orchestrator 核心调度实现 | 当前骨架 20% |
| 3 | 内容审核中间件 | Gateway 做 |
| 4 | 限流中间件升级 | Token Bucket |
| 5 | 监控 Trace | 链路追踪 |
| 6 | 多租户隔离 | 多用户准备 |

### Phase 3 完善

| # | 任务 | 说明 |
|:---|:------|:-----|
| 7 | A2A 真实网络通信 | HTTP/WS 升级 |
| 8 | NURO 多模态优化 | MiniCPM-o 调优 |
| 9 | 飞书多维表格对接 | L7 知识协同 |
| 10 | 1688 货源适配器完善 | Nebula 货源接入 |
| 11 | Ghost.html 知识浏览 | 查询 Obsidian 卡片 |
| 12 | 电商 MVP 场景闭环 | 铺货→售卖→履约→数据回传 |

---
## 17. 根目录清理计划

| 文件/目录 | 处理 |
|:----------|:-----|
| GHOST.md | 保留 — 项目宪法 |
| ARCHITECTURE.md | 保留 — 架构设计文档 |
| PROJECT_STATUS_REPORT.md | 保留 — 项目状态快照 |
| SYSTEM_MAP.md | 保留 — 系统全景图 |
| WORK_LOG.md | 保留 — 工作日志 |
| DECISIONS.md | 保留 — 决策记录 |
| 1.md.md | 保留 — 战略定位来源 |
| 2.md.md | 保留 — 战略定位来源 |
| README.md | 保留 |
| archive/md_old/ | 保留不动 |
| ARCHITECTURE_DIAGRAM.md | 已整合进 GHOST.md → 可删除 |
| ARCHITECTURE_REVIEW.md | 已整合进 GHOST.md → 可删除 |
| FRAMEWORK.md | 已整合进 GHOST.md → 可删除 |
| TRUTH.md | 已整合进 GHOST.md → 可删除 |

---
## 18. 已确认决策（项目宪法）

以下决策是项目基石，后续所有开发必须遵循，不反复确认：

| 决策 | 来源 | 影响 |
|:-----|:------|:-----|
| 项目定位 = Web4.0 AtoA 全域自主智能体操作系统 | 2.md.md / 1.md.md | 所有技术选型围绕此定位 |
| 三层终极堆栈: 理念层(Denny) → 系统中枢(AlphaID) → 底层网络(Ghost) | 2.md.md | 架构分层依据 |
| 七层系统架构: L1感知→L2身份→L3工作流→L4调度→L5网关→L6业务→L7知识 | 1.md.md | 服务部署/开发分层 |
| 电商 = MVP 场景，非最终形态 | 2.md.md | Ghost DS 是验证工具，非最终产品 |
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
| 货源全开放：官方货源 + 用户Skill私接双向兼容 | 1.md.md | 供应链层设计 |
| 双模电商：集市(拼单) + 独立站(SaaS) | 1.md.md | Ghost DS storeMode 设计 |
| 严禁二清：不自建资金池 | 1.md.md | 支付合规红线 |

---
## 19. 启动指南

### Docker Compose（推荐，12 服务一键启动）

```bash
# 开发环境
docker compose up -d

# 生产环境
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

**服务映射**:
| Docker 服务 | 端口 | 对应 |
|:-----------|:-----|:-----|
| alphaid | 8000 | Alpha-ID |
| gateway | 18080 | Gateway |
| nebula | 2002 | Nebula |
| orchestrator | 19090 | Orchestrator |
| net-agent | 18180 | Net-Agent |
| ghost-ds | 3004 | Ghost DS |
| mindflow | 3036 | MindFlow |
| feishu-bot | - | Feishu Bot |
| postgres | 5432 | PostgreSQL |
| redis | 6379 | Redis |
| prometheus | 9090 | Prometheus |
| grafana | 3000 | Grafana |

### 手动启动（开发调试）

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

# 4. Ghost DS (电商看板)
cd D:\MW\DS
npm run dev  # Next.js :3004

# 5. Orchestrator (任务调度)
cd D:\MW\orchestrator
python -m uvicorn app:app --host 0.0.0.0 --port 19090
```

### 验证

| 验证项 | 命令/URL | 期望 |
|:-------|:---------|:-----|
| Gateway | http://localhost:18080/v1/internal/health | ✅ 200 |
| Alpha-ID | http://localhost:8000/api/health | ✅ 200 |
| Nebula | http://localhost:2002/health | ✅ 200 |
| Ghost DS | http://localhost:3004/api/health | ✅ 200 |
| Orchestrator | http://localhost:19090/health | ✅ 200 |
| MindFlow | http://localhost:3036/health | ✅ 200 |
| Ghost.html | 浏览器打开 alphaid/projects/src/alpha_id/templates/ghost.html | 注册/仪表盘/聊天 |
| 飞书 | 发消息给飞书机器人 | 全平台能力响应 |
| NURO | `python -m entrypoints.cli` 或 `aid-daemon` | 桌面精灵启动 |
| 豆包 | 自动扫描（Gateway启动后自动启用） | LevelDB→Obsidian |
| Prometheus | http://localhost:9090 | ✅ 200 |
| Grafana | http://localhost:3000 | ✅ 200 |

### NURO 桌宠单独启动

```bash
cd D:\MW\alphaid\projects
python -m entrypoints.cli          # 正常启动
python -m entrypoints.cli --check  # 环境检测
install_deskpet.bat                # 一键安装
```

---
## 20. 参考文档 & 旧档说明

### 项目核心文档（必须同步阅读）

| 文档 | 定位 | 说明 |
|:-----|:-----|:-----|
| `GHOST.md` | 项目宪法 | 本文档，项目基调、架构、任务清单、决策 |
| `ARCHITECTURE.md` | 架构设计 | 七层架构详细设计、服务详解、数据流、认证链 |
| `SYSTEM_MAP.md` | 系统全景 | 5条调用链、事件流、配置审计、优化路线图 |
| `PROJECT_STATUS_REPORT.md` | 状态快照 | Docker状态、服务功能度评分、已知bug |
| `WORK_LOG.md` | 工作日志 | 每次会话的审计发现和决策记录 |
| `DECISIONS.md` | 决策记录 | 所有已确认的架构决策（D-20260804-*） |
| `1.md.md` | 战略来源 | AlphaID跨境全链路一体化平台架构复盘 |
| `2.md.md` | 战略来源 | 从AI外置大脑到Web4.0 AtoA全域智能体 |

### 旧文档

旧文档在 `archive/md_old/` 保留不动: ARCHITECTURE_DIAGRAM.md ARCHITECTURE_REVIEW.md FRAMEWORK.md TRUTH.md PROJECT_AUDIT.md AID_FULL_INTEGRATION.md 繁星计划申请材料.md

根目录保留: GHOST.md + ARCHITECTURE.md + SYSTEM_MAP.md + PROJECT_STATUS_REPORT.md + WORK_LOG.md + DECISIONS.md + README.md + archive/

详细组件文档:
- NURO桌宠: `alphaid/projects/docs/nuro-desktop-pet.md`
- Ghost.html前端: `alphaid/projects/docs/ghost-frontend.md`
- 豆包阅读器: `ghost-main/docs/doubao-reader.md`

---
## 变更记录
| 日期 | 版本 | 变更 |
|:-----|:----|:------|
| 2026-07-27 | 4.1 | 新增8个模块: Orchestrator(24K) SmartCapture(15K) AgentFeed(12K) SelfEvolution(10K) ObsidianBridge(10K) NUROBridge(7.6K) FeishuBridge(8.6K) MCPTools(14K) 全部验证跑通 架构图+组件表+启动指南更新 |
| 2026-07-27 | 4.0 | 全面大修:版本升至4.0 修正全部行数(Gateway 1,857L/17F, Alpha-ID 32.6K/141F, Nebula 7.7K/67F) P0-1~P0-4标记DONE 新增§8 NURO桌面精灵(1,719L/7F) 新增§9豆包知识管道(1,055L/5F) 架构图加入NURO+豆包 启动指南更新为实际命令 |
| 2026-07-25 | 3.0 | 全面审计:修正全部行数/路径/状态标记 新增§1.5完整组件清单 修复Mermaid→ASCII框图 统一✅⚠️❌ |
| 2026-07-25 | 2.0 | 完整重写:整合5份旧文档+全部审计+今日决策 每组件写现状→目标→路径 |
| 2026-07-25 | 1.0 | 初始整合版 |


