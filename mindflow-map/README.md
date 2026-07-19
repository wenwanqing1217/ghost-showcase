# MindFlow Map

**AI 统一工作流引擎 | 飞书/微信/公众号多端接入 | 百度地图 Agent Plan | 抖音短剧自动化 | Shopify 电商运营**

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Tests](https://img.shields.io/badge/tests-121%2F121%20passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

> **一句话定位**：你在飞书/微信里说话，MindFlow 自动帮你查地图、规划路线、发短剧、运营店铺，所有平台统一在一个工作台里。
>
> **差异化**：不仅是工作流自动化，MindFlow 还能自主扫描代码、生成修复、跑测试、提交 Git——唯一具备「自我进化」能力的 AI 工作流引擎。

---

## 为什么选择 MindFlow Map？

| 能力 | MindFlow Map | n8n | 飞书/企业微信 | AutoGen / CrewAI |
|------|-------------|-----|--------------|------------------|
| 多平台消息统一 | 飞书长连接 + 微信 Webhook + 公众号 | ❌ | 仅限自有生态 | ❌ |
| 真实地图 Agent | 百度地图 Agent Plan 深度集成 | ❌ | ❌ | ❌ |
| 自主代码修复 | Self-Loop 扫描 → 修复 → 测试 → 提交 | ❌ | ❌ | ❌ |
| 短剧 AI 预审 | 本地 AI 扫描 + 平台提交 + 回调入库 | ❌ | ❌ | ❌ |
| 零配置试用 | `DEMO_MODE=true` 即可运行 | ❌ 需 Docker | ❌ SaaS | ❌ 需 API Key |
| 中文生态原生 | 飞书/微信/抖音/百度全链路 | ❌ | 仅国内 | ❌ |
| 可扩展工具 | 工具注册表 + 声明式 YAML 工作流 | 400+ 节点 | 封闭 | LangChain 工具 |

### 核心场景

- **个人助理**：在微信/飞书发「明天去故宫的路线」，自动返回规划结果并同步日历。
- **内容运营**：抖音短剧脚本生成 → AI 合规预检 → 人工审批 → 自动发布。
- **团队协作**：工作流 + 审批流 + 通知流三合一，替代零散的工具组合。
- **开发者增效**：Autopilot 模式让 AI 自主扫描项目问题、生成补丁、跑测试、提交代码。

---

## 快速开始

### 环境要求

- Python 3.10+
- pip
- （可选）Playwright + Chromium，用于抖音自动化

### 一键启动（演示模式）

```bash
git clone https://github.com/<your-org>/mindflow-map.git
cd mindflow-map

pip install -e .

# 演示模式：无需任何 API Key 即可体验核心功能
$env:DEMO_MODE=true  # Windows PowerShell
# 或 Linux/macOS: export DEMO_MODE=true

uvicorn mindflow_map.main:app --host 0.0.0.0 --port 8000
```

### 生产配置

```bash
cp .env.example .env
# 填入至少以下配置：
# - BAIDU_MAP_AUTH_TOKEN
# - FEISHU_APP_ID / FEISHU_APP_SECRET
# - WECHAT_TOKEN / WECHAT_APP_ID / WECHAT_APP_SECRET
# - OPENAI_API_KEY（如需使用 AI 意图识别）

uvicorn mindflow_map.main:app --host 0.0.0.0 --port 8000
```

### 访问地址

| 服务 | 地址 |
|------|------|
| Workspace 工作台 | http://localhost:8000/workspace |
| API 文档 | http://localhost:8000/docs |
| 健康检查 | http://localhost:8000/health |
| 自动开发 API | http://localhost:8000/api/v1/autopilot |

---

## 项目结构

```
mindflow-map/
├── src/mindflow_map/
│   ├── main.py              # FastAPI 入口 + lifespan 资源管理
│   ├── config.py            # 配置管理（pydantic-settings）
│   ├── api/                 # API 路由层
│   │   ├── autopilot.py     # 自主开发 REST API
│   │   ├── feishu.py        # 飞书长连接客户端
│   │   ├── wechat.py        # 微信 Webhook 适配器
│   │   ├── map.py           # 百度地图 API 代理
│   │   ├── workflow.py      # 工作流执行 API
│   │   ├── shortdramas.py   # 短剧预审 API
│   │   └── automation.py    # 自动化聚合 API
│   ├── workflows/           # 核心工作流引擎
│   │   └── engine.py        # 意图识别 + 工具编排 + 线程池执行
│   ├── autopilot/           # 自主开发系统
│   │   ├── executor.py      # LLM 代码生成 + 安全写文件
│   │   ├── orchestrator.py  # 任务分解 + 角色匹配
│   │   ├── runner.py        # 测试 + Git 提交
│   │   ├── scheduler.py     # Cron 定时触发
│   │   ├── workflows.py     # YAML 工作流定义与执行
│   │   ├── self_loop.py     # 自循环改进引擎
│   │   ├── collaboration.py # 多 Agent 消息总线
│   │   └── ...
│   ├── ai/                  # AI 能力层
│   │   ├── llm.py           # LLM 客户端封装
│   │   └── intent.py        # 意图识别（LLM + 规则 fallback）
│   ├── tools/               # 工具集成
│   │   └── baidu_map.py     # 百度地图 Agent Plan SDK
│   ├── automation/          # 自动化集成
│   │   ├── douyin.py        # 抖音 Playwright 自动化
│   │   └── shopify.py       # Shopify Admin API
│   ├── integration/         # 第三方集成
│   │   └── shortdramas.py   # 短剧平台 AI 预检
│   ├── identity/            # 身份层
│   │   └── aid_client.py    # Alpha-ID 客户端
│   └── memory/              # 记忆层
│       └── store.py         # SQLite 持久化
├── static/                  # Workspace 前端资源
├── templates/               # Workspace HTML
├── tests/                   # 测试套件（121 passed）
├── workflows/               # 示例 YAML 工作流
├── docs/                    # 架构与部署文档
├── scripts/                 # 启动与工具脚本
├── pyproject.toml
├── .env.example
└── README.md
```

---

## 核心能力

### 1. 多平台统一工作流

一个后端同时接入飞书、微信、公众号，共用同一套意图识别和工具编排逻辑。用户在任何一端发起请求，体验一致。

### 2. 自主开发系统（Autopilot）

```
任务描述 → 角色匹配 → 安全校验 → LLM 生成代码 → 写文件 → 跑测试 → Git 提交
```

支持：
- **Self-Loop**：自动扫描项目问题，按优先级修复，循环直到通过。
- **Cron 调度**：定时触发工作流，无需人工干预。
- **Human-in-the-Loop**：关键步骤可插入审批，通过飞书/微信通知。

### 3. 中文生态深度集成

| 平台 | 能力 |
|------|------|
| 飞书 | 长连接实时收发消息，支持富文本、卡片 |
| 微信 | Webhook 签名验证，Access Token 缓存，CDATA 安全转义 |
| 百度地图 | Agent Plan API，语义化地点检索、路线规划、天气 |
| 抖音 | Playwright 自动化框架，支持短剧发布 |
| Shopify | Admin API REST 客户端，店铺运营 |

### 4. 声明式 YAML 工作流

```yaml
id: daily-content-pipeline
name: 每日内容流水线
triggers:
  - schedule: "0 9 * * *"
steps:
  - id: scan_trends
    type: task
    prompt: "扫描抖音今日热点话题"
  - id: generate_script
    type: task
    prompt: "基于热点生成短剧脚本"
  - id: precheck
    type: task
    agent: shortdramas
  - id: approval
    type: approval
    notify: wechat
  - id: publish
    type: task
    agent: douyin
```

---

## 测试

```bash
# 运行全量测试（121 passed）
pytest tests/ -v

# 仅单元测试
pytest tests/unit/ -v

# 带覆盖率报告
pytest tests/ --cov=mindflow_map --cov-report=html
start htmlcov/index.html
```

---

## 架构设计

详细架构文档：[docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)

### 核心原则

- **异步优先**：FastAPI + asyncio + httpx + aiosqlite，全链路非阻塞。
- **安全前置**：微信签名验证、SSRF 防护、路径逃逸检查、命令注入防护。
- **可观测性**：结构化日志、健康检查、执行历史持久化。
- **可扩展**：Tool 抽象基类 + 注册表模式，新增平台 = 新增 Tool 实现。

### 关键技术决策

| 决策 | 原因 |
|------|------|
| FastAPI 而非 Flask | 原生 async、自动生成 OpenAPI、依赖注入 |
| SQLAlchemy 2.x async | 异步 ORM，支持 aiosqlite 及未来切换 PostgreSQL |
| Pydantic Settings | 类型安全的配置管理，支持 `.env` 和环境变量 |
| ThreadPoolExecutor | 非 CPU 密集型 I/O 场景下，比 asyncio.create_task 更可控 |
| YAML 工作流 | 非技术人员可读可写，比 JSON 更友好 |

---

## API 文档

启动服务后访问：http://localhost:8000/docs

### 主要端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 + 配置状态 |
| GET | `/api/v1/autopilot/health` | Autopilot 健康检查 |
| POST | `/api/v1/autopilot/execute` | 自主执行任务 |
| POST | `/api/v1/autopilot/self-loop` | 自循环改进 |
| GET | `/api/v1/autopilot/workflows` | 列出 YAML 工作流 |
| POST | `/api/v1/autopilot/workflows` | 创建 YAML 工作流 |
| POST | `/api/v1/autopilot/workflows/{id}/start` | 启动工作流 |
| GET | `/api/v1/autopilot/workflows/{id}/runs` | 查询运行历史 |
| POST | `/api/v1/autopilot/scheduler/jobs` | 创建定时任务 |
| GET | `/api/v1/autopilot/scheduler/jobs` | 列出定时任务 |
| POST | `/api/v1/shortdramas/submit` | 提交短剧预审 |
| POST | `/api/v1/shortdramas/query` | 查询预审状态 |
| GET | `/api/v1/map/search` | 地点搜索 |
| GET | `/api/v1/map/direction` | 路线规划 |
| POST | `/api/v1/automation/douyin/publish` | 抖音发布 |

---

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | Python FastAPI + Uvicorn |
| AI | DeepSeek / 豆包 API（可插拔） |
| 地图 | 百度地图 Agent Plan（Bearer Token） |
| 自动化 | Playwright（抖音短剧） |
| 电商 | Shopify Admin API |
| 前端 | 原生 HTML/CSS/JS，Tailwind CSS |
| 数据库 | SQLite + SQLAlchemy（记忆存储） |
| 部署 | 任意支持 Python 的服务器 / Docker |

---

## 路线图

- [x] Phase 1: 基础架构 + 飞书长连接
- [x] Phase 2: 百度地图 Agent Plan 集成
- [x] Phase 3: MindFlow Workspace 统一工作台
- [x] Phase 4: 微信公众号接入
- [x] Phase 5: 抖音短剧预审 + 自动化
- [x] Phase 6: Autopilot 自主开发系统
- [ ] Phase 7: Visual Workflow Editor（拖拽式工作流编辑器）
- [ ] Phase 8: Plugin SDK + Integration Marketplace
- [ ] Phase 9: Multi-Tenancy + RBAC + Audit Logs
- [ ] Phase 10: 英文文档 + 国际化

---

## 贡献

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

## License

MIT
