# Ghost — AI 时代的 Ghost Layer

**6 个独立项目，各自可本地运行，部分支持 Docker 部署。**

> **诚实说明**：这是一个开发中的项目集合，不是生产级平台。
> 各项目独立运行，尚未实现跨服务数据互通。

## 项目一览

| 项目 | 描述 | 技术栈 | 本地启动 | 端口 |
|------|------|--------|----------|------|
| [mindflow-map](#mindflow-map) | AI 工作流引擎 | Python/FastAPI/SQLite | `uvicorn mindflow_map.main:app` | 2002 |
| [DS](#ds) | AI 电商仪表盘 | Next.js/Prisma/SQLite | `npm run dev` | 3004 |
| [AID](#aid) | 数字身份服务 | Python/FastAPI/JSON | `uvicorn src.main:app` | 8000 |
| [MindFlow](#mindflow) | AI 工作流平台 | Next.js/Fastify | `npm run dev` | 3000/3001 |
| [ai综艺](#ai综艺) | AI 综艺互动 | React/Vite | `npm run dev` | 5173 |
| [zcode-brain](#zcode-brain) | Agent 编排 | TypeScript | `npm test` | - |

## 快速启动

**Windows 用户**: 双击 `start-demo.bat`，选择项目。

**手动启动**:
```bash
# mindflow-map（需 .env 或 DEMO_MODE=true）
cd mindflow-map && uvicorn mindflow_map.main:app --reload --port 2002

# DS（需 .env 配置 DASH_USER/DASH_PASS）
cd DS && npm run dev   # http://localhost:3004

# AID（需 AUTH_MASTER_KEY 环境变量）
cd AID/projects && uvicorn src.main:app --reload --port 8000
```

## 测试状态

| 项目 | 测试数 | 覆盖范围 |
|------|--------|----------|
| **AID** | 928/928 ✅ | JWT 认证、身份管理、社交、风控、API 端点 |
| **mindflow-map** | 221/221 ✅ | 认证中间件、工作流、地图工具、意图识别 |
| **DS** | 40/40 ✅ | 风险引擎、指标聚合、输入验证、API 路由 |
| **zcode-brain** | 42/42 ✅ | 安全检查器、角色匹配、调度器、边界输入 |
| **MindFlow** | 32/32 ✅ | API + Web 单元测试 |
| **ai综艺** | N/A | 前端 Demo，无测试 |

**合计**: 1263+ 测试通过

## 项目详情

### mindflow-map
AI 统一工作流引擎，集成地图导航、内容预审、LLM 意图识别。

**启动**:
```bash
cd mindflow-map
pip install -e ".[dev]"
uvicorn mindflow_map.main:app --reload --port 2002
```

**核心特性**:
- LLM 意图识别 + 规则引擎双重 fallback
- 多模型自动回退 + Circuit Breaker
- 百度地图集成
- 飞书/微信集成
- 可视化工作流编辑器（React Flow）
- Bearer Token 认证 + 权限角色系统

**已知限制**:
- 数据库默认 SQLite，生产需替换 PostgreSQL
- LLM 调用需配置 API Key（支持 DeepSeek/LongCat 等 OpenAI 兼容接口）
- 飞书/微信集成需对应平台开发者账号

### DS
AI 电商仪表盘，3 个 AI Agent 自动化处理内容、广告和客服。

**启动**:
```bash
cd DS && npm run dev   # http://localhost:3004
```

**核心特性**:
- Content Agent: AI 生成商品文案 + 人工审核
- Ads Agent: 广告管理 + AI 优化建议
- CS Agent: 客服工单 + 智能升级
- 风险引擎 (ad-budget-cap, banned-words, price-change)
- Session Cookie 认证 + 登录页面
- Zod 输入验证

**已知限制**:
- 默认 SQLite + Demo 模式（无需 OpenAI Key 可运行）
- 生产部署需替换 PostgreSQL + 配置真实 OpenAI/Shopify API Key
- Dashboard 认证使用简单 session，非企业级 SSO

### AID (Alpha-ID)
数字身份基础设施，支持 DID 生成、设备指纹、JWT 认证。

**启动**:
```bash
cd AID/projects
pip install -e ".[dev]"
# 必须设置 AUTH_MASTER_KEY（任意 32+ 字符）
set AUTH_MASTER_KEY=your-random-key-here
uvicorn src.main:app --reload --port 8000
```

**核心特性**:
- 自定义 HS256 JWT 实现（零依赖）
- 注册/登录/刷新令牌/跨设备同步
- 跨服务 JWT 验证端点 (`/api/v1/identity/auth/verify`)
- 风控评估 + 声纹验证
- 短剧内容审核自动化

**已知限制**:
- 用户存储默认 JSON 文件（生产需实现 PostgresStorage）
- 设备指纹为简单字符串匹配，非真实浏览器指纹
- 无密码找回/重置流程

### MindFlow
全栈 AI 工作流平台，支持多步骤任务执行。

**启动**:
```bash
cd mindflow/apps/web && npm run dev    # http://localhost:3000
cd mindflow/apps/api && npm run dev    # http://localhost:3001
```

**已知限制**:
- 前端 3000 端口与 DS 默认端口冲突（DS 已改为 3004）
- 需要分别启动 web 和 api 两个服务

### ai综艺
沉浸式 AI 推理综艺互动 Web 应用。

**启动**:
```bash
cd "ai综艺" && npm run dev   # http://localhost:5173
```

**已知限制**:
- 纯前端 Demo，无后端 API
- 数据为静态 mock

### zcode-brain
Agent 编排层，支持多角色匹配和安全护栏。

**运行测试**:
```bash
cd zcode-brain && npm test   # 42 个 vitest 测试
```

**核心特性**:
- 基于文件的 JSON 角色发现
- 关键词匹配评分算法
- 安全护栏（危险命令/密钥泄漏检测）
- 调度器集成安全检查

**已知限制**:
- 角色匹配为关键词匹配，非语义理解
- 安全检测基于正则，可被高级攻击绕过
- 无实际 LLM 调用（仅编排层）

## 部署

### Docker Compose（根目录统一编排）
```bash
docker compose up -d
# mindflow-map:2002, ds:3004, aid:8000
```

### 单独部署
各项目目录下含独立 `Dockerfile` 和 `docker-compose.yml`。

**注意**: Docker 部署需配置对应环境变量（见各项目 `.env.example`）。

## 项目结构
```
D:\MW/
├── mindflow-map/     # AI 工作流引擎（Python/FastAPI）[独立 git]
├── mindflow/         # AI 工作流平台（Next.js/Fastify）[submodule]
├── DS/               # AI 电商仪表盘（Next.js）[submodule]
├── ai综艺/           # AI 综艺（Vite）[submodule]
├── zcode-brain/      # Agent 编排 [submodule]
├── AID/projects/     # 数字身份 [submodule]
├── docs/             # 审计报告/翻新方案
├── scripts/          # 工具脚本（health_check.py）
├── demo/             # 演示配置
├── docker-compose.yml # 统一编排
├── start-demo.bat    # 一键启动
└── Caddyfile         # 反向代理配置（需 Caddy）
```

## 架构现状

```
用户 → start-demo.bat → 6 个独立服务
                               ↓
                        无数据互通（Phase 4 已建立 JWT 验证端点）
                               ↓
                        各自独立数据库
```

**集成状态**:
- AID 提供 `/api/v1/identity/auth/verify` 端点，其他服务可验证其签发的 JWT
- mindflow-map 已有 AlphaIDClient 连接 AID 的 profile/memory 接口
- 尚未实现完整的跨服务数据流

## 安全状态

- ✅ 无密钥硬编码（全部环境变量注入）
- ✅ DS 仪表盘 Session Cookie 认证
- ✅ mindflow-map Bearer Token + 角色权限
- ✅ AID JWT HS256 认证
- ✅ Zod/Pydantic 输入验证
- ✅ 安全护栏（zcode-brain 危险命令检测）
- ⚠️ 生产部署需配置 HTTPS（Caddy 或反向代理）
- ⚠️ 默认 SQLite，生产需 PostgreSQL

## License

MIT
