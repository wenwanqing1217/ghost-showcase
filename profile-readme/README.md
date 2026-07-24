<div align="center">

<!-- 动态标题 -->
<h1>
  <img src="https://readme-typing-svg.demolab.com?font=Inter&weight=600&size=28&duration=3000&pause=1000&color=A78BFA&center=true&vCenter=true&width=500&lines=Hi+%F0%9F%91%8B+I'm+Wenwanqing;Building+Ghost+%E2%80%94+AI+Agent+Matrix;Digital+Identity+%2B+Agent+Orchestration" />
</h1>

<!-- 徽章 -->
<p>
  <img src="https://img.shields.io/badge/Python-3.12+-blue?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/TypeScript-5.x-blue?logo=typescript&logoColor=white" />
  <img src="https://img.shields.io/badge/Next.js-14-black?logo=nextdotjs&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/DID-Ed25519-7c3aed" />
</p>

</div>

---

## 👻 Ghost — AI Agent 应用矩阵

> **让每个 AI Agent 都认识你是谁。**

Ghost 不是另一个 AI 助理，而是坐在所有 AI 工具之上的 **Ghost Layer** — 一个 AI Agent 应用矩阵。核心已发布到 PyPI。

### 架构

```
┌─────────────────────────────────────────────┐
│          AI Agent 应用矩阵（建设中）            │
│   电商 · 内容 · 办公 · 社交 · 出行 · 更多      │
├─────────────────────────────────────────────┤
│              执行层 — mindflow-map           │
│       工作流引擎 · LLM 意图识别 · 多平台接入    │
├─────────────────────────────────────────────┤
│              编排层 — zcode-brain            │
│         角色匹配 · 安全护栏 · 任务调度          │
├─────────────────────────────────────────────┤
│              身份层 — alpha-id  ← 核心        │
│       DID · 记忆双链 · JWT · Token 经济        │
└─────────────────────────────────────────────┘
```

### 核心包 — Alpha-ID

[![PyPI version](https://img.shields.io/pypi/v/alpha-id.svg)](https://pypi.org/project/alpha-id/)
[![Python](https://img.shields.io/pypi/pyversions/alpha-id.svg)](https://pypi.org/project/alpha-id/)
[![License](https://img.shields.io/pypi/l/alpha-id.svg)](https://github.com/wenwanqing1217/alpha-id/blob/main/LICENSE)
[![Tests](https://img.shields.io/badge/tests-928%20passing-brightgreen.svg)]()

```bash
pip install alpha-id
aid init                        # 初始化数字身份
aid detect                      # 扫描本机数字痕迹
aid collect chatgpt ~/export.zip # 从 ChatGPT 导入
aid profile show                # 查看数字画像
```

---

## 📦 项目矩阵

| 项目 | 定位 | 技术栈 | 测试 | 状态 |
|------|------|--------|------|------|
| **[alpha-id](https://github.com/wenwanqing1217/alpha-id)** | 身份层 — DID + 记忆 + JWT | Python + FastAPI | 928 ✅ | PyPI 已发布 |
| **[mindflow-map](https://github.com/wenwanqing1217/mindflow-map)** | 执行层 — 工作流引擎 | Python + FastAPI | 221 ✅ | 可用 |
| **[zcode-brain](https://github.com/wenwanqing1217/zcode-brain)** | 编排层 — 角色匹配 + 护栏 | TypeScript + Node | 42 ✅ | 可用 |
| **[mindflow](https://github.com/wenwanqing1217/mindflow)** | 前端门户 — AI 控制台 | Next.js + Fastify | 32 ✅ | 可用 |

---

## 🛠️ 技术栈

```
语言:     Python · TypeScript · SQL
后端:     FastAPI · SQLAlchemy · Alembic · PostgreSQL · Redis
前端:     Next.js 14 · React 18 · Tailwind · Leaflet
AI:       MCP Protocol · LLM Gateway · ReAgent · TwinBrain
身份:     DID (Ed25519) · JWT · Skill Signing · Proof of Execution
基础设施: Docker · Kubernetes · Caddy · Prometheus · GitHub Actions
平台接入: 飞书 · 微信 · 抖音 · Shopify · 百度地图
```

---

## 📊 测试覆盖

| 层级 | 测试数 | 覆盖率 | CI |
|------|--------|--------|-----|
| 身份层 (alpha-id) | 928 | 68% | ![CI](https://img.shields.io/github/actions/workflow/status/wenwanqing1217/alpha-id/ci.yml?label=CI) |
| 执行层 (mindflow-map) | 221 | — | ![CI](https://img.shields.io/github/actions/workflow/status/wenwanqing1217/mindflow-map/ci.yml?label=CI) |
| 编排层 (zcode-brain) | 42 | — | ![CI](https://img.shields.io/github/actions/workflow/status/wenwanqing1217/zcode-brain/ci.yml?label=CI) |
| 前端 (mindflow) | 32 | — | ![CI](https://img.shields.io/github/actions/workflow/status/wenwanqing1217/mindflow/ci.yml?label=CI) |

---

## 🎯 可演示 Demo

1. **飞书出行智能体** — 自然语言输入 → 百度地图路径规划 → 飞书消息交互
2. **AI 助手 + 交互地图** — 对话式 AI + POI 搜索 + 工作流可视化
3. **数字身份 CLI** — `aid init` → `aid detect` → `aid profile show` 完整链路

---

## 📫 联系

- GitHub: [@wenwanqing1217](https://github.com/wenwanqing1217)
- PyPI: [alpha-id](https://pypi.org/project/alpha-id/)
- 邮箱: wenwanqing1217@github.com

---

<p align="center">
  <sub>Built with ❤️ — Ghost Layer sitting on top of all AI tools.</sub>
</p>
