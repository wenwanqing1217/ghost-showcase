<!-- STATUS: ACTIVE -->
<!-- 项目入口：快速了解 + 快速启动。详细架构见 GHOST.md。 -->

# Ghost Platform

Web4.0 人机共生基础设施。一人一生唯一 Alpha-ID + A2A 智能体协同。

## 快速启动

```bash
# 1. 克隆（含 submodule）
git clone --recursive <repo-url>
cd ghost-platform

# 2. 配置环境变量
cp DS/.env.example DS/.env
cp ghost-main/gateway/.env.example ghost-main/gateway/.env
cp alphaid/projects/.env.example alphaid/projects/.env

# 3. 启动所有服务
docker compose up -d

# 4. 验证
curl http://localhost:18080/health
curl http://localhost:8000/health
```

## 服务清单

| 服务 | 端口 | 说明 |
|:-----|:----:|:-----|
| Alpha-ID | 8000 | 身份层 + 记忆 + AgentLoop |
| Gateway | 18080 | 统一 API 网关 |
| Orchestrator | 19090 | 双工具协同调度 |
| Nebula | 2002 | 工作流引擎 |
| Flow | 3036 | 工作流编排 |
| Ghost DS | 3001 | 电商看板 |
| Net-Agent | 18180 | 网络管理 |
| Feishu Bot | — | 飞书 WebSocket Bot |
| Redis | 6379 | 缓存 + 事件总线 |
| PostgreSQL | 5432 | 持久化 |

## 关键端点

```
GET  /health                    — 服务健康检查
POST /v1/chat                   — 聊天（需 alpha_id + message）
POST /v1/human/chat             — 聊天（需 tenant 身份）
GET  /docs                      — API 文档
```

## 开发命令

```bash
make help     # 查看所有可用命令
make up       # 启动服务
make down     # 停止服务
make logs     # 查看日志
make test     # 运行测试
make lint     # 代码检查
```

## 文档

| 文档 | 用途 |
|:-----|:-----|
| `GHOST.md` | 项目唯一真相源（架构 + 术语 + 服务清单） |
| `AGENTS.md` | 项目级 AI Agent 指令（TERM 规则 + 死代码处理） |
| `DECISIONS.md` | 架构决策日志 |
| `PHASE1_PLAN.md` | 实施计划 |
| `CODEOWNERS` | 代码归属 |
| `CONTRIBUTING.md` | 贡献规范 |

## 当前状态

- 11/12 服务运行中（feishu-bot / feishu-consumer 需配置 `FEISHU_APP_ID` / `FEISHU_APP_SECRET`）
- `/v1/chat` 链路已验证可用
- CI 配置完整（GitHub Actions）


| 模块 | 文件 | 行数 | 状态 | 本质 |
|:-----|:-----|:----:|:----:|:-----|
| **Orchestrator** | `alpha_id/orchestrator.py` | ~24K | ✅ 运行中 | 总调度器：串联所有模块，5个后台循环 |
| **Smart Capture** | `alpha_id/smart_capture.py` | ~15K | ✅ 可用 | 智能采集：侦探不是搬运工，发现矛盾/卡住/偏离 |
| **Agent Feed** | `alpha_id/feed.py` | ~12K | ✅ 可用 | 资讯采集：GitHub/HN/ArXiv/RSS → Agent 学习 |
| **Self Evolution** | `alpha_id/self_evolution.py` | ~10K | ✅ 可用 | 自进化：从纠正中学习教训，定期审视偏好 |
| **Obsidian Bridge** | `alpha_id/obsidian_bridge.py` | ~10K | ✅ 可用 | Obsidian 双向同步：写入+读取+自动链接 |
| **NURO Bridge** | `alpha_id/nuro_bridge.py` | ~7.6K | ✅ 可用 | 桌宠连接：本地小模型 + 云端大模型 |
| **Feishu Bridge** | `alpha_id/feishu_bridge.py` | ~12K | ✅ 可用 | 飞书集成 + 代码模式（CodeRunner 3后端：atomcode/zcode/codex） |
| **MCP Tools** | `alpha_id/mcp_tools.py` | ~18K | ✅ 可用 | 24个 MCP 工具暴露全部新模块能力 |
| **Orchestrator CLI** | `alpha_id/orchestrate_cli.py` | ~11K | ✅ 可用 | 一键启动总调度器 |
| **Tool Orchestrator** | `alpha_id/tool_orchestrator.py` | ~8K | ✅ 可用 | 编程工具协同调度：串行/并行 + 线程池 + TTL 清理 |
| **Codex API** | `alpha_id/codex_api.py` | ~6K | ✅ 可用 | Codex CLI HTTP 接口：atomcode/codex 后端 + API Key 认证 |
| **Baidu Map** | `alpha_id/skills/baidu_ai_map.py` | ~7K | ✅ 可用 | 百度地图 AI 技能：地点/路线/天气/地理编码 |

### 新模块核心循环

```
┌─────────────────────────────────────────────────────────────┐
│                   Master Orchestrator                        │
│                                                             │
│  AgentFeed ──→ evaluate_relevance ──→ learn/sediment       │
│       │                         │                           │
│       ▼                         ▼                           │
│  SelfEvolution ←── lessons ── SmartCapture ──→ observe     │
│       │                            │                        │
│       ▼                            ▼                        │
│  ObsidianBridge ←── notes ── FeishuBridge ──→ work_ctx    │
│       │                            │                        │
│       ▼                            ▼                        │
│  NUROBridge ←── local/cloud ── TwinBrain ──→ think         │
│       │                            │                        │
│       └────────── EventBus ─────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 快速启动

```bash
# 1. Alpha-ID (身份+记忆+AgentLoop+NURO+新模块)
cd D:\MW\alphaid\projects
python -m uvicorn entrypoints.api:app --host 0.0.0.0 --port 8000

# 2. Nebula (工作流+飞书WS)
cd D:\MW\nebula
python -m uvicorn src.mindflow_map.main:app --host 0.0.0.0 --port 2002

# 3. Gateway (统一网关)
cd D:\MW\ghost-main\gateway
python -m uvicorn app:app --host 0.0.0.0 --port 18080
```

### 验证

```bash
curl http://localhost:8000/api/health      # Alpha-ID
curl http://localhost:2002/health          # Nebula
curl http://localhost:18080/v1/internal/health  # Gateway
```

### 启动 Orchestrator（新模块总调度）

```bash
cd D:\MW\alphaid\projects

# 基础启动（Feed + Capture + NURO + Evolution）
python -m alpha_id.orchestrate_cli start

# 完整启用（包括 Obsidian 和飞书）
python -m alpha_id.orchestrate_cli start \
    --obsidian-vault "D:/MyVault" \
    --git-repos "D:/MW,D:/Projects" \
    --feishu-app-id "cli_xxx" \
    --feishu-app-secret "xxx"

# 查看状态
python -m alpha_id.orchestrate_cli status

# 单次资讯拉取
python -m alpha_id.orchestrate_cli feed

# 单次采集扫描
python -m alpha_id.orchestrate_cli scan

# NURO 聊天
python -m alpha_id.orchestrate_cli chat "你好"
```

### 飞书代码模式

飞书桥接支持**对话模式**和**写代码模式**切换，代码模式支持 3 个后端：

| 后端 | 说明 | 特点 |
|:-----|:-----|:-----|
| `atomcode` | AtomCode CLI（默认） | AtomGit 免费额度，deepseek-v4-flash |
| `zcode` | ZCode CLI | GLM / LongCat 模型 |
| `codex` | Codex CLI | 桌面版，仅限本机 |

**飞书命令**：
```
/mode                — 切换对话/代码模式
/mode code           — 进入代码模式（自动执行编程任务）
/mode chat           — 回到对话模式
/backend list        — 列出可用后端
/backend atomcode    — 切换到指定后端
/status              — 查看当前模式和后端
/code 写个爬虫       — 显式执行代码任务
```

**代码示例**：
```python
from alpha_id.feishu_bridge import FeishuBridge

bridge = FeishuBridge(app_id="xxx", app_secret="xxx")
bridge.set_mode(chat_id, FeishuBridge.CODE)  # 进入代码模式
bridge.set_mode(chat_id, FeishuBridge.CHAT)  # 回到对话模式
```

### NURO 桌宠单独启动

```bash
cd D:\MW\alphaid\projects
python -m entrypoints.cli          # 正常启动
python -m entrypoints.cli --check  # 环境检测
install_deskpet.bat                # 一键安装
```

---

## 文档索引

| 文档 | 位置 | 内容 |
|:-----|:-----|:-----|
| **项目宪法** | [GHOST.md](./GHOST.md) | 完整框架、六层架构、P0/P1/P2任务、启动指南 |
| **NURO 桌宠** | [alphaid/projects/docs/nuro-desktop-pet.md](./alphaid/projects/docs/nuro-desktop-pet.md) | 桌面精灵架构、14步启动、语音链路、VRAM预算 |
| **Ghost.html 前端** | [alphaid/projects/docs/ghost-frontend.md](./alphaid/projects/docs/ghost-frontend.md) | 两视图架构、API调用、注册流程 |
| **端口速查** | [PORTS.md](./PORTS.md) | 所有服务端口、启动命令、Gateway 路由结构 |
| **旧档归档** | [archive/md_old/](./archive/md_old/) | 历史文档（不再更新） |

---

## 四条使用主线

```
主线A（能力用）: 对话飞书 → Gateway → Alpha-ID/Nebula/Flow
主线B（统一看）: 打开Ghost.html → Gateway → 后端
主线C（桌面伴）: NURO桌宠 → 本地Ollama + 双链记忆 + MCP
主线D（自进化）: Orchestrator → Memory + Evolution → 持续学习
```

---

## 已确认决策

- 唯一官网 = Ghost.html
- 飞书 = 总对话助理（走Gateway）
- NURO = 纯本地AI（不依赖Gateway）
- 不用微信、不用Claude Code
- 不做：AI Mesh libp2p / Skill自进化 / A2A真实网络通信

---

## 变更记录

| 日期 | 版本 | 变更 |
|:-----|:----|:------|
| 2026-07-27 | 4.2 | 新增 ToolOrchestrator/CodexAPI/BaiduMap 3个模块，集成飞书代码模式，MCP 工具增至24个 |
| 2026-07-27 | 4.0 | 全面大修：修正行数、P0标记DONE、新增NURO板块 |
| 2026-07-25 | 3.0 | 全面审计：修正全部行数/路径/状态标记 |
| 2026-07-25 | 2.0 | 完整重写：整合5份旧文档+全部审计 |
| 2026-07-25 | 1.0 | 初始整合版 |
