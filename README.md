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
│  L2  身份管理层 — Alpha-ID                        ~32.6K 行 / 141文件 │
│  DID + 签名 + AgentLoop + 双链记忆 + TwinBrain + 采集 + CLI         │
├─────────────────────────────────────────────────────────────────────┤
│  L3  记忆知识库层                                                    │
│  双链记忆 + TwinBrain + Coala记忆 + 记忆防御 + Obsidian              │
├─────────────────────────────────────────────────────────────────────┤
│  L4  Agent调度层                                                     │
│  AgentLoop + Orchestrator + Tenant + Risk + Recovery + A2A          │
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
| Alpha-ID | 8000 | ~32.6K / 141文件 | ✅ 运行中 | 身份+记忆+AgentLoop 全栈核心 |
| Nebula | 2002 | ~7.7K / 67文件 | ✅ 运行中 | 工作流引擎+飞书WS+AI网关 |
| Gateway | 18080 | 1,857 / 17文件 | ✅ 运行中 | 统一网关 四层路由+限流+信封 |
| Ghost.html | — | 2,515 / 1文件 | ✅ 可用 | Web展示层(注册/仪表盘/聊天) |
| NURO 桌宠 | — | 1,719 / 7文件 | ✅ 可用 | 纯本地AI贾维斯(桌面悬浮精灵) |
| 豆包阅读器 | — | 1,055 / 5文件 | ✅ 可用 | LevelDB扫描→精炼→Obsidian |
| Flow/API | 3036 | ~4.4K TS | ⚠️ 部分 | 工作流/地图/Computer Use |

---

## 快速启动

```bash
# 1. Alpha-ID (身份+记忆+AgentLoop+NURO)
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
| **旧档归档** | [archive/md_old/](./archive/md_old/) | 历史文档（不再更新） |

---

## 四条使用主线

```
主线A（知识进）: 豆包聊天 → LevelDB扫描 → 豆包阅读器 → Gateway → Obsidian
主线B（能力用）: 对话飞书 → Gateway → Alpha-ID/Nebula/Flow
主线C（统一看）: 打开Ghost.html → Gateway → 后端
主线D（桌面伴）: NURO桌宠 → 本地Ollama + 双链记忆 + MCP
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
|:-----|:----|:-----|
| 2026-07-27 | 4.0 | 全面大修：修正行数、P0标记DONE、新增NURO/豆包板块 |
| 2026-07-25 | 3.0 | 全面审计：修正全部行数/路径/状态标记 |
| 2026-07-25 | 2.0 | 完整重写：整合5份旧文档+全部审计 |
| 2026-07-25 | 1.0 | 初始整合版 |
