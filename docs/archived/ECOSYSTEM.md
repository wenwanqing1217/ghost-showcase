# Ghost 全局生态系统

> 更新日期：2026-07-27
> 本文档串联所有组件，展示完整架构

---

## 一、系统全景图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              用户入口层                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Ghost.html│  │ 飞书 Bot │  │ 桌面宠   │  │ Chrome   │  │ CLI      │    │
│  │ (:8000)  │  │          │  │ (pyautogui)│ │ 扩展     │  │ (aid)    │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       │              │              │              │              │          │
└───────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────┘
        │              │              │              │              │
        ↓              ↓              ↓              ↓              ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Gateway 统一网关 (:18080)                          │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐                 │
│  │ /v1/human/* │ /v1/agent/* │ /v1/internal│ /v1/net/*   │                 │
│  └──────┬──────┴──────┬──────┴──────┬──────┴──────┬──────┘                 │
└─────────┼─────────────┼─────────────┼─────────────┼────────────────────────┘
          │             │             │             │
          ↓             ↓             ↓             ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                              后端服务层                                       │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  Alpha-ID    │  │   Nebula     │  │  Orchestrator│  │  Net-Agent   │   │
│  │  (:8000)     │  │  (:2002)     │  │  (:19090)    │  │  (:18180)    │   │
│  │  身份/记忆   │  │  工作流引擎  │  │  任务调度    │  │  路由器管理  │   │
│  └──────┬───────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│         │                                                                   │
│  ┌──────┴───────┐  ┌──────────────┐  ┌──────────────┐                      │
│  │  Flow/API    │  │  豆包扫描器  │  │ Collector    │                      │
│  │  (:3001)     │  │  (后台线程)  │  │ Daemon       │                      │
│  │  AI 路由     │  │  LevelDB     │  │ Cursor/Trae  │                      │
│  └──────────────┘  └──────────────┘  └──────────────┘                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                              数据存储层                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  PostgreSQL  │  │   SQLite     │  │   Obsidian   │  │  JSON 文件   │   │
│  │  (Docker)    │  │  (本地)      │  │  Vault       │  │  (assets/)   │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 二、组件清单

### 2.1 核心服务

| 组件 | 端口 | 语言 | 职责 | 状态 |
|:-----|:-----|:-----|:-----|:-----|
| **Alpha-ID** | 8000 | Python | DID 身份、双链记忆（AES-256-GCM）、TwinBrain 状态机、AgentLoop、A2A 协议、风控引擎、GDPR 合规、Prometheus 指标 | ✅ 运行中 |
| **Gateway** | 18080 | Python | 统一 API 入口、四层路由、限流 | ✅ 运行中 |
| **Nebula** | 2002 | Python | 工作流引擎、意图识别 | ✅ 运行中 |
| **Net-Agent** | 18180 | Python | 路由器管理、网络操作 | ⚠️ 可选 |
| **Orchestrator** | 19090 | Python | 双编程工具协同调度 | ⚠️ 可选 |
| **Flow/API** | 3001 | TypeScript | AI 多 Provider 路由、Computer Use | ⚠️ 可选 |

### 2.2 后台进程

| 组件 | 类型 | 职责 | 状态 |
|:-----|:-----|:-----|:-----|
| **豆包扫描器** | 后台线程 | 扫描豆包桌面 App LevelDB，提取对话 | ✅ 运行中 |
| **Collector Daemon** | 后台进程 | 采集 Cursor/Trae/Git 数据 → Gateway | ⚠️ 可选 |
| **CDP Capture** | Chrome 扩展 | 捕获豆包网页版对话 | ⚠️ 可选 |

### 2.3 用户入口

| 组件 | 类型 | 职责 | 状态 |
|:-----|:-----|:-----|:-----|
| **Ghost.html** | Web 前端 | 官网、A2A 生态区、Mindflow 协作 | ✅ 运行中 |
| **飞书 Bot** | 飞书应用 | AI 编程助手（AtomCode/ZCode/Codex） | ⚠️ 可选 |
| **桌面宠** | 桌面应用 | Ollama 本地 LLM 交互 | ⚠️ 可选 |
| **CLI (aid)** | 命令行 | DID 创建、数据采集、画像查看 | ✅ 可用 |

---

## 三、数据流

### 3.1 用户请求主流程

```
用户 → Ghost.html / 飞书 / CLI
  ↓
Gateway (:18080)
  ↓ 路由匹配
  ├── /v1/human/* → Alpha-ID (:8000)
  ├── /v1/agent/* → Alpha-ID / Obsidian
  ├── /v1/internal/* → Alpha-ID / Orchestrator
  └── /v1/net/* → Net-Agent (:18180)
  ↓
响应信封封装 → 返回用户
```

### 3.2 数据采集流

```
┌─ 豆包桌面 App ──────────────────┐
│ LevelDB 数据库                   │
│   ↓ 每 2 分钟扫描               │
│ doubao_reader (LogReader)        │
│   ↓ POST                        │
│ Gateway /v1/internal/doubao     │
│   ↓                             │
│ Alpha-ID /memory/store          │
│   ↓                             │
│ Obsidian Vault                  │
└─────────────────────────────────┘

┌─ 豆包网页版 ────────────────────┐
│ Chrome 扩展 (Ghost Capture)      │
│   ↓ CDP 捕获                    │
│ cdp_poll.py                     │
│   ↓                             │
│ Gateway /v1/internal/doubao     │
│   ↓                             │
│ Alpha-ID + Obsidian             │
└─────────────────────────────────┘

┌─ 开发工具 ──────────────────────┐
│ Collector Daemon                │
│   ├── Cursor 使用数据           │
│   ├── Trae 使用数据             │
│   └── Git 提交记录              │
│   ↓ POST                        │
│ Gateway /v1/memory/store        │
│   ↓                             │
│ Alpha-ID 双链记忆               │
└─────────────────────────────────┘

┌─ 飞书 Bot ──────────────────────┐
│ 用户发消息                       │
│   ↓                             │
│ bot.py (WebSocket + HTTP)       │
│   ↓ 调用后端                    │
│ AtomCode / ZCode / Codex        │
│   ↓ 返回结果                    │
│ 飞书回复用户                     │
└─────────────────────────────────┘
```

### 3.3 任务编排流

```
用户提交任务
  ↓
Orchestrator /v1/task/submit
  ↓
┌─ 串联模式 ──────────────────────┐
│ 需求 → AI 起草 → ToolA 生成     │
│   → ToolB 优化 → 归档           │
└─────────────────────────────────┘
┌─ 并行模式 ──────────────────────┐
│ 需求 → ToolA + ToolB 同时执行   │
│   → 对比 → 归档                 │
└─────────────────────────────────┘
  ↓
Gateway /v1/memory/store → 记忆沉淀
```

---

## 四、服务间通信

### 4.1 同步通信

| 调用方 | 被调方 | 协议 | 端点 |
|:-------|:-------|:-----|:-----|
| Ghost.html | Gateway | HTTP | `http://localhost:18080/*` |
| Gateway | Alpha-ID | HTTP | `http://localhost:8000/*` |
| Gateway | Nebula | HTTP | `http://localhost:2002/*` |
| Gateway | Net-Agent | HTTP | `http://localhost:18180/*` |
| Gateway | Orchestrator | HTTP | `http://localhost:19090/*` |
| 豆包扫描器 | Gateway | HTTP | `POST /v1/internal/doubao/capture` |
| Collector Daemon | Gateway | HTTP | `POST /v1/memory/store` |
| Orchestrator | Gateway | HTTP | `POST /v1/memory/store` |
| 飞书 Bot | Alpha-ID | HTTP | 直接调用 |

### 4.2 异步/后台

| 进程 | 触发方式 | 目标 |
|:-----|:---------|:-----|
| 豆包扫描器 | 每 2 分钟 | Gateway |
| Collector Daemon | 每 2 分钟 | Gateway |
| CDP Capture | 页面事件 | Gateway |
| 飞书 Bot | WebSocket 长连接 | 飞书服务器 |

---

## 五、部署拓扑

### 5.1 本地开发环境

```
start-all.bat 启动:
  1. Gateway (:18080)
  2. Alpha-ID (:8000)
  3. CDP 豆包捕获
```

### 5.2 Docker 生产环境

```yaml
docker-compose.yml 服务:
  db:         PostgreSQL (:5432)
  nebula:     Nebula (:2002)
  alphaid:    Alpha-ID (:8000)
  gateway:    Gateway (:18080)
```

依赖关系：
```
gateway → alphaid + nebula
alphaid → db
nebula → db
```

---

## 六、配置一览

### 6.1 环境变量

| 变量 | 服务 | 默认值 | 说明 |
|:-----|:-----|:-------|:-----|
| `ALPHAID_URL` | Gateway | `http://localhost:8000` | Alpha-ID 地址 |
| `NEBULA_URL` | Gateway | `http://localhost:2002` | Nebula 地址 |
| `ORCHESTRATOR_URL` | Gateway | `http://localhost:19090` | 编排器地址 |
| `NETAGENT_URL` | Gateway | `http://localhost:18180` | Net-Agent 地址 |
| `GATEWAY_PORT` | Gateway | `18080` | Gateway 端口 |
| `DEFAULT_ALPHA_ID` | 全局 | `` | 默认 Alpha-ID |
| `AUTH_MASTER_KEY` | Alpha-ID | - | JWT 签名密钥 |
| `DATABASE_URL` | Alpha-ID/Nebula | - | PostgreSQL 连接 |
| `FEISHU_APP_ID` | 飞书 Bot | - | 飞书应用 ID |
| `FEISHU_APP_SECRET` | 飞书 Bot | - | 飞书应用密钥 |

### 6.2 端口分配

| 端口 | 服务 | 协议 |
|:-----|:-----|:-----|
| 8000 | Alpha-ID | HTTP |
| 18080 | Gateway | HTTP |
| 2002 | Nebula | HTTP |
| 3001 | Flow/API | HTTP |
| 18180 | Net-Agent | HTTP |
| 19090 | Orchestrator | HTTP |
| 5432 | PostgreSQL | TCP |

---

## 七、开发指南

### 7.1 启动完整开发环境

```bash
# 方式 1：一键启动
D:\MW\start-all.bat

# 方式 2：Docker
docker compose up -d

# 方式 3：手动逐个启动
# Terminal 1: Alpha-ID
cd D:\MW\alphaid\projects
PYTHONPATH=src python -m uvicorn main:app --port 8000

# Terminal 2: Gateway
cd D:\MW\ghost-main\gateway
python app.py

# Terminal 3: 豆包捕获
cd D:\MW\ghost-capture
python cdp_poll.py
```

### 7.2 验证服务

```bash
# Gateway 健康检查
curl http://localhost:18080/health

# Alpha-ID 健康检查
curl http://localhost:8000/health

# API 文档
start http://localhost:18080/docs
```

### 7.3 运行测试

```bash
# Gateway 测试
cd D:\MW\ghost-main\gateway
python -m pytest tests/ -v

# Alpha-ID 测试
cd D:\MW\alphaid\projects
PYTHONPATH=src python -m pytest tests/test_registration.py -v
```

---

## 八、文档索引

### 8.1 架构文档

| 文档 | 内容 |
|:-----|:-----|
| `ECOSYSTEM.md`（本文） | 全局生态系统、组件串联 |
| `ARCHITECTURE.md` | 统一架构、服务地图、执行顺序 |
| `GATEWAY_API_REFERENCE.md` | Gateway 全部 32 个 API 端点 |
| `alphaid/projects/docs/architecture.md` | Alpha-ID 内部架构（DI 容器、双链记忆、TwinBrain、AgentLoop、A2A、中间件栈） |
| `alphaid/projects/docs/api-reference.md` | Alpha-ID 全部 ~30 个 API 端点参考 |

### 8.2 指南文档

| 文档 | 内容 |
|:-----|:-----|
| `guides/STARTUP.md` | 启动指南、配置参考、测试 |
| `guides/USER_GUIDE.md` | 用户手册、API 调用示例 |

### 8.3 设计文档

| 文档 | 内容 |
|:-----|:-----|
| `design/README.md` | Alpha-ID 产品介绍 |
| `design/ALPHA_ID_00-04.md` | Alpha-ID 设计系列 |
| `design/DESIGN_PHILOSOPHY.md` | 设计哲学 |

### 8.4 审计文档

| 文档 | 内容 |
|:-----|:-----|
| `EXPERT_DEEP_AUDIT_2026-07-27.md` | 深度审计报告 |
| `PROJECT_AUDIT_2026-07-27.md` | 项目审计报告 |

---

## 九、待完成事项

### 9.1 文档补齐

- [x] Alpha-ID 架构文档（`alphaid/projects/docs/architecture.md`）
- [x] Alpha-ID API 参考（`alphaid/projects/docs/api-reference.md`）
- [ ] 飞书 Bot 使用文档
- [ ] 桌面宠安装使用文档
- [ ] Ghost Capture 扩展开发文档
- [ ] Collector Daemon 配置文档
- [ ] Net-Agent API 参考
- [ ] Orchestrator 使用文档

### 9.2 架构优化

- [ ] AgentLoop → API 路由接通
- [ ] TwinBrain → AgentLoop 注入
- [ ] A2A → Gateway 路由
- [ ] 可观测性 → FastAPI 中间件
- [ ] Ghost.html 拆 3 文件
- [ ] 存储路径统一

### 9.3 部署完善

- [ ] Docker 生产配置
- [ ] CI/CD 流水线
- [ ] 监控告警
- [ ] 日志聚合
