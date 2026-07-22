# Ghost 项目审计与重组方案

> **日期**: 2026-07-23 | **状态**: 待执行
> **目的**: 基于 GHOST_ECO_MASTER.md 的规划, 对现有全部资产做审计, 找出"不该做的"、"该调整的"、"缺失的", 并给出清理后的项目结构。

---

## 一、审计方法论

审计基于三个维度:

| 维度 | 问题 | 判断标准 |
|------|------|---------|
| **一致性** | 现状和 GHOST_ECO_MASTER.md 规划的差距是什么? | 规划说了要做 X, 实际做了吗? |
| **健康度** | 每个子项目的代码质量和结构是否合理? | 有无过度工程、安全漏洞、测试虚胖? |
| **完整性** | 从"能跑"到"能上线", 缺了什么模块? | P0 规划中的模块, 哪个还没建? |

---

## 二、文档层审计

### 2.1 问题: docs/ 目录有 17 个 MD 文件, 严重冗余

当前文件:

| 文件 | 大小 | 状态 | 处理建议 |
|------|------|------|---------|
| `GHOST_ECO_MASTER.md` | 45KB | ✅ **总纲** | 保留, 作为唯一决策文档 |
| `ECOSYSTEM_ARCHITECTURE.md` | 72KB | 🔴 已被总纲吸收 | **归档**或删除 |
| `AID_FULL_INTEGRATION.md` | 33KB | 🔴 已被总纲吸收 | **归档**或删除 |
| `PLATFORM_VISION_AND_DIRECTION.md` | 13KB | 🔴 已被总纲吸收 | **归档**或删除 |
| `DECISION_SKILLS.md` | 9KB | 🔴 已被总纲吸收 | **归档**或删除 |
| `RENOVATION_PLAN.md` | 13KB | 🟡 部分有效 | 核心内容合并到总纲十三节 |
| `ROOT_AUDIT.md` | 12KB | 🟡 部分有效 | 核心内容合并到本审计文档 |
| `ACCEPTANCE_REPORT.md` | 15KB | 🟡 部分有效 | 保留为验收记录 |
| `DEPLOYMENT.md` | 5KB | 🟡 部署相关 | 保留, 更新为最新结构 |
| `CI_CD.md` | 4KB | 🟡 CI/CD 相关 | 保留, 更新为最新结构 |
| `DATABASE_MIGRATION.md` | 4KB | 🟡 数据库相关 | 保留 |
| `CROSS_SERVICE_INTEGRATION.md` | 3KB | 🟡 跨服务相关 | 保留 |
| `aid-mindflow-讨论纪要.md` | 45KB | 🟡 历史记录 | **归档** |
| `MIND_FLOW_EXECUTION_PLAN.md` | 12KB | 🟡 执行计划 | 合并到总纲十一节 |
| `ds-aid-mindflowmap-checklist.md` | 2KB | 🟡 检查清单 | 合并或归档 |
| `mindflow-blocks-interview.md` | 1KB | 🟡 面试相关 | 归档 |
| `screenshot_response.json` | 6KB | 🔴 临时文件 | **删除** |

### 2.2 处理方案

```
删除 (已完全被总纲吸收):
  ❌ ECOSYSTEM_ARCHITECTURE.md  → GHOST_ECO_MASTER.md §8
  ❌ AID_FULL_INTEGRATION.md    → GHOST_ECO_MASTER.md §2
  ❌ PLATFORM_VISION_AND_DIRECTION.md → GHOST_ECO_MASTER.md §1
  ❌ DECISION_SKILLS.md         → GHOST_ECO_MASTER.md §9
  ❌ screenshot_response.json    → 临时文件

归档到 docs/archive/ (保留但不活跃):
  📦 aid-mindflow-讨论纪要.md
  📦 mindflow-blocks-interview.md

保留并更新 (仍然活跃):
  ✅ GHOST_ECO_MASTER.md           — 总纲, 持续更新
  ✅ PROJECT_AUDIT_AND_REORGANIZATION.md — 本文档
  ✅ DEPLOYMENT.md              — 更新为新的命名和结构
  ✅ CI_CD.md                   — 更新 CI 流程
  ✅ DATABASE_MIGRATION.md      — 保留
  ✅ CROSS_SERVICE_INTEGRATION.md — 保留
  ✅ ACCEPTANCE_REPORT.md       — 保留为验收记录
```

**归档后 docs/ 从 17 个文件降到 8 个活跃文件。**

---

## 三、代码层审计

### 3.1 AID (Alpha-ID) — 核心项目

#### 不该做的 ❌

| 问题 | 位置 | 原因 | 处理 |
|------|------|------|------|
| **三个 DID 实现并存** | `alpha_id/did.py`(有bug), `core/did.py`(最小), `alpha_id/signer.py`(实际用) | 维护成本高, 混乱 | 只保留 signer.py, 标注其他两个 @deprecated |
| **928 个测试大量虚胖** | 大量边界条件测试(空串/超长/中文) | 不增加信心, 只增加维护成本 | 清理到 < 400 个核心测试 |
| **fairy_agent.py 29KB 空壳** | `alpha_id/fairy_agent.py` | try/except 探测依赖, HAS_SCREEN 等全 False | 删除或重写为真正可用的模块 |
| **alpha_id 目录过度膨胀** | `alpha_id/` 30+ 文件, 包含 collectors/mining/profile/skill_signer/social 等 | 每个文件都是一套独立系统 | 按 MW_ECO_MASTER §三 重新规划, 只保留身份相关 |
| **autopilot 100KB 过度工程** | `alpha_id/autopilot/` 16 文件 | 自改进循环远超个人项目合理范围 | 砍到 3 个文件以内, 或直接删除 |

#### 该调整的 🔧

| 问题 | 调整方案 | 优先级 |
|------|---------|--------|
| `core/` 与 `alpha_id/` 两个灵魂 | 统一为单一 `aid/` 包, 36 人时 | 🔴 P0 |
| 身份验证缺失 | 接入支付宝/微信实名认证 API | 🔴 P0 |
| 私链加密未实现 | 实现 AES-256-GCM 本地加密 | 🔴 P0 |
| Token 防护未实现 | 五层防护 (日预算/单次上限/速率/睡眠/告警) | 🔴 P0 |
| MCP Server 返回 mock | 接入真实 Profile 数据 | 🟡 P1 |
| CLI 命令不完整 | 实现 aid init/collect/profile show | 🔴 P0 |
| 测试质量低 | 删除低价值测试, 增加端到端测试 | 🟡 P1 |

#### 缺失的 🆕

| 模块 | 说明 | 优先级 |
|------|------|--------|
| **身份验证模块** | 支付宝/微信 二要素 + 人脸活体 | 🔴 P0 |
| **Token 经济模块** | 五层防护 + 计费引擎 | 🔴 P0 |
| **私链加密模块** | 本地 SQLite + AES-256-GCM | 🔴 P0 |
| **知链 Obsidian 模块** | Markdown 输出 + vault 同步 | 🟡 P1 |
| **导入器** | ChatGPT 导出 → Profile | 🔴 P0 |
| **Agent 注册模块** | Datasheet 提交 + Trial Call | 🟡 P1 |
| **凭证保险库** | 加密存储 + 临时授权 | 🟡 P1 |
| **REST API** | 总纲 §七 定义的全部端点 | 🟡 P1 |

### 3.2 mindflow-map — 工作流引擎

#### 不该做的 ❌

| 问题 | 位置 | 原因 | 处理 |
|------|------|------|------|
| **autopilot 100KB 过度工程** | `src/mindflow_map/autopilot/` | self-loop 自改进远超合理范围 | 砍到 3 个文件以内 |
| **secrets 过度设计** | `src/mindflow_map/secrets/` | env/K8s/Vault 三种 provider, 实际只用 env | 只保留 env |
| **抖音自动化跑不通** | `src/mindflow_map/automation/` | Playwright cookie 注入, 实际需开放平台 API | 标记为 @experimental |
| **百度地图/飞书/微信框架在但无 Key** | `src/mindflow_map/integration/` | 全是占位代码 | 标记为 @placeholder |

#### 该调整的 🔧

| 问题 | 调整方案 | 优先级 |
|------|---------|--------|
| 与 mindflow 功能重叠 | 明确分工: mindflow-map = 工作流引擎, mindflow = Web 前端 | 🟡 P1 |
| 138 个文件 | 清理 autopilot 和 secrets 后约 80 个 | 🟡 P1 |

#### 缺失的 🆕

| 模块 | 说明 | 优先级 |
|------|------|--------|
| **AID 身份集成** | 工作流引擎应使用 Alpha-ID 做用户识别 | 🟡 P1 |

### 3.3 DS — 电商 Agent

#### 不该做的 ❌

| 问题 | 位置 | 原因 | 处理 |
|------|------|------|------|
| **测试数字有水分** | `src/` 下 8 个 .test.ts, 其余匹配到 node_modules | 虚报测试数 | 修正测试统计 |
| **middleware 开发环境安全漏洞** | `src/lib/middleware.ts` | API_KEY 未配置时直接放行 | 修复: 开发环境也需认证 |

#### 该调整的 🔧

| 问题 | 调整方案 | 优先级 |
|------|---------|--------|
| 3 个 Agent 本质是 prompt template | 明确为"轻量 Agent", 不强求复杂 | 🟢 可接受 |

#### 缺失的 🆕

| 模块 | 说明 | 优先级 |
|------|------|--------|
| **AID 身份集成** | 电商 Agent 应读取用户 Profile | 🟡 P1 |
| **Shopify 真实数据** | 目前框架在但无真实店铺 | 🟡 P1 |

### 3.4 zcode-brain — 角色匹配

#### 不该做的 ❌

| 问题 | 位置 | 原因 | 处理 |
|------|------|------|------|
| **README 描述远超实际** | `README.md` | "智能代理编排系统"实际是关键词匹配 | 修正 README, 诚实描述 |

#### 该调整的 🔧

| 问题 | 调整方案 | 优先级 |
|------|---------|--------|
| 代码本身简洁诚实 | 保持现状, 作为 prompt 组装工具 | 🟢 可接受 |

### 3.5 ai综艺 — 内容前端

#### 不该做的 ❌

| 问题 | 位置 | 原因 | 处理 |
|------|------|------|------|
| **中文目录名** | `ai综艺/` | Linux 部署编码问题 | **重命名**为 `stage` |
| **无后端无测试** | 整个项目 | 纯前端 Demo | 明确为"展示前端", 不纳入核心 |

#### 该调整的 🔧

| 问题 | 调整方案 | 优先级 |
|------|---------|--------|
| 定位不清 | 作为"内容创作 Agent 展示前端", 不独立发展 | 🟡 P1 |

### 3.6 mindflow — 双端架构

#### 不该做的 ❌

| 问题 | 位置 | 原因 | 处理 |
|------|------|------|------|
| **与 mindflow-map 功能重叠** | 整个项目 | 两个"工作流"项目 | 明确分工或合并 |

#### 该调整的 🔧

| 问题 | 调整方案 | 优先级 |
|------|---------|--------|
| 和 mindflow-map 关系不明 | mindflow = Web 前端门户, mindflow-map = 工作流引擎 | 🟡 P1 |

---

## 四、基础设施审计

### 4.1 当前基础设施资产

| 资产 | 状态 | 用途 |
|------|------|------|
| `.github/workflows/ci.yml` | ✅ 可用 | Python CI |
| `.github/workflows/reusable-python-ci.yml` | ✅ 可用 | 复用 Python CI |
| `.github/workflows/reusable-node-ci.yml` | ✅ 可用 | 复用 Node CI |
| `docker-compose.yml` | ✅ 可用 | 开发环境 |
| `docker-compose.prod.yml` | 🟡 需更新 | 生产环境 (需更新命名) |
| `Caddyfile` | 🟡 需更新 | 反向代理 (需更新域名) |
| `build-all.bat` | 🟡 需更新 | 构建脚本 (需更新命名) |
| `scripts/health_check.py` | ✅ 可用 | 健康检查 |
| `scripts/github_sync.py` | ✅ 可用 | GitHub 同步 |
| `scripts/acceptance_check.py` | 🟡 需更新 | 验收检查 (需适配新结构) |
| `sql/init/01-databases.sql` | ✅ 可用 | 数据库初始化 |

### 4.2 缺失的基础设施

| 缺失 | 说明 | 优先级 |
|------|------|--------|
| **统一构建脚本** | 目前 build-all.bat 需更新命名 | 🔴 P0 |
| **Docker health checks** | 容器健康检查未配置 | 🟡 P1 |
| **环境变量模板** | `.env.example` 存在但需更新 | 🟡 P1 |
| **日志聚合** | 多服务日志未统一 | 🟢 P2 |
| **监控告警** | Prometheus 中间件存在但未配置告警 | 🟢 P2 |

---

## 五、重组后的项目结构

### 5.1 目录命名方案

```
Ghost/
├── aid/              ← 原 AID/ (身份层, 核心)
├── nebula/           ← 原 mindflow-map/ (工作流引擎)
├── pulse/            ← 原 DS/ (电商 Agent)
├── core/             ← 原 zcode-brain/ (调度引擎组件)
├── stage/            ← 原 ai综艺/ (内容前端)
├── flow/             ← 原 mindflow/ (Web 前端门户)
├── docs/             ← 文档
├── scripts/          ← 运维脚本
├── skills/           ← 技能包
├── sql/              ← 数据库脚本
└── (配置文件)         ← docker-compose, Caddyfile, .github
```

### 5.2 aid/ (原 AID/) 内部重组

```
aid/
├── src/
│   ├── aid/                    ← 统一包名
│   │   ├── identity/           ← 身份层 (合并 core/ + alpha_id/)
│   │   │   ├── did.py          ← DID 生成 (只保留 signer.py 逻辑)
│   │   │   ├── signer.py       ← Ed25519 签名 (实际使用)
│   │   │   ├── document.py     ← DID Document 结构
│   │   │   ├── verification.py ← 身份证+人脸 实名认证
│   │   │   └── recovery.py     ← 密钥恢复
│   │   │
│   │   ├── memory/             ← 记忆系统
│   │   │   ├── private_chain.py    ← 私链 (加密本地)
│   │   │   ├── knowledge_chain.py  ← 知链 (Obsidian)
│   │   │   ├── profile.py          ← 六维度 Profile
│   │   │   └── episodic.py         ← 情景记忆
│   │   │
│   │   ├── brain/              ← 孪生大脑
│   │   │   ├── twin_brain.py   ← 状态机 (sleep/awake/idle)
│   │   │   ├── spirit.py       ← 5 大内部驱力
│   │   │   └── drives.py       ← 驱力定义
│   │   │
│   │   ├── token/              ← Token 经济 (新增)
│   │   │   ├── guard.py        ← 五层防护
│   │   │   ├── billing.py      ← 计费引擎
│   │   │   └── quota.py        ← 配额管理
│   │   │
│   │   ├── vault/              ← 凭证保险库 (新增)
│   │   │   ├── store.py        ← 加密存储
│   │   │   ├── grant.py        ← 临时授权
│   │   │   └── audit.py        ← 审计日志
│   │   │
│   │   ├── platform/           ← 平台服务 (新增)
│   │   │   ├── agent_registry.py ← Agent 注册
│   │   │   ├── trial_call.py   ← Trial Call 验证
│   │   │   ├── directory.py    ← Agent 目录
│   │   │   └── reputation.py   ← 声誉计算
│   │   │
│   │   ├── importer/           ← 导入器
│   │   │   ├── chatgpt.py      ← ChatGPT 导出导入
│   │   │   └── base.py         ← 导入器基类
│   │   │
│   │   ├── mcp/                ← MCP 注入
│   │   │   └── server.py       ← profile://, memory://
│   │   │
│   │   └── api/                ← REST API
│   │       ├── routes.py       ← 路由定义
│   │       └── middleware.py   ← 中间件
│   │
│   └── cli/                    ← CLI 入口
│       └── main.py             ← aid init/collect/profile
│
├── tests/                      ← 测试 (清理到 < 400)
├── docs/                       ← 项目文档
├── pyproject.toml              ← 包配置
└── README.md                   ← 项目说明
```

### 5.3 docs/ 重组后结构

```
docs/
├── GHOST_ECO_MASTER.md                    ← 总纲 (持续更新)
├── PROJECT_AUDIT_AND_REORGANIZATION.md ← 本文档
├── DEPLOYMENT.md                       ← 部署指南
├── CI_CD.md                            ← CI/CD 流程
├── DATABASE_MIGRATION.md               ← 数据库迁移
├── CROSS_SERVICE_INTEGRATION.md        ← 跨服务集成
├── ACCEPTANCE_REPORT.md                ← 验收记录
└── archive/                            ← 归档
    ├── ECOSYSTEM_ARCHITECTURE_v0.4.md  ← 历史架构文档
    ├── AID_FULL_INTEGRATION.md         ← AID 文件整合
    ├── PLATFORM_VISION.md              ← 愿景文档
    ├── DECISION_SKILLS.md              ← 决策技能
    ├── aid-mindflow-讨论纪要.md         ← 讨论记录
    └── mindflow-blocks-interview.md    ← 面试文档
```

---

## 六、不该做的事 (红线清单)

| # | 红线 | 原因 | 触发条件 |
|---|------|------|---------|
| 1 | ❌ 新增子项目 | 6 个已经太多, 先整合 | 任何"我想做个新东西"的想法 |
| 2 | ❌ 测试数量膨胀 | 855 → 928 → ? 没意义 | 写边界条件测试前, 先问"这能证明什么?" |
| 3 | ❌ README 叙事膨胀 | "智能代理编排"实际是关键词匹配 | 描述前, 先问"这是真的吗?" |
| 4 | ❌ 开发 autopilot 自改进 | 100KB 代码做 self-loop, 跑不通 | 任何"让代码自己改自己"的想法 |
| 5 | ❌ 新增第三方 provider | secrets 写了 env/K8s/Vault, 只用 env | 接入新 provider 前, 先问"现在需要吗?" |
| 6 | ❌ 注册收费 | 门槛必须为零 | 任何"注册收费"的建议 |
| 7 | ❌ 中文目录名 | Linux 部署编码问题 | 新建任何目录 |
| 8 | ❌ 新增文档文件 | docs/ 已经 17 个, 先整合 | 写新文档前, 先问"能追加到总纲吗?" |

---

## 七、该调整的事 (优化清单)

| # | 调整 | 原因 | 优先级 | 预估 |
|---|------|------|--------|------|
| 1 | 子项目重命名 (6 个) | 命名不专业, 影响品牌 | 🔴 P0 | 2 小时 |
| 2 | docs/ 清理 (17→8) | 减少认知负担 | 🔴 P0 | 1 小时 |
| 3 | 统一 AID 包名 | core/ + alpha_id/ 两个灵魂 | 🔴 P0 | 8 小时 |
| 4 | 清理 autopilot 模块 | 100KB 过度工程 | 🔴 P0 | 2 小时 |
| 5 | 清理低价值测试 | 928 → < 400 | 🟡 P1 | 4 小时 |
| 6 | DS middleware 安全漏洞 | 开发环境无认证 | 🔴 P0 | 0.5 小时 |
| 7 | 更新 build-all.bat | 适配新命名 | 🟡 P1 | 0.5 小时 |
| 8 | 更新 docker-compose | 适配新命名 | 🟡 P1 | 1 小时 |
| 9 | 修正 zcode-brain README | 诚实描述 | 🟢 P2 | 0.5 小时 |
| 10 | 删除 fairy_agent 空壳 | 29KB 无用代码 | 🟡 P1 | 0.5 小时 |

---

## 八、缺失的模块 (待建清单)

| # | 模块 | 说明 | 优先级 | 预估 |
|---|------|------|--------|------|
| 1 | **实名认证 API** | 支付宝/微信 二要素 + 人脸 | 🔴 P0 | 8 小时 |
| 2 | **Token 五层防护** | 日预算/单次/速率/睡眠/告警 | 🔴 P0 | 8 小时 |
| 3 | **私链加密存储** | AES-256-GCM + SQLite | 🔴 P0 | 4 小时 |
| 4 | **ChatGPT 导入器** | 导出文件 → Profile | 🔴 P0 | 4 小时 |
| 5 | **CLI 命令** | aid init/collect/profile show | 🔴 P0 | 4 小时 |
| 6 | **知链 Obsidian 同步** | Markdown + frontmatter | 🟡 P1 | 8 小时 |
| 7 | **凭证保险库** | 加密存储 + 临时授权 | 🟡 P1 | 8 小时 |
| 8 | **Agent 注册系统** | Datasheet + Trial Call | 🟡 P1 | 12 小时 |
| 9 | **MCP Server 真实数据** | 接入 Profile 而非 mock | 🟡 P1 | 4 小时 |
| 10 | **REST API** | 总纲 §七 定义的全部端点 | 🟡 P1 | 16 小时 |
| 11 | **SDK** | aid-kit-python + aid-kit-js | 🟢 P2 | 16 小时 |

---

## 九、执行顺序建议

### 第一周: 清理 + 命名

```
Day 1: 子项目重命名 (6 个) + 更新 .gitmodules + 更新 build-all.bat
Day 2: docs/ 清理 (17→8) + 归档旧文档
Day 3: DS middleware 安全漏洞修复 + zcode-brain README 修正
Day 4: 统一 AID 包名 (core/ + alpha_id/ → aid/)
Day 5: 清理 autopilot 模块 + 删除 fairy_agent 空壳
```

### 第二周: P0 功能

```
Day 6-7:   实现 aid init + aid profile show
Day 8-9:   实现实名认证 API (支付宝/微信)
Day 10:    实现私链加密存储
Day 11-12: 实现 Token 五层防护
Day 13-14: 实现 ChatGPT 导入器
```

### 第三周: P1 功能

```
Day 15-17: 知链 Obsidian 同步
Day 18-19: 凭证保险库
Day 20-21: Agent 注册系统 (基础)
```

---

## 十、总账: 我们有什么, 缺什么, 该扔什么

### 已有的 (可用级及以上)

```
✅ Ed25519 签名 (零依赖, 生产级)
✅ DID 生成 (生产级)
✅ PoE 执行证明 (可用级)
✅ JWT 实现 (零依赖, 生产级)
✅ DI 容器 (可用级)
✅ Profile Schema (可用级)
✅ 工作流引擎 (可用级, 需清理 autopilot)
✅ 风险引擎 (可用级)
✅ Zod 验证 (生产级)
✅ Session 认证 (生产级)
✅ Docker 编排 (可用级)
```

### 缺的 (P0)

```
🆕 实名认证 (身份证+人脸)
🆕 私链加密存储
🆕 Token 五层防护
🆕 ChatGPT 导入器
🆕 aid CLI 命令
🆕 Agent 注册/目录
🆕 凭证保险库
🆕 MCP Server 真实数据
🆕 平台 REST API
🆕 SDK (Python/JS)
```

### 该扔的

```
🗑️ autopilot 模块 (100KB 过度工程)
🗑️ fairy_agent.py (29KB 空壳)
🗑️ 低价值测试 (928 → < 400)
🗑️ secrets 多 provider (只留 env)
🗑️ 冗余文档 (17 → 8)
🗑️ 抖音自动化 (跑不通, 标记 experimental)
```

---

> **下一步**: 确认本审计方案 → 按"第一周"计划执行清理和重命名 → 然后进入 P0 功能开发。
