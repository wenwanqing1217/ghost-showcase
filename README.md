# Ghost — AI Agent 应用矩阵

> **让每个 AI Agent 都认识你是谁。**

Ghost 是 AI Agent 世界的身份层。当越来越多的 AI 工具涌现，每次使用新工具都像遇到陌生人的困境——你要重新介绍自己。Ghost 终结这件事：一次注册，所有 Agent 都认识你。

> 🤖 **Agent 必读顺序**：[`PROJECT_BRAIN.md`](./PROJECT_BRAIN.md)（项目大脑：意图/架构/问题/方向）→ [`AGENT_PLAYBOOK.md`](./AGENT_PLAYBOOK.md)（操作手册：怎么改/改哪里）。不读不动手。

---

## 架构

```
┌─────────────────────────────────────────────────────────┐
│              唯一官网：Ghost.html（已部署）                │
│  单文件 HTML + Tailwind CDN                              │
│  包含：首页 / Web4.0路由器 / 个人工作台 / 电商管理          │
└────────────────────────┬────────────────────────────────┘
                         │ fetch()
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌──────────────┐ ┌───────────────┐ ┌───────────────┐
│  身份层       │ │  执行层        │ │  电商后端      │
│  alphaid     │ │  nebula       │ │  DS           │
│  :8000       │ │  :2002        │ │  :3004        │
└──────────────┘ └───────────────┘ └───────────────┘
        ▲
        │
┌──────────────┐
│  编排层       │
│  core        │
│  :3001       │
└──────────────┘
```

---

## 项目清单

| 层级 | 项目 | 技术 | 测试 | 部署 | 说明 |
|------|------|------|------|------|------|
| **官网** | `Ghost.html` | 单文件 HTML | — | ✅ | 唯一对外入口，所有面板对接真实 API |
| **身份层** | [alphaid](https://github.com/wenwanqing1217/alpha-id) | Python+FastAPI | 928✅ | :8000 | DID/JWT/记忆双链/MCP/飞书Bot |
| **编排层** | [core](https://github.com/wenwanqing1217/zcode-brain) | TypeScript+Node | 42✅ | :3001 | 角色匹配/安全护栏/任务调度 |
| **执行层** | nebula | Python+FastAPI | 221✅ | :2002 | 工作流引擎/LLM意图识别/多平台接入 |
| **电商后端** | `DS/` | Next.js+Prisma | — | :3004 | 连接 Shoplazza（店匠） |
| **前端原型** | [flow](https://github.com/wenwanqing1217/mindflow) | Next.js | 32✅ | ❌ | 功能参考，未部署，不是官网 |

---

## 快速启动

```bash
# 身份层（核心）
cd alphaid/projects
pip install -e ".[dev]"
set AUTH_MASTER_KEY=your-random-key-here
uvicorn src.main:app --reload --port 8000

# 执行层
cd nebula
pip install -e ".[dev]"
set DEMO_MODE=true
uvicorn mindflow_map.main:app --reload --port 2002

# 电商后端
cd DS
npm install
npm run dev  # → :3004
```

---

## 官网功能（Ghost.html）

| 模块 | 数据来源 | 说明 |
|------|----------|------|
| 首页 Landing | 静态 | 品牌展示 + 小精灵互动 |
| Web 4.0 路由器 | alphaid :8000 | 意图解析/Skill路由/决策树/记忆图谱/Agent广场 |
| 电商管理 | DS :3004 | 店铺/商品/订单实时数据 |
| 个人工作台 | alphaid :8000 | 思维画布/任务看板/笔记库/人格画像 |
| 登录/注册 | alphaid :8000 | 面部识别 → 真实 DID 注册 |

---

## License

MIT
