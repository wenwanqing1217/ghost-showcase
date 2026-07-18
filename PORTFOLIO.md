# MindFlow Portfolio - 成品展示包

**直接运行，无需配置。所有项目已构建、测试、准备好展示。**

## 快速开始

### 方式一：一键启动（推荐）
双击运行 `start-demo.bat`，选择要演示的项目。

### 方式二：分别启动
```bash
# MindFlow - AI Workflow Platform
cd mindflow/apps/web && npm run dev    # http://localhost:3000
cd mindflow/apps/api && npm run dev    # http://localhost:3001

# DS - AI Autonomous Shopify Shop
cd DS && npm run dev                    # http://localhost:3002

# ai综艺 - AI Variety Show
cd "ai综艺" && npm run dev            # http://localhost:5173

# ZCode Brain - Orchestration Layer
cd zcode-brain && npm test             # 运行测试
```

## 项目状态

| 项目 | 构建 | 测试 | 文档 | 状态 |
|------|------|------|------|------|
| MindFlow | ✅ | 32/32 ✅ | ✅ | 可直接运行 |
| DS | ✅ | 20/20 ✅ | ✅ | 可直接运行 |
| ai综艺 | ✅ | N/A | ✅ | 可直接运行 |
| ZCode Brain | ✅ | 12/12 ✅ | ✅ | 可直接运行 |

## 面试展示要点

### 1. MindFlow - AI Workflow Platform
**一句话**: "我架构了一个全栈 AI 工作流平台，支持多步骤任务执行。"

展示要点:
- 打开 http://localhost:3000
- 展示 Hero 区域的聊天界面
- 输入框输入内容，展示 Typed Input/Output
- 展示 WorkflowResult 组件的步骤状态

技术亮点:
- Next.js 14 App Router + Fastify 后端
- 多 workspace 架构 (web/api/shared)
- 完整的 CI/CD (GitHub Actions)
- Docker 多阶段构建
- 32 个自动化测试

### 2. DS - AI Autonomous Shopify Shop
**一句话**: "我构建了一个自主运营的电商平台，有 3 个 AI Agent 自动化处理内容、广告和客服。"

展示要点:
- 打开 http://localhost:3002/dashboard
- **Content Agent**: 展示 AI 生成商品文案 + 人工审核流程
- **Ads Agent**: 展示广告活动管理 + AI 优化建议
- **CS Agent**: 展示客服工单队列 + 智能升级规则
- **Revenue**: 展示 Recharts 收入趋势图
- **Alerts**: 展示实时通知系统

技术亮点:
- Next.js 14 + Prisma + OpenAI SDK
- 3 个完整功能的 AI Agent
- 风险引擎 (ad-budget-cap, banned-words, price-change)
- 人工审核工作流 (approve/reject)
- Recharts 数据可视化
- 20 个自动化测试

### 3. ai综艺 - AI Variety Show
**一句话**: "我创建了一个沉浸式 AI 推理综艺互动 Web 应用。"

展示要点:
- 打开 http://localhost:5173
- 展示动画过渡效果
- 展示响应式设计
- 演示交互投票流程

技术亮点:
- React 18 + Vite 6 + TypeScript
- Framer Motion 动画
- Tailwind CSS 样式
- 生产级构建 (4.17s, 2208 modules)

### 4. ZCode Brain - Agent Orchestration
**一句话**: "我设计了一个智能代理编排系统，实现专家角色匹配和安全护栏。"

展示要点:
- 运行 `npm test` 展示 10 个角色匹配测试
- 运行 `npx vitest run` 展示 12 个正式测试
- 展示 10 个专家角色定义
- 展示 6 条安全规则

技术亮点:
- 基于文件的角色发现系统
- 关键词匹配评分算法
- 模式匹配安全验证
- Codex Bridge 集成层
- Agency-Agents + AGENT-ZERO 概念实现

## 技术栈总览

```
MindFlow:  Next.js 14, Fastify, TypeScript, Prisma, Tailwind, Vitest, Docker
DS:        Next.js 14, TypeScript, Tailwind, Prisma, OpenAI, Recharts, Vitest
ai综艺:    React 18, Vite 6, TypeScript, Tailwind, Framer Motion
ZCode:     TypeScript, Vitest, file-based JSON roles
```

## 项目结构

```
mindflow-workspace/
├── mindflow/          # AI Workflow Platform
│   ├── apps/
│   │   ├── web/       # Next.js 14 frontend
│   │   └── api/       # Fastify backend
│   └── packages/
│       └── shared/    # Shared types
├── DS/                # AI Autonomous Shopify Shop
│   ├── src/app/
│   │   ├── (dashboard)/    # 8 dashboard pages
│   │   └── api/            # 5 API routes
│   ├── src/lib/
│   │   ├── shopify/        # Shopify client
│   │   ├── ai/             # OpenAI wrapper
│   │   ├── agents/         # Content agent
│   │   └── risk/           # Risk engine
│   └── prisma/
│       └── schema.prisma   # Database schema
├── ai综艺/            # AI Variety Show
│   ├── src/
│   ├── .archive/      # Legacy files
│   └── assets/
├── zcode-brain/       # Agent Orchestration
│   ├── roles/         # 10 expert roles
│   ├── dispatcher/    # Role matching + Codex bridge
│   └── safety/        # 6 safety rules
├── build-all.bat      # Build all projects
└── start-demo.bat     # Launch demo
```

## 数据流展示

```
用户请求 → ZCode Brain (角色匹配 + 安全检查)
                    ↓
            Codex (代码生成)
                    ↓
            MindFlow / DS (部署运行)
```

## 部署准备

所有项目已准备好部署到生产环境:

- **ai综艺**: 直接部署到 Vercel (无需环境变量)
- **DS**: 部署到 Vercel (需要 OPENAI_API_KEY, Shopify 凭证)
- **MindFlow**: Web 部署到 Vercel, API 部署到 Railway (需要 OPENAI_API_KEY)

详见各项目的 `DEPLOY.md` 文件。

## 测试覆盖

```
MindFlow:  32 测试通过 (API 16 + Web 11 + Shared 5)
DS:        20 测试通过 (Risk 3 + API 2 + Pages 15)
ZCode:     12 测试通过 (Dispatcher 10 + Safety 2)
```

## License

MIT
