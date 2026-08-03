# Ghost 代码资产地图 · Code Base Map v0.1

> 用途：任何人在改代码前，先看这里。  
> 目标：10 分钟内知道“这个 repo 里每个部分是干什么的、主链在哪、现在该碰哪里”。

---

## 1. 全局阅读顺序

建议按这个顺序读：

1. docs/planning/GHOST_COMPLETE_MASTER_PLAN.md — 先理解最终定位
2. docs/planning/PHASE1_MINIMUM_TASKBOOK.md — 再理解当前最小执行边界
3. README.md — 项目旧描述，只当背景参考
4. ARCHITECTURE.md — 架构旧文档，可核对历史结构
5. 本文件 — 代码资产地图
6. 下文“主链路代码” — 动手前必读
7. 其他目录 — 按任务索引查找，不要散读

---

## 2. 目录职责总表

| 目录 | 职责 | 现状 | 现在能碰吗 |
|:---|:---|:---|:---|
| lphaid/projects/src/core | 身份/记忆/A2A/审计/配置核心 | 主资产 | ✅ Phase1 可动 |
| lphaid/projects/src/api | Alpha-ID REST 路由 | 主资产 | ✅ Phase1 可动 |
| lphaid/projects/src/entrypoints | 启动入口、CLI、MCP、NURO | 主资产 | ✅ 仅最小必要修改 |
| lphaid/projects/src/alpha_id | 高层桥接/模板/CLI | 主资产 | ⚠️ 慎改 |
| lphaid/projects/src/mindflow | 本地 MindFlow 引擎 | 旁支资产 | ❌ 先冻结 |
| lphaid/projects/src/fairy | NURO 桌宠人设/语音 | 旁支资产 | ❌ 先冻结 |
| lphaid/projects/src/tools | 桌面控制/OCR/身份工具 | 旁支资产 | ❌ 先冻结 |
| ghost-main/gateway | Gateway 统一入口 | 主资产 | ✅ Phase1 可动 |
| ghost-main/doubao_reader | 豆包日志读取/Obsidian 写入 | 旁支资产 | ❌ 先冻结 |
| ghost-main/net_agent_server | 路由器管理服务 | 旁支资产 | ❌ 先冻结 |
| ghost-main/net_client | 网络巡检客户端 | 旁支资产 | ❌ 先冻结 |
| 
ebula | 工作流/飞书/自动化服务 | 旁支资产 | ❌ 先冻结 |
| low | MindFlow 前端与 API | 旁支资产 | ❌ 先冻结 |
| orchestrator | 双工具编排器 | 旁支资产 | ❌ 先冻结 |
| ghost-capture | 豆包浏览器扩展 | 旁支资产 | ❌ 先冻结 |
| docs | 设计/审计/路线/规划 | 决策资料 | ✅ 可读 |
| scripts | 脚本资产 | 参考资产 | ⚠️ 仅查阅 |

---

## 3. 主链路代码索引（Phase 1 只碰这里）

### 3.1 身份与 A2A
- lphaid/projects/src/core/settings.py — 全局配置
- lphaid/projects/src/main.py — Alpha-ID 主服务入口
- lphaid/projects/src/core/a2a.py — A2A 协议核心
- lphaid/projects/src/api/identity.py — 注册/登录/refresh
- lphaid/projects/src/api/dual_chain.py — 双链记忆读写
- lphaid/projects/src/api/observability.py — 就绪/指标

### 3.2 Gateway
- ghost-main/gateway/app.py — Gateway 主服务、中间件、路由挂载
- ghost-main/gateway/config.py — 后端地址与 CORS 配置
- ghost-main/gateway/routes/agent.py — Agent 路由
- ghost-main/gateway/services/proxy.py — 代理/统一响应/重试
- ghost-main/gateway/services/observability.py — 指标采集

### 3.3 前端入口（只读不改）
- lphaid/projects/src/alpha_id/web.py — Alpha-ID 演示页
- lphaid/projects/src/alpha_id/templates/ghost.html — Ghost 演示页

---

## 4. 关键技术对象说明

### 4.1 Identity
- UserIdentityManager
- DIDRegistry
- JWT/CSRF/RateLimit middleware
- 核心职责：谁可以进入系统、对应哪个 alpha_id

### 4.2 Memory
- DualChainManager
- MemoryStore
- 核心职责：存知识链/私链、支持查询统计、负责回写

### 4.3 A2A
- A2AServer
- A2AClient
- A2ASkillRegistry
- A2ASigner
- 核心职责：注册、发现、调用、签名、幂等

### 4.4 Governance
- 审计当前没有统一单例，准备收敛
- 授权当前只有弱策略，准备在 Phase1 做最小 schema

### 4.5 Gateway
- 不是业务层，是统一入口
- 不新增业务逻辑，只做路由、CORS、日志、限流、代理

---

## 5. 资产复用映射（快速版）

| 资产 | 命运 |
|:---|:---|
| Alpha-ID 主服务 | 保留为主服务 |
| A2A 协议 | 保留并收敛成唯一入口 |
| 双链记忆 | 保留为主记忆层 |
| Gateway | 保留并瘦身 |
| MCP Server | 保留为接入壳 |
| NURO | 冻结/归档 |
| MindFlow | 冻结/归档 |
| 豆包 | 冻结/归档 |
| Net-Agent | 冻结/归档 |
| Orchestrator | 冻结/归档 |
| Flow | 冻结/归档 |

---

## 6. 给后续 agent 的执行口诀

- 先看 GHOST_COMPLETE_MASTER_PLAN.md
- 再看 PHASE1_MINIMUM_TASKBOOK.md
- 再看本章节
- 只改主链路列出的文件
- 不要顺手清理旁支
- 不要重构非主链代码
- 不要新增前端页面
- 不确定时，只加注释，不改结构

---

*本文件只用于“知道代码是干什么的”，不用于定义产品功能。*
*产品功能以 GHOST_COMPLETE_MASTER_PLAN.md 为准。*
