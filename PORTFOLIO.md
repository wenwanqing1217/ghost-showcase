# Ghost Portfolio · 数字创世纪

**6 个独立项目，各自可本地运行和演示。**

> **诚实说明**：这是开发中的项目集合，面试时展示的是技术能力和工程实践，
> 而非生产级产品。各项目独立运行，跨服务集成仍在进行中。

## 快速开始

### 方式一：一键启动（推荐）
双击运行 `start-demo.bat`，选择要演示的项目。

### 方式二：分别启动
```bash
# mindflow-map - AI 工作流引擎
cd mindflow-map && uvicorn mindflow_map.main:app --port 2002

# DS - AI 电商仪表盘
cd DS && npm run dev   # http://localhost:3004

# AID - 数字身份服务
cd AID/projects && uvicorn src.main:app --port 8000

# MindFlow - AI 工作流平台
cd mindflow/apps/web && npm run dev    # http://localhost:3000
cd mindflow/apps/api && npm run dev    # http://localhost:3001

# ai综艺 - AI 综艺互动
cd "ai综艺" && npm run dev            # http://localhost:5173

# zcode-brain - Agent 编排
cd zcode-brain && npm test             # 运行 42 个测试
```

## 项目状态

| 项目 | 构建 | 测试 | Docker | 实际完成度 | 状态 |
|------|------|------|--------|-----------|------|
| AID | ✅ | 928/928 ✅ | ✅ | ~85% | 功能完整，生产需替换存储 |
| mindflow-map | ✅ | 221/221 ✅ | ✅ | ~75% | 核心功能完成，待安全加固 |
| DS | ✅ | 40/40 ✅ | ✅ | ~60% | Demo 可用，生产需替换数据库 |
| MindFlow | ✅ | 32/32 ✅ | ✅ | ~70% | 功能完整，待集成验证 |
| zcode-brain | ✅ | 42/42 ✅ | - | ~50% | 原型阶段，安全模块可用 |
| ai综艺 | ✅ | N/A | - | ~40% | 前端 Demo，无后端 |

**总计测试**: 1263+ passed

## 面试展示要点

### 1. mindflow-map - AI 工作流引擎
**一句话**: "我构建了一个 AI 工作流引擎，集成 LLM 意图识别、多模型回退和地图导航。"

展示要点:
- 打开 http://localhost:2002/docs 展示 Swagger API
- 展示 LLM 意图识别 + 规则引擎双重 fallback
- 展示 Bearer Token 认证 + 角色权限系统
- 展示 221 个测试覆盖的核心链路

技术亮点:
- Python 3.14, FastAPI, SQLite (aiosqlite)
- 多模型自动回退 + Circuit Breaker 防雪崩
- 百度地图集成 + 飞书/微信集成
- Pydantic 输入验证 + 认证中间件

### 2. DS - AI 电商仪表盘
**一句话**: "我构建了一个 AI 电商仪表盘，有 3 个 Agent 自动化处理内容、广告和客服。"

展示要点:
- 打开 http://localhost:3004 展示登录页面（Session Cookie 认证）
- 展示 Content Agent 人工审核工作流
- 展示风险引擎（ad-budget-cap, banned-words, price-change-threshold）
- 展示 Zod 输入验证 + 40 个测试

技术亮点:
- Next.js 14 + Prisma + SQLite
- Session Cookie 认证（非简单 Basic Auth）
- Zod schema 验证所有 API 输入
- 风险引擎 + 人工审核工作流

### 3. AID - 数字身份服务
**一句话**: "我实现了一个零依赖的 JWT 身份认证系统，支持跨服务验证。"

展示要点:
- 展示 `/api/v1/identity/auth/verify` 跨服务验证端点
- 展示自定义 HS256 JWT 实现（无 pyjwt 依赖）
- 展示 928 个测试覆盖 JWT 全生命周期
- 展示注册/登录/刷新/设备绑定流程

技术亮点:
- 零依赖 JWT 实现（hmac + base64 + json）
- FastAPI + Pydantic 模型验证
- 跨服务 JWT 验证端点（供 mindflow-map/DS 调用）
- 风控评估 + 声纹验证

### 4. zcode-brain - Agent 编排
**一句话**: "我设计了一个智能代理编排系统，实现专家角色匹配和安全护栏。"

展示要点:
- 运行 `npm test` 展示 42 个测试
- 展示安全护栏（危险命令/密钥泄漏检测）
- 展示角色匹配评分算法
- 展示边界输入处理（空/空白/超长/中文）

技术亮点:
- TypeScript + Vitest
- 安全检测覆盖 rm -rf/DROP DATABASE/密钥泄漏等
- 角色匹配基于文件发现 + 关键词评分
- 调度器集成安全检查前置

### 5. MindFlow - AI 工作流平台
**一句话**: "我架构了一个全栈 AI 工作流平台，支持多步骤任务执行。"

展示要点:
- 展示 Next.js 14 + Fastify 双端架构
- 展示 32 个测试覆盖 API + Web

### 6. ai综艺 - AI 综艺互动
**一句话**: "我创建了一个沉浸式 AI 推理综艺互动 Web 应用。"

展示要点:
- 展示 React + Vite + Framer Motion 动画
- 展示响应式设计

## 技术栈总览

```
mindflow-map: Python 3.14, FastAPI, SQLite, Pydantic, httpx, pytest
DS:           Next.js 14, Prisma, SQLite, OpenAI SDK, Recharts, Vitest, Zod
AID:          Python 3.14, FastAPI, JSON Storage, Pydantic, pytest
MindFlow:     Next.js 14, Fastify, TypeScript, Prisma, Tailwind, Vitest
ai综艺:       React 18, Vite 6, TypeScript, Tailwind, Framer Motion
zcode-brain:  TypeScript, Vitest, file-based JSON roles
```

## 工程实践

### 测试
- 1263+ 单元/集成测试，全部通过
- 测试覆盖：认证、输入验证、风险引擎、API 路由、安全检测
- 无页面渲染测试（全部替换为逻辑测试）

### 安全
- 无密钥硬编码（全部环境变量注入）
- 多层认证：Session Cookie / Bearer Token / JWT
- 输入验证：Zod (TypeScript) + Pydantic (Python)
- 安全护栏：危险命令/密钥泄漏正则检测

### 部署
- Docker Compose 统一编排（mindflow-map:2002, ds:3004, aid:8000）
- 各项目独立 Dockerfile + 健康检查
- Caddy 反向代理配置（需手动部署）

## 已知限制

- 默认 SQLite，生产需替换 PostgreSQL
- 跨服务数据流尚未完全打通（JWT 验证端点已就绪）
- LLM 调用需配置 API Key
- 无 CI/CD 流水线（本地测试通过）
- 生产部署需配置 HTTPS + 域名

## License

MIT
