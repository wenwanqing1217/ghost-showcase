<!-- ════════════════════════════════════════════════════════════════════ -->
<!-- STATUS: ARCHIVED → 历史审计报告                                        -->
<!-- 本文件为 2026-07-26 Ghost 项目完整问题清单。核心发现已整合到 GHOST.md。 -->
<!-- 保留原因：问题清单细节有价值，但概览和优先级已在 GHOST.md 第 8 节。     -->
<!-- ════════════════════════════════════════════════════════════════════ -->

# Ghost 项目完整问题清单与战略解决方案

> 审计日期: 2026-07-26 | 覆盖范围: 根目录 + 全部子模块

---

## 第一部分：全部问题清单

### A. 仓库卫生问题（7项）

| # | 问题 | 位置 | 严重度 |
|:-:|:-----|:------|:------:|
| A1 | 22 个调试文件在磁盘上未清理 | `_*.txt`, `_*.log`, `_doubao_*_copy/` | 🟢 |
| A2 | 9 个调试文件被提交到 git | `final_reply.txt`, `gateway_debug.txt` 等在 alphaid/projects | 🟡 |
| A3 | 11 个一次性修复脚本在根目录 | `fix_*.py`, `fix_*.js` | 🟢 |
| A4 | `.gitignore` 没覆盖 `_doubao_*` 目录 | 3.4MB LevelDB 副本在根目录 | 🟢 |
| A5 | 两个独立的 `.env` 仍标记"废弃"但内容未清除 | `alphaid/projects/.env` 含真实密钥 | 🔴 |
| A6 | `alphaid_restart.log`, `flow_api.log` 等日志文件 | 根目录 | 🟢 |
| A7 | `__pycache__/` 目录被提交 | `alphaid/projects/` 下 | 🟢 |

### B. 架构问题（8项）

| # | 问题 | 说明 |
|:-:|:-----|:------|
| B1 | 5 种数据读写方式 | Container DI / 模块级 sqlite3 / 文件 os.walk / JSON 文件 / SQLite 直连 |
| B2 | 双栈撕裂 | Python alphaid + Node Flow，Flow 在 Windows 不能后台驻留 |
| B3 | Ghost.html 4300 行单体文件 | CSS/HTML/JS 全在一个文件，不可测试 |
| B4 | 9 个工作台面板仅 2 个有数据 | 意图、路由、决策、Agent、日志、设置面板全是空壳或硬编码 |
| B5 | `core/` 目录完全孤立 | TypeScript 项目，与 Ghost 没有任何实际连接 |
| B6 | `codex-remote/` 孤立 | 可能是实验性项目，无人维护 |
| B7 | 两套 CORS 配置 | Gateway 的 `allow_origins` 和 alphaid 的 `origins` 各自独立 |
| B8 | Docker Compose 文件从未验证 | 4 个 `docker-compose*.yml`，从未启动过 |

### C. 数据问题（5项）

| # | 问题 | 说明 |
|:-:|:-----|:------|
| C1 | 两个 `alpha_id.db` | 根目录 `assets/` 和 `alphaid/projects/assets/` 各一份，可能不同步 |
| C2 | SMS 验证码存储直连 SQLite | 没有使用 Container DI，测试无法隔离 |
| C3 | 没有 schema 版本控制 | 数据库变更靠手动，无 migration |
| C4 | 用户数据 user_id 格式不稳定 | `user_20260726_130219_Alpha9283599` 依赖时间戳+Alpha-ID |
| C5 | 未实现在线用户查询优化 | `collections` 表是 key-value 模式 |

### D. 安全问题（6项）

| # | 问题 | 说明 |
|:-:|:-----|:------|
| D1 | `alphaid/projects/.env` 含真实密钥 | AUTH_MASTER_KEY、OPENAI_API_KEY 等在生产级密钥在已提交文件里 |
| D2 | JWT 密钥有默认值 | `validate_master_key()` 有 fallback |
| D3 | Gateway dev 模式 CORS 通配符 | 生产环境有保护，但 dev 完全开放 |
| D4 | 没有请求频率限制 | 注册/Gateway 等端点无全局限流 |
| D5 | 敏感信息可能写入日志 | SMS 验证码、支付宝密钥等 |
| D6 | `AUTH_MASTER_KEY` 硬编码在 `.env` | 应该只从环境变量读取 |

### E. 测试与 CI（4项）

| # | 问题 | 说明 |
|:-:|:-----|:------|
| E1 | 3 个测试文件之前收集阶段就崩溃 | 已在本次修复，但根源是删了模块没删测试 |
| E2 | CI 从未在 GitHub 上真正跑过 | `.github/workflows/ci.yml` 存在但无绿色勾 |
| E3 | `test_aid_daemon.py` 仍引用已删模块 | `entrypoints.daemon` 在 conftest 中的引用已修复，但 test_aid_daemon.py 本身可能仍有问题 |
| E4 | 新功能测试覆盖率低 | 注册 8 个测试、SMS 1 个、health 2 个——远不够 |

### F. 部署问题（3项）

| # | 问题 | 说明 |
|:-:|:-----|:------|
| F1 | Python 后端无部署方案 | Vercel 仅前端，alphaid/Gateway/Nebula 全部本机 |
| F2 | SQLite 不能用于 Serverless | 部署到生产必须 PostgreSQL |
| F3 | 没有 `.dockerignore` | `node_modules/`、`__pycache__/` 等会被打包进镜像 |

### G. 商业/未来规划问题（3项）

| # | 问题 | 说明 |
|:-:|:-----|:------|
| G1 | 目标用户未定义 | 不知道给谁用就无法做产品决策 |
| G2 | 没有定价模型 | GHOST.md 提到"商业生态"但无方案 |
| G3 | 法律合规 | 收集用户 DID/手机号/人脸，涉及《个人信息保护法》，无隐私政策 |

---

## 第二部分：战略级解决方案

### 原则

1. **先删后建** — 没人用的代码先砍掉，再决定要不要重写
2. **先通后优** — 一条用户路径跑通再考虑优化，而不是全面开花
3. **先本地后云端** — 本地能闭环再考虑部署

### Phase 0：大扫除（1天）

**目标：仓库干净，不留遗留文件**

| 操作 | 涉及问题 |
|:-----|:---------|
| 删掉 22 个根目录调试文件 + 11 个 fix 脚本 | A1, A3, A4 |
| 从 git 历史中移除 9 个已提交的调试文件 | A2 |
| 移除两个废弃 `.env` 中的真实密钥 | D1 |
| 删掉 `core/` 目录 | B5 |
| 删掉 `codex-remote/` 目录 | B6 |
| 删掉 `docs/` 空目录 | — |
| 删掉 `alphaid/projects/` 下已提交的 txt 调试文件 | A2 |

### Phase 1：止血（3-5天）

**目标：代码统一、可测试、一条用户路径走通**

| 操作 | 涉及问题 |
|:-----|:---------|
| **砍 Flow API** | B2 — 注册已迁到 alphaid，AI 路由暂无人用 |
| **registration.py 改用 Container DI** | C2, B1 — 不再直连 SQLite |
| **统一 storage 层** | C1 — 确保只有一个 `alpha_id.db` |
| **Ghost.html 拆 3 文件** | B3 — CSS → `.css`，JS → `.js`，HTML → `ghost.html` |
| **删除孤立目录 core/, codex-remote/** | B5, B6 |
| **编写 Ghost.html 工作台面板空壳标记** | B4 — "开发中"标签替代硬编码假数据 |
| **跑通 GitHub Actions CI** | E2 — 至少一次绿色勾 |
| **添加 pytest 到 CI** | E1, E4 |

### Phase 2：上生产（2周）

**目标：可以在公网访问**

| 操作 | 涉及问题 |
|:-----|:---------|
| 决定部署方案：Railway / Fly.io / 轻量服务器 | F1 |
| SQLite → PostgreSQL | F2, C3 |
| 必须的 `.dockerignore` + Docker 流程 | F3 |
| CORS 生产环境白名单 | D3 |
| 移除 dev 模式通配符 | D3 |
| 添加全局请求限流 | D4 |
| 编写隐私政策 + 用户协议 | G3 |
| 公网发布 | — |

### Phase 3：做产品（1-2月）

**目标：有人愿意用**

| 操作 | 涉及问题 |
|:-----|:---------|
| 定义目标用户 + MVP | G1 |
| Ghost.html 用框架重写 | B3 — 彻底解决单体问题 |
| 工作台 9 个面板全部接数据 | B4 |
| 豆包知识采集插件 | G1 — GHOST.md 核心功能 |
| 飞书机器人稳定运行 | G1 |
| 定价模型设计 | G2 |

---

## 第三部分：必须立即做的 3 件事

1. **删掉废弃 .env 里的密钥** — `alphaid/projects/.env` 里的 `OPENAI_API_KEY` 和 `AUTH_MASTER_KEY` 已提交到 git，任何人都能看到
2. **删掉调试文件和孤立目录** — 22 个调试文件 + `core/` + `codex-remote/` 不应该在仓库里
3. **选一个部署方案** — 所有其他问题都不重要如果项目只在本机能跑

---

## 第四部分：愿景-代码差距分析

### 3 份文档描述的功能 vs 当前代码实现

| 功能 | 出自文档 | 代码状态 | 差距 | 实现方案 |
|:-----|:---------|:---------|:-----|:---------|
| **实名 DID 注册（身份证+人脸）** | Web4.0文档§1.3 | 🟡 Alpha-ID 已注册，但走演示模式 | 需接真实身份证核验 | 对接阿里云/腾讯云实名认证 API |
| **双链记忆（私链+知链）** | 两份文档均有 | 🟢 完整实现 | 无差距 | 已可用 |
| **双层网关隔离** | Web4.0文档§2.2 | 🟡 Gateway 单层 | 只有公共网关，缺私有网关 | 新建私有网关或拆分当前 Gateway |
| **MCP 技能适配** | Web4.0文档§4.2 | 🔴 0 行代码 | 整个模块不存在 | 从零搭建 MCP 注册/发现/调用体系 |
| **A2A 智能体协作** | Web4.0文档§4.2 | 🟡 a2a.py 有代码但 0 引用 | 写完了但没接 | 接入 AgentLoop + Gateway |
| **八大行业知识库** | Web4.0文档§4.2 | 🔴 0 行代码 | 不存在 | 每条行业需独立爬虫+清洗+入库 |
| **Obsidian 双向同步** | 两份文档均有 | 🔴 0 行代码 | Gateway 能搜但不会写 | 开发 Obsidian 插件 |
| **豆包知识采集** | GHOST_DOUBAO_DESIGN.md | 🔴 ghost-capture/ 已删除 | 整个模块没了 | 重建浏览器扩展 |
| **星点积分/支付** | Web4.0文档§4.4 | 🔴 0 行代码 | 不存在 | 接入支付宝/微信支付 SDK |
| **飞书机器人总助** | Web4.0文档§2.4 | 🟡 nebula 有代码但未稳定运行 | 机器人能起但没人用 | 让 nebula 常驻 + 联调 |
| **技能市场/创作者后台** | Web4.0文档§4.4 | 🔴 0 行代码 | 不存在 | 前端+后端+分账全新建 |
| **AgentLoop 主循环** | core/agent.py | 🟡 813 行完整但 0 引用 | 写完了没接入口 | 接入 API 路由 |
| **TwinBrain 状态机** | core/twin_brain.py | 🟡 690 行完整但 0 引用 | 写完了没通 | 接入 AgentLoop |
| **风控引擎** | core/risk_engine.py | 🟢 被引用 | 无差距 | 已可用 |
| **故障恢复** | core/recovery.py | 🟡 534 行但 0 引用 | 写完了没人用 | 接入 Gateway |
| **可观测性** | core/observability.py | 🟡 553 行但 0 引用 | 写完了没人用 | 接入 API 中间件 |

### 核心发现

**文档说的 34 项功能，代码只实现了 4 项（约 12%）。**

已经实现的部分：DID 身份、双链记忆、Gateway 网关、注册流程。
文档描述但完全没碰的部分：知识库、支付、商业生态、Obsidian 同步、技能市场。
代码有但没接的部分：AgentLoop、TwinBrain、A2A、采集器、mindflow 工作流。

### 差距总结图

```
                                     已实现 ▓▓░░░░░░░░ 12%
                                     已写未接 ▓▓▓░░░░░░░ 18%
                                     未开始 ▓▓▓▓▓▓▓░░░ 70%

