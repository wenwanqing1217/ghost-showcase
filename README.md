<div align="center">

<!-- ═══════════════════════════════════════════════════════════════════ -->
<!-- 动态标题 — Typing SVG                                               -->
<!-- ═══════════════════════════════════════════════════════════════════ -->
<h1>
  <img src="https://readme-typing-svg.demolab.com?font=Inter&weight=600&size=32&duration=3000&pause=1000&color=A78BFA&center=true&vCenter=true&width=600&lines=%F0%9F%91%BB+Ghost+%E2%80%94+AI+Agent+Matrix;One+Identity%2C+All+Agents;Digital+You%2C+Everywhere" />
</h1>

<!-- ═══════════════════════════════════════════════════════════════════ -->
<!-- 徽章墙                                                              -->
<!-- ═══════════════════════════════════════════════════════════════════ -->
<p>
  <!-- CI / 构建 -->
  <img src="https://img.shields.io/github/actions/workflow/status/wenwanqing1217/monorepo/ci.yml?branch=master&style=flat-square&label=CI" alt="CI" />
  <!-- License -->
  <img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square" alt="License: MIT" />
  <!-- 测试数 -->
  <img src="https://img.shields.io/badge/tests-1223%20passing-brightgreen?style=flat-square" alt="Tests" />
  <!-- 语言 -->
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&style=flat-square&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript&style=flat-square&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/Next.js-14-000000?logo=nextdotjs&style=flat-square&logoColor=white" alt="Next.js" />
  <!-- 框架 -->
  <img src="https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&style=flat-square&logoColor=white" alt="FastAPI" />
  <!-- 身份标准 -->
  <img src="https://img.shields.io/badge/DID-Ed25519-7C3AED?style=flat-square" alt="DID" />
  <!-- 部署 -->
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&style=flat-square&logoColor=white" alt="Docker" />
</p>

<p>
  <strong>让每个 AI Agent 都认识你是谁。</strong><br />
  <em>One identity. All agents. Every channel.</em>
</p>

<p>
  <a href="#quickstart">🚀 快速启动</a> ·
  <a href="#architecture">🏗️ 架构</a> ·
  <a href="#features">✨ 功能</a> ·
  <a href="#projects">📦 项目</a> ·
  <a href="#roadmap">🗺️ 路线图</a> ·
  <a href="#contributing">🤝 贡献</a> ·
  <a href="docs/">📖 文档</a>
</p>

</div>

---

<!-- ═══════════════════════════════════════════════════════════════════ -->
<!-- 一句话定位                                                          -->
<!-- ═══════════════════════════════════════════════════════════════════ -->

> **Ghost 不是另一个 AI 助理。** 它是坐在所有 AI 工具之上的 **Ghost Layer** — 一个 AI Agent 应用矩阵。
>
> 当越来越多的 AI 工具涌现，每次使用新工具都像遇到陌生人——你要重新介绍自己。Ghost 终结这件事：**一次注册，所有 Agent 都认识你。**

---

## 🚀 Quickstart <a name="quickstart"></a>

```bash
# 克隆（含子模块）
git clone --recurse-submodules https://github.com/wenwanqing1217/monorepo.git
cd monorepo

# 一键启动全部服务（PostgreSQL + AlphaID + Nebula + DS）
cp .env.example .env          # 编辑 .env 填入你的 API Key
docker compose up -d

# 打开浏览器 → 访问本地服务
#   Alpha-ID (身份层)  → http://localhost:8000
#   Nebula (执行层)    → http://localhost:2002
#   DS (电商后端)      → http://localhost:3004
```

或者单独启动某个模块：

```bash
# 身份层（核心 — PyPI 已发布）
pip install alpha-id
aid init                        # 初始化数字身份
aid detect                      # 扫描本机数字痕迹
aid profile show                # 查看数字画像

# 身份层（源码）
cd alphaid/projects
pip install -e ".[dev]"
uvicorn src.main:app --reload --port 8000

# 执行层
cd nebula
pip install -e ".[dev]"
uvicorn mindflow_map.main:app --reload --port 2002

# 电商后端
cd DS
npm install && npm run dev      # → :3004
```

---

## 🏗️ Architecture <a name="architecture"></a>

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                     🌐 Ghost.html — 唯一官网                            │
│                    单文件 HTML + Tailwind CDN                            │
│                    首页 │ 工作台 │ 电商管理 │ 交互地图 │ AI 助理          │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐       │
│  │   身份层          │  │   执行层          │  │   电商后端        │       │
│  │   Alpha-ID       │  │   Nebula         │  │   DS             │       │
│  │   :8000          │  │   :2002          │  │   :3004          │       │
│  │                  │  │                  │  │                  │       │
│  │  DID / JWT       │  │  工作流引擎       │  │  Shoplazza 连接   │       │
│  │  双链记忆         │  │  LLM 意图识别    │  │  Prisma ORM      │       │
│  │  MCP 协议        │  │  多平台接入       │  │  实时仪表盘       │       │
│  │  飞书 Bot        │  │  向量搜索         │  │  商品/订单管理    │       │
│  └────────┬─────────┘  └──────────────────┘  └──────────────────┘       │
│           ▲                                                             │
│           │                                                             │
│  ┌────────┴─────────┐                                                   │
│  │   编排层          │                                                   │
│  │   core           │                                                   │
│  │   :3001          │                                                   │
│  │                  │                                                   │
│  │  角色匹配         │                                                   │
│  │  安全护栏         │                                                   │
│  │  任务调度         │                                                   │
│  └──────────────────┘                                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
          │
          │ 统一入口
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Caddy 反向代理 + 自动 HTTPS                                            │
│  Internet → Caddy (443/80) → 各服务内部端口                              │
└─────────────────────────────────────────────────────────────────────────┘
```

### 五层模型

| 层级 | 名称 | 职责 | 状态 |
|------|------|------|------|
| **Layer 5** | 生态层 | 插件市场 · Agent 交易所 · 社区治理 · 开放 API | 🔮 规划中 |
| **Layer 4** | 经济层 | Ghost Key 2.0 · 贡献证明(PoE) · 服务计价 | 🔮 规划中 |
| **Layer 3** | 平台层 | 多租户 · 插件系统 · 事件总线 · 可观测性 | 🚧 建设中 |
| **Layer 2** | 智能体层 | MasterAgent · DomainAgents · Loop 引擎 · 记忆系统 | ✅ 可用 |
| **Layer 1** | 基础设施层 | LLM 网关 · PostgreSQL · Redis · 加密 · 监控 | ✅ 可用 |

详见 [ARCHITECTURE.md](./ARCHITECTURE.md)

---

## ✨ Features <a name="features"></a>

| 模块 | 说明 | 亮点 |
|------|------|------|
| 🆔 **DID 身份** | 基于 Ed25519 的去中心化身份 | 双链记忆 · JWT · Token 经济 · 飞书 Bot |
| 🗺️ **交互地图** | Leaflet + Overpass + OSRM + Nominatim | 地理定位 · 周边搜索 · 路径规划 · 地点搜索 |
| 🤖 **AI 助理** | 多模态对话（文本/语音/图像） | Web Speech API · 语音合成 · 图像上传 · 快捷指令 |
| 📊 **电商管理** | 连接 Shoplazza（店匠） | 实时仪表盘 · 商品管理 · 订单追踪 |
| 🧠 **记忆系统** | 公开链 + 私有链（AES-256-GCM） | 短期/中期/长期三层记忆 · 向量搜索 |
| 🔄 **工作流引擎** | LLM 意图识别 + 多平台接入 | 飞书 · 微信 · 抖音 · 百度地图 |
| 🛡️ **安全护栏** | 权限门控 + 风险评估 + 信誉系统 | 多层安全 · 审计日志 |
| 🔌 **MCP 协议** | Model Context Protocol 支持 | Agent 间互操作标准 |

---

## 📦 Projects <a name="projects"></a>

| 项目 | 定位 | 技术栈 | 测试 | 部署 | 说明 |
|------|------|--------|------|------|------|
| **Ghost.html** | 唯一官网 | 单文件 HTML | — | ✅ | 所有面板对接真实 API |
| **[alpha-id](https://github.com/wenwanqing1217/alpha-id)** | 身份层 | Python + FastAPI | 928 ✅ | :8000 | PyPI 已发布 · DID/JWT/双链记忆/MCP |
| **[zcode-brain](https://github.com/wenwanqing1217/zcode-brain)** | 编排层 | TypeScript + Node | 42 ✅ | :3001 | 角色匹配 · 安全护栏 · 任务调度 |
| **[mindflow-map](https://github.com/wenwanqing1217/mindflow-map)** | 执行层 | Python + FastAPI | 221 ✅ | :2002 | 工作流引擎 · LLM 意图识别 |
| **DS** | 电商后端 | Next.js + Prisma | — | :3004 | Shoplazza（店匠）连接 |
| **[mindflow](https://github.com/wenwanqing1217/mindflow)** | 前端门户 | Next.js | 32 ✅ | — | 功能参考，已整合到 Ghost.html |

---

## 🛠️ Tech Stack

```
语言:     Python · TypeScript · SQL
后端:     FastAPI · SQLAlchemy · Alembic · PostgreSQL · Redis
前端:     Next.js 14 · React 18 · Tailwind · Leaflet
AI:       MCP Protocol · LLM Gateway · DeepSeek · ReAgent · TwinBrain
身份:     DID (Ed25519) · JWT · Skill Signing · Proof of Execution
基础设施: Docker · Caddy · Prometheus · GitHub Actions
平台接入: 飞书 · 微信 · 抖音 · Shopify · 百度地图
```

---

## 🗺️ Roadmap <a name="roadmap"></a>

### Phase 0: 地基 ✅
- [x] 身份层（Alpha-ID）发布 PyPI
- [x] 执行层（Nebula）工作流引擎
- [x] 编排层（core）安全护栏
- [x] 唯一官网（Ghost.html）
- [x] Docker Compose 一键启动

### Phase 1: 核心 🚧
- [ ] 统一飞书对话路径（TwinBrain 接入）
- [ ] 安全加固（凭证移入环境变量）
- [ ] 修复 CI / 端口不一致
- [ ] 重写调度层（MasterOrchestrator）

### Phase 2: 平台 📋
- [ ] 事件总线（Message Bus）
- [ ] 多租户引擎（Tenant Isolation）
- [ ] 持久化（flow → Prisma + PostgreSQL）
- [ ] A2A 真实通信协议
- [ ] Ghost.html 重构（合并工作台）

### Phase 3: 经济 🔮
- [ ] Ghost Key 2.0
- [ ] Proof of Execution 扩展
- [ ] 服务计价与自动结算

### Phase 4: 生态 🔮
- [ ] Agent 交易所
- [ ] 社区治理（提案 + 投票）
- [ ] Open API + SDK

详见 [ARCHITECTURE.md#四、演进路线图](./ARCHITECTURE.md)

---

## 🤝 Contributing <a name="contributing"></a>

欢迎贡献！请阅读我们的 [AGENT_PLAYBOOK.md](./AGENT_PLAYBOOK.md) 了解开发规范。

### 快速开始

```bash
# 1. Fork + Clone
git clone --recurse-submodules https://github.com/YOUR_NAME/monorepo.git
cd monorepo

# 2. 安装 pre-commit hooks
pip install pre-commit
pre-commit install

# 3. 启动开发环境
docker compose up -d db          # 先启动数据库
cd alphaid/projects && pip install -e ".[dev]" && uvicorn src.main:app --reload

# 4. 运行测试
pytest tests/ -v --tb=short --cov=src --cov-report=term-missing
```

### 提交规范

- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档变更
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 构建/工具变更

### 代码风格

- Python: `ruff` (lint + format)
- TypeScript: `eslint` + `prettier`
- 所有 PR 必须通过 CI

---

## 🤖 Agent 必读

> 如果你是 AI Agent（或 AI 辅助开发），请先阅读：
> 1. [`PROJECT_BRAIN.md`](./PROJECT_BRAIN.md) — 项目大脑：意图/架构/问题/方向
> 2. [`AGENT_PLAYBOOK.md`](./AGENT_PLAYBOOK.md) — 操作手册：怎么改/改哪里
>
> **不读不动手。**

---

## 📊 测试覆盖

| 层级 | 测试数 | 覆盖率 | CI |
|------|--------|--------|-----|
| 身份层 (alpha-id) | 928 | 68% | ✅ |
| 执行层 (nebula) | 221 | — | ✅ |
| 编排层 (core) | 42 | — | ✅ |
| 前端 (mindflow) | 32 | — | ✅ |
| **总计** | **1223** | — | ✅ |

---

## 🎯 可演示 Demo

1. **飞书出行智能体** — 自然语言输入 → 百度地图路径规划 → 飞书消息交互
2. **AI 助理 + 交互地图** — 对话式 AI + POI 搜索 + 工作流可视化
3. **数字身份 CLI** — `aid init` → `aid detect` → `aid profile show` 完整链路

---

## 📫 联系

- GitHub: [@wenwanqing1217](https://github.com/wenwanqing1217)
- PyPI: [alpha-id](https://pypi.org/project/alpha-id/)
- 项目文档: [ARCHITECTURE.md](./ARCHITECTURE.md) · [PROJECT_BRAIN.md](./PROJECT_BRAIN.md)

---

## License

[MIT](./LICENSE)

---

<div align="center">

<sub>Built with ❤️ — Ghost Layer sitting on top of all AI tools.</sub><br />
<sub>一次注册，所有 Agent 都认识你。</sub>

</div>
