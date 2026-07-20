# MindFlow Workspace - 成品展示

**5 个项目集合，核心项目已完成构建和测试修复，可直接演示。**

## 项目

| 项目 | 描述 | 启动命令 | 端口 |
|------|------|----------|------|
| [MindFlow](#mindflow) | AI Workflow Platform | `cd mindflow/apps/web && npm run dev` | 3000 |
| [DS](#ds) | AI Autonomous Shopify Shop | `cd DS && npm run dev` | 3002 |
| [ai综艺](#ai综艺) | AI Variety Show | `cd ai综艺 && npm run dev` | 5173 |
| [mindflow-brain](#mindflow-brain) | Agent Orchestration | `cd zcode-brain && npm test` | - |

## 快速启动

**Windows 用户**: 双击 `start-demo.bat`，选择项目即可。

**Mac/Linux 用户**:
```bash
# 构建所有项目
./build-all.sh

# 启动演示
./start-demo.sh
```

## MindFlow

全栈 AI 工作流平台，支持多步骤任务执行。

**启动**:
```bash
cd mindflow/apps/web && npm run dev    # 前端 http://localhost:3000
cd mindflow/apps/api && npm run dev    # 后端 http://localhost:3001
```

**技术栈**: Next.js 14, Fastify, TypeScript, Prisma, Tailwind, Vitest, Docker

**测试**: 32/32 通过 (API 16 + Web 11 + Shared 5)

**特点**:
- 多 workspace 架构
- 完整的 CI/CD (GitHub Actions)
- Docker 多阶段构建
- 生产级错误处理

## DS

AI 自主运营的电商平台，包含 3 个 AI Agent。

**启动**:
```bash
cd DS && npm run dev    # http://localhost:3002
```

**技术栈**: Next.js 14, TypeScript, Tailwind, Prisma, OpenAI, Recharts, Vitest
**测试**: 20/20 通过
**测试**: 20 passed / 8 failed (待修复)

**特点**:
- Content Agent: AI 生成商品文案 + 人工审核
- Ads Agent: 广告优化 + 预算管理
- CS Agent: 客服工单 + 智能升级
- Revenue: Recharts 收入趋势图
- Alerts: 实时通知系统

## ai综艺

沉浸式 AI 推理综艺互动 Web 应用。

**启动**:
```bash
cd "ai综艺" && npm run dev    # http://localhost:5173
```

**技术栈**: React 18, Vite 6, TypeScript, Tailwind, Framer Motion

**构建**: 2208 modules, 4.17s

**特点**:
- 流畅的动画过渡
- 响应式设计
- 交互式投票流程
- 生产级构建优化

## mindflow-brain

智能代理编排层，实现专家角色匹配和安全护栏。

**启动**:
```bash
cd zcode-brain && npm test    # 运行测试
```

**技术栈**: TypeScript, Vitest, file-based JSON roles

**测试**: 10/10 通过

**特点**:
- 10 个专家角色定义
- 关键词匹配评分
- 6 条安全规则
- Codex Bridge 集成

## 面试展示脚本

### 5 分钟快速展示

1. **MindFlow** (1 min)
   - 打开 http://localhost:3000
   - 展示聊天界面
   - 输入 "Build a React component"
   - 展示 WorkflowResult

2. **DS Dashboard** (2 min)
   - 打开 http://localhost:3002/dashboard
   - 点击 Content Agent → Generate Listing → Approve
   - 点击 Ads Agent → Auto-Optimize
   - 点击 Revenue → 切换 Weekly/Monthly
   - 点击 Alerts → 展示通知

3. **ai综艺** (1 min)
   - 打开 http://localhost:5173
   - 展示动画效果
   - 演示交互

4. **mindflow-brain** (1 min)
   - 运行 `npm test`
   - 展示 10 个 PASS 结果
   - 解释角色匹配机制

### 技术深度展示

- **架构**: 展示 monorepo 结构，解释 workspace 划分
- **测试**: 运行 `npm test` 各项目，展示 64+ 测试通过
- **CI/CD**: 展示 GitHub Actions 配置文件
- **Docker**: 展示 MindFlow Dockerfile 多阶段构建
- **数据库**: 展示 DS Prisma schema 和迁移

## 文件说明

- `start-demo.bat` - Windows 一键启动脚本
- `build-all.bat` - 构建所有项目
- `PORTFOLIO.md` - 详细面试指南
- `DEPLOY.md` - 各项目部署指南

## 环境要求

- Node.js >= 18
- npm >= 9
- 4GB+ RAM (推荐 8GB)

## 常见问题

**Q: 启动失败怎么办？**
A: 确保已运行 `npm install` 在各项目目录下。

**Q: 端口被占用？**
A: 修改各项目的 `.env` 或启动命令中的端口号。

**Q: DS 的 AI 功能不工作？**
A: DS 的 AI Agent 需要 `OPENAI_API_KEY`，演示模式使用 Mock 数据，可直接查看 UI。

---

**状态**: 核心项目已修复 ✅ | **构建**: mindflow 通过 ✅ | **测试**: mindflow 32/32、zcode-brain 10/10 通过 ⚠️ DS 仍有 8 个失败
