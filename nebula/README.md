# MindFlow Map — AI 工作流引擎

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-221%20passing-brightgreen.svg)](https://github.com/wenwanqing1217/mindflow-map)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/wenwanqing1217/mindflow-map/blob/main/LICENSE)

> **Ghost 矩阵的执行层** — 工作流引擎、LLM 意图识别、多平台接入。

MindFlow Map 是 [Ghost](https://github.com/wenwanqing1217) AI Agent 矩阵的执行层。它提供工作流编排、LLM 网关、多平台消息接入（飞书/微信/抖音）、地图服务等能力。

---

## 在 Ghost 矩阵中的位置

```
┌─────────────────────────────────────────────┐
│          AI Agent 应用矩阵                    │
├─────────────────────────────────────────────┤
│              执行层 — mindflow-map  ← 本仓库  │  ← 你在这里
│       工作流引擎 · LLM 意图识别 · 多平台接入    │
├─────────────────────────────────────────────┤
│              编排层 — zcode-brain            │
├─────────────────────────────────────────────┤
│              身份层 — alpha-id               │
└─────────────────────────────────────────────┘
```

---

## ✨ 核心能力

| 模块 | 说明 |
|------|------|
| ⚙️ **工作流引擎** | 任务编排、状态管理、异步执行 |
| 🤖 **LLM 网关** | 支持熔断、降级、健康检查 |
| 🗺️ **地图服务** | 百度地图 API — 地点查询、路径规划、POI 搜索 |
| 💬 **飞书集成** | Bot + Webhook 双模式，消息回调与交互 |
| 📱 **微信接入** | 基础消息回调 |
| 🎬 **抖音自动化** | 内容发布自动化 |
| 🛒 **Shopify 接入** | 电商数据对接 |
| 📊 **Prometheus 监控** | 指标采集与暴露 |
| 🔐 **中间件栈** | 审计、认证、限流、错误处理 |

---

## 🚀 快速开始

```bash
# 安装依赖
pip install -e ".[dev]"

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Key

# 启动服务
uvicorn mindflow_map.main:app --reload --port 2002
```

### Docker 部署

```bash
docker-compose up -d
```

---

## 🛠️ 技术栈

- **Python 3.10+** / **FastAPI** — 高性能异步 Web 框架
- **SQLAlchemy 2.0** + **Alembic** — ORM 与数据库迁移
- **PostgreSQL** + **Redis** — 数据持久化与缓存
- **Pydantic v2** — 数据验证
- **Playwright** — 浏览器自动化
- **OpenAI SDK** — LLM 调用

---

## 📁 项目结构

```
src/mindflow_map/
├── main.py               # FastAPI 入口
├── config.py             # 配置管理
├── api/                  # REST API 路由
│   ├── workflow.py       # 工作流接口
│   ├── map.py            # 地图服务
│   ├── feishu.py         # 飞书集成
│   ├── wechat.py         # 微信接入
│   ├── shortdramas.py    # 短剧内容
│   ├── automation.py     # 自动化
│   └── health.py         # 健康检查
├── core/                 # 核心引擎
│   ├── metrics.py        # Prometheus 指标
│   └── ...
├── middleware/           # 中间件栈
│   ├── auth.py           # 认证
│   ├── rate_limit.py     # 限流
│   ├── audit.py          # 审计
│   └── prometheus.py     # 监控
├── workflows/            # 工作流定义
└── models/               # 数据模型
```

---

## 📄 许可证

MIT

---

<p align="center">
  <sub>Built with ❤️ — <a href="https://github.com/wenwanqing1217">Ghost Layer</a> 执行层</sub>
</p>
