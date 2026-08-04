<!-- STATUS: REFERENCE -->

# Ghost — Web4.0 人机共生基础设施

> 国内合规、以人为核心的 Web4.0 人机共生基础设施。
> 一人一生唯一 Alpha-ID + 双大脑架构 + A2A 智能体协同 + Obsidian 知识闭环。

---

## 架构全景

```
┌─────────────────────────────────────────────────────────────────────┐
│  L1  用户交互层                                                      │
│  Ghost.html(2.5K)  飞书WS(200L)  NURO桌宠(1.7K)  豆包阅读器(1.1K)    │
├─────────────────────────────────────────────────────────────────────┤
│  L2  身份管理层 — Alpha-ID                        ~35K+ 行 / 150+文件│
│  DID + 签名 + AgentLoop + 双链记忆 + TwinBrain + 采集 + CLI + 新模块│
├─────────────────────────────────────────────────────────────────────┤
│  L3  记忆知识库层                                                    │
│  双链记忆 + TwinBrain + Coala记忆 + 记忆防御 + Obsidian 双向同步     │
├─────────────────────────────────────────────────────────────────────┤
│  L4  Agent调度层                                                     │
│  AgentLoop + Orchestrator + Tenant + Risk + Recovery + A2A          │
│  + AgentFeed + SmartCapture + SelfEvolution (自进化循环)             │
├─────────────────────────────────────────────────────────────────────┤
│  L5  网关管控层 — Gateway :18080                  1,857 行 / 17文件  │
│  /v1/human/* /v1/agent/* /v1/internal/* /v1/net/*                   │
├─────────────────────────────────────────────────────────────────────┤
│  L6  底层通信层                                   AI Mesh (未开发)     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 组件速查

| 组件 | 端口 | 代码量 | 状态 | 本质 |
|:-----|:----:|:------:|:----:|:-----|
| Alpha-ID | 8000 | ~35K+ / 150+文件 | ✅ 运行中 | 身份+记忆+AgentLoop+新模块 全栈核心 |
| Nebula | 2002 | ~7.7K / 67文件 | ✅ 运行中 | 工作流引擎+飞书WS+AI网关 |
| Gateway | 18080 | 1,857 / 17文件 | ✅ 运行中 | 统一网关 四层路由+限流+信封 |
| Ghost.html | — | 2,515 / 1文件 | ✅ 可用 | Web展示层(注册/仪表盘/聊天) |
| NURO 桌宠 | — | 1,719 / 7文件 | ✅ 可用 | 纯本地AI贾维斯(桌面悬浮精灵) |
| 豆包阅读器 | — | 1,055 / 5文件 | ✅ 可用 | LevelDB扫描→精炼→Obsidian |
| Flow/API | 3036 | ~4.4K TS | ⚠️ 部分 | 工作流/地图/Computer Use |

---

## Alpha-ID 新模块 (v0.4.0)

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
| **豆包阅读器** | [ghost-main/docs/doubao-reader.md](./ghost-main/docs/doubao-reader.md) | LevelDB解析、知识精炼、Obsidian写入 |
| **端口速查** | [PORTS.md](./PORTS.md) | 所有服务端口、启动命令、Gateway 路由结构 |
| **旧档归档** | [archive/md_old/](./archive/md_old/) | 历史文档（不再更新） |

---

## 四条使用主线

```
主线A（知识进）: 豆包聊天 → LevelDB扫描 → 豆包阅读器 → Gateway → Obsidian
主线B（能力用）: 对话飞书 → Gateway → Alpha-ID/Nebula/Flow
主线C（统一看）: 打开Ghost.html → Gateway → 后端
主线D（桌面伴）: NURO桌宠 → 本地Ollama + 双链记忆 + MCP
主线E（自进化）: Orchestrator → Feed + Capture + Evolution → 持续学习
```

---

## 已确认决策

- 唯一官网 = Ghost.html
- 豆包 = 知识输入主入口（LevelDB扫描方案）
- 飞书 = 总对话助理（走Gateway）
- NURO = 纯本地AI（不依赖Gateway）
- 不用微信、不用Claude Code
- 不做：AI Mesh libp2p / Skill自进化 / A2A真实网络通信

---

## 变更记录

| 日期 | 版本 | 变更 |
|:-----|:----|:------|
| 2026-07-27 | 4.2 | 新增 ToolOrchestrator/CodexAPI/BaiduMap 3个模块，集成飞书代码模式，MCP 工具增至24个 |
| 2026-07-27 | 4.0 | 全面大修：修正行数、P0标记DONE、新增NURO/豆包板块 |
| 2026-07-25 | 3.0 | 全面审计：修正全部行数/路径/状态标记 |
| 2026-07-25 | 2.0 | 完整重写：整合5份旧文档+全部审计 |
| 2026-07-25 | 1.0 | 初始整合版 |
