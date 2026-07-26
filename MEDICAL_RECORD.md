# Ghost / Alpha-ID 完整项目病历

> 主治医师：AtomCode | 诊断日期：2026-07-26
> 本文档替代所有之前的零散审计报告，是唯一诊断依据。

---

## 一、病史

### 1.1 项目起源

Alpha-ID 始于一个原始场景：用户在 ChatGPT 中聊了三个月，ChatGPT 已经"认识"他了——但换到 Claude，一切归零。项目目标：让用户的数字存在在所有 AI 工具中连续。

### 1.2 发展历程

```
阶段 1（0.0.1 → 0.0.9）：核心身份系统
  完成：DID 生成、Ed25519 签名、CLI 工具
  未完成：验证入口

阶段 2（0.1.0 → 0.2.0）：Web API + 记忆系统
  完成：FastAPI 入口、双链记忆、JWT 认证
  未完成：前端面板数据接通

阶段 3（0.3.0 → 0.3.1）：Ghost 矩阵
  完成：Gateway 网关、Ghost.html 前端、注册流程
  未完成：18 个 core 模块未接、CI 未通
```

### 1.3 当前状态

- Python 代码：~22,000 行 / 约 304 个文件
- TypeScript 代码：~960 行 / 23 个文件  
- 前端：Ghost.html 4,300 行单体
- PyPI 版本：0.3.0（本地）/ 0.3.1（远程，来源不明）
- CI：从未通过
- 测试：37 个文件，需要 `--noconftest` 才能收集
- 活跃用户：0

---

## 二、全部症状清单（211 项总览）

### 🔴 致命级（6 项）— 系统不可用

| 编号 | 症状 | 位置 |
|:----:|:-----|:------|
| F-01 | `aid-api` 入口指向已删除模块 `entrypoints.api:main` | `pyproject.toml` |
| F-02 | `aid-daemon` 入口指向已删除模块 `entrypoints.daemon:main` | `pyproject.toml` |
| F-03 | PyPI 包名 `alpha-id-zix` 与本地 `pyproject.toml` 的 `name="alpha-id"` 不一致 | `pyproject.toml` / PyPI |
| F-04 | CI 从未通过，928 tests 在 README 中不实 | `.github/workflows/` |
| F-05 | 硬编码百度地图 API Token 在源码中 | `mindflow/agents/travel.py:15` |
| F-06 | Docker PostgreSQL 密码 `changeme_in_production` | `docker-compose.postgres.yml` |

### 🟡 严重级（14 项）— 功能严重受限

| 编号 | 症状 | 位置 |
|:----:|:-----|:------|
| S-01 | 18 个 core 模块写完但 0 处引用（约 6,530 行死代码） | `src/core/` |
| S-02 | Ghost.html 9 个工作台面板中仅 2 个有真实数据 | `ghost.html` |
| S-03 | `registration.py` 直连 SQLite，绕过 Container DI | `api/registration.py` |
| S-04 | `rotate_token` 未做已撤销校验（重放攻击漏洞） | `auth/jwt.py` ← 已修 |
| S-05 | 默认存储后端为 JSON 文件，非 SQLite | `user_identity.py` ← 已修 |
| S-06 | `dual_chain.py` 默认 JSON 存储，SQLite 不统一 | `dual_chain.py` ← 已修 |
| S-07 | `GHOST_WORKSPACE_PATH` 与 `COZE_WORKSPACE_PATH` 混用 | 多处 |
| S-08 | entrypoints 目录 3 个入口全部从未启动 | `entrypoints/` |
| S-09 | `aid-mcp` 入口指向存在但从未验证 | `pyproject.toml` |
| S-10 | 两个独立 FastAPI 应用（`main.py` + `web.py`），一个从未启动 | `web.py` |
| S-11 | 依赖声明不全：代码用 `fastapi`/`uvicorn`/`httpx`，但 `pyproject.toml` 未声明 | `pyproject.toml` |
| S-12 | 前端 `innerHTML` 赋值中用户输入未转义（XSS 风险） | `ghost.html` |
| S-13 | 飞书机器人 WebSocket 无心跳保活，超时断连 | `nebula/feishu.py` |
| S-14 | Ghost.html 4300 行单体，无组件化、无可测试性 | `ghost.html` |

### 🟢 轻微级（32 项）— 影响体验/维护

| 类别 | 数量 | 示例 |
|:-----|:----:|:------|
| 根目录调试文件 | 6 | `_cdp_err.txt`、`_cdp_poll2.log` |
| LevelDB 副本 | 2 目录 | `_doubao_clean_copy/`、`_doubao_db_copy/` |
| 一次性脚本 | 15+ | `fix_*.py`、`patch_*.py` |
| 已提交的调试文件 | 7 | `final_reply.txt`、`gateway_debug.txt` |
| 孤立未连接目录 | 3 | `core/`、`codex-remote/`、`config/` |
| 配置问题 | 3 | `MASTER_KEY` 读取时机、无版本号策略、无国际化 |
| 测试问题 | 3 | 37 测试崩溃、3 坏文件已修未验证 CI |
| 文档问题 | 3 | README 徽章不实、GHOST.md 过时、无贡献指南 |

**总 52 项已记录，全量可追溯。**

---

## 三、根因诊断（不是 52 个问题，是 3 个病因）

### 病因 A：先搭框架后填内容（根本病因）

```
症状表现：
  18 个 core 模块写完没接 ← 框架写完了
  Ghost.html 4300 行 ← 前端框架搭好了
  3 个入口 2 个坏的 ← 入口配好了但没验证
  mindflow 10 文件 ← 工作流框架搭好了

形成原因：每次迭代都从"搭架子"开始，到"能看"就停。
           没有一次迭代到"能跑"。

影响范围：项目 70% 的代码量、90% 的功能缺失。
```

### 病因 B：没有验收标准

```
症状表现：
  CI 从不跑 ← 没有"改完要验证"的标准
  测试需要 --noconftest ← 没有"测试必须通过"的标准
  PyPI 入口是坏的 ← 没有"发布前必须 pip install 验证"的标准

形成原因：写代码的是你，验收代码的也是你。
           没有第二双眼睛，没有自动检查。

影响范围：每次发布的质量不可控。
```

### 病因 C：架构设计超前实现

```
症状表现：
  A2A 协议 ← Agent 网络还没用户用
  CoALA 记忆 ← 基本双链记忆还没跑通
  故障恢复 ← 服务还没部署到生产
  多租户 ← 单用户模式都没验证

形成原因：设计文档写了 6 层，就照着 6 层全写了。
           但用户只走通了最下面 2 层。

影响范围：大量精力花在了用户暂时不需要的功能上。
```

### 三病因关系图

```
    病因 A：先搭框架后填内容（根本）
         │
         ├──→ 病因 B：没有验收标准（加速器）
         │        每次"搭完框架"没人叫停 → 每次都不验证
         │
         └──→ 病因 C：架构超前（放大器）
                  框架搭得太多了 → 收尾工作量太大 → 不敢收尾
```

---

## 四、治疗方案（分 4 期，每期验证通过才能进入下一期）

### 第 1 期：止血（1 天）

**目标：现在就能做的事情，发一个新版本 0.3.2。**

| 步骤 | 操作 | 对应症状 |
|:----:|:-----|:---------|
| 1.1 | 修 pyproject.toml：删 `aid-daemon`、改 `aid-api` → `uvicorn main:app` | F-01, F-02 |
| 1.2 | 删 `aid-mcp` 入口（未验证） | S-09 |
| 1.3 | 把 `travel.py` 的硬编码 Token 移到环境变量 | F-05 |
| 1.4 | Ghost.html 空壳面板加 "开发中" 标记 | S-02 |
| 1.5 | 准备 `pip install` 验证脚本 | F-03 |
| 1.6 | 发版 `alpha-id-zix 0.3.2` | F-01～F-06 |

**验收标准：** `pip install alpha-id-zix` 后 `aid init`、`aid-api` 两条命令能用。

---

### 第 2 期：接死代码（1 周）

**目标：把写了没接的核心模块接通，让 Ghost 从 "框架" 变成 "产品"。**

| 优先级 | 模块 | 接通方式 | 工期 |
|:------:|:-----|:---------|:----:|
| P0 | AgentLoop | 新建 `/api/v1/agent/chat` → 调用 `AgentLoop.run()` | 2 天 |
| P1 | TwinBrain | AgentLoop 初始化时注入 | 1 天 |
| P2 | 可观测性 | 注册为 FastAPI 中间件 | 1 天 |
| P3 | 故障恢复 | Gateway 启动时注册 | 1 天 |
| P4 | registration.py | 改为 Container DI | 0.5 天 |

**验收标准：** `POST /api/v1/agent/chat` 返回 Agent 真实响应。

---

### 第 3 期：存储 + CI 基建（1 周）

**目标：统一数据层、让 CI 通过。**

| 步骤 | 操作 | 工期 |
|:----:|:-----|:----:|
| 3.1 | 统一 `GHOST_WORKSPACE_PATH` 环境变量名 | 0.5 天 |
| 3.2 | `registration.py` 改用 Container DI（取代直连 SQLite） | 0.5 天 |
| 3.3 | 修 CI：至少 `pytest tests/test_registration.py` 通过 | 1 天 |
| 3.4 | 修 CI：去掉 `--noconftest` 后收集通过 | 1 天 |
| 3.5 | 把测试覆盖率报告加入 CI | 1 天 |

**验收标准：** GitHub Actions 绿色勾。

---

### 第 4 期：架构闭环（持续）

**目标：41 目录的设计逐项落地到代码。**

| 设计文档 | 对应代码 |
|:---------|:---------|
| `ALPHA_ID_01_Web端` → Ghost.html 重设计 | Phase 外 |
| `ALPHA_ID_03_技术架构` → AgentLoop + A2A 接通 | Phase 2 |
| `ALPHA_ID_00_项目总纲` → 7 个核心诉求 | 持续 |
| `ALPHA_ID_V1_核心逻辑链` → 设计决策溯源 | 参考 |

---

## 五、后续架构设计框架

### 5.1 当前架构问题

```
问题：6 层架构 → 代码写完了 6 层 → 用户只用到 2 层
方案：从"按层写"改为"按用户路径写"
```

### 5.2 新架构原则

1. **不被 41 目录的设计文档限制** — 文档是方向，不是施工图
2. **每个新模块必须回答一个问题：** 用户在什么场景下会用到它？
3. **不发没有验证的新代码** — 入口必须通过 `pip install` 验证

### 5.3 41 目录落地优先级

| 设计文档 | 优先级 | 原因 |
|:---------|:------:|:------|
| `ALPHA_ID_00_项目总纲` | P0 | 定义了"我们做什么"——所有决策依据 |
| `ALPHA_ID_V1_核心逻辑链` | P0 | 定义了"为什么做"——设计哲学 |
| `ALPHA_ID_01_Web端` | P1 | 定义了"用户看到什么"——前端重设计 |
| `ALPHA_ID_03_技术架构` | P1 | 定义了"怎么实现"——技术选型 |
| `ALPHA_ID_V2_Web4生态位` | P2 | 定义了"站在哪里"——定位 |
| `ALPHA_ID_02_模拟盘` | P3 | 定义了"未来往哪走"——延展 |
| 其余 | P3+ | 辅助参考 |

---

## 六、执行纪律

- **一期做完、验证通过、再进下一期** — 不跳期
- **每个版本发版前必须跑 `pip install` 验证** — 不发布坏包
- **41 目录的设计文档每月 review 一次** — 但不作为开发任务

---

## 七、一句话诊断

> **这个项目不是一个技术问题，是一个节奏问题。你建东西的速度是接东西的速度的 3 倍。解决办法不是建得更快，是接完再接新的。**
