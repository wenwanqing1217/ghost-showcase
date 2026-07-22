# MindFlow Map 审计报告

> 审计时间：2026-07-21
> 审计方法：逐文件代码审查 + 实际运行验证（pytest / ruff / 导入冒烟）
> 说明：本报告刷新并取代 2026-07-19 的旧版报告（旧报告基于 10/10 测试的早期状态，已严重过时）。
> 本次审计时工作区存在大量未提交修改，以下结论以工作区当前代码为准，并区分「存量问题」与「未提交改动引入的问题」。

---

## 一、验证基线（实测数字）

| 项目 | 修复前 | 修复后 |
|------|--------|--------|
| `pytest tests/` | **220 passed, 1 failed**（27s） | **221 passed**（26s） |
| ruff `src/`（全规则） | 973 errors | 951 errors |
| ruff `src/`（F821/F811/F601 未定义名/重复定义/重复键） | 13 errors | **0 errors** |
| `from mindflow_map.main import app` 冒烟 | OK | OK（48 条路由） |

环境：Python 3.14.3（系统解释器，包以非 editable 方式装过元数据但 `import mindflow_map` 不可直接导入；测试依赖 pyproject 中 `pythonpath=["src"]` 正常运行）。`pip install -e ".[dev]"` 的可导入性未重新验证。

### README 声明核对

| README 声明 | 实测 | 结论 |
|------|------|------|
| badge `218/218 passing` | 实际收集 221 个用例，修复前 220+1 失败 | **不实**，已更正为 221/221 |
| 端口 2002 | Dockerfile `EXPOSE 2002`、CORS 白名单含 2002 | 属实 |
| `uvicorn mindflow_map.main:app` 启动 | 应用可导入，lifespan 逻辑完整 | 基本属实（未实际起服务验证 HTTP） |
| 「飞书/微信/抖音/Shopify 全链路」 | 抖音/Shopify 仅框架就位（README 自己的「模块状态」节也承认） | 营销口径偏大，代码层属实 |

---

## 二、决策失误清单（按严重度排序）

### 1. 未提交改动里混入整段复制粘贴重复代码，且直接弄挂了测试
- 证据：`src/mindflow_map/workflows/engine.py` 工作区改动中 `ChatTool` 类被**完整粘贴了两遍**（原 207-234 与 238-265 行），`tools` 字典里 `"chat": ChatTool()` 也写了两次，`typing` 导入重复两行。
- 后果：新增 `chat` 内建工具后没同步更新 `tests/unit/test_plugins.py::test_builtin_tools_loaded_by_default`，全量测试红灯（220+1 failed）。
- 性质：这不是架构问题，是改动没有经过任何本地验证（项目配了 pre-commit + pytest 钩子，显然没跑）。
- **已修复**：删除重复类/重复键/重复导入，测试断言更新为含 `chat`，221/221 通过。

### 2. PostgreSQL/Alembic 路径上存在必现 NameError，说明生产数据库路径从未被运行过
- 证据：`src/mindflow_map/models/session.py` 的 `_ensure_initialized()` 与 `init()` 在 `_use_alembic` 分支调用 `asyncio.get_event_loop()`（原 88、99 行），但整个文件**从未 `import asyncio`**。SQLite 路径走 `create_all` 所以测试全绿，一旦切到 PostgreSQL（README/Helm 均以此作为生产形态）第一次初始化就 `NameError` 崩溃。
- **已修复**：补充 `import asyncio`。
- 附带问题：迁移通过 `subprocess.run([sys.executable, "-m", "alembic", ...])` 起子进程执行（同文件 `_run_alembic_migrations`），而不是用 Alembic Python API；且 `alembic/env.py` 只把 `models.database.Base` 注册为 `target_metadata`，`memory.store.Base` 导入了却没用——记忆库的表根本不在迁移覆盖范围内。这是一处「看起来有迁移体系，实际没闭环」的决策失误。

### 3. 认证中间件允许「自报家门」式头认证，RBAC 形同虚设
- 证据：`src/mindflow_map/middleware/auth.py:54-56`——只要请求带上 `X-Tenant-ID` + `X-User-ID` 两个明文头、无需任何令牌/签名，就以该用户在库中的角色放行。没有配套文档说明这些头必须由可信网关注入。
- 影响：直接暴露服务时，任何人构造两个头即可冒用任意租户/用户身份，README 宣称的「多租户 RBAC、租户隔离」不成立。
- 处置：架构级问题，本次不擅自改（见「待确认提案」P2）。

### 4. 密钥管理体系「有文档有代码」，但落地链断裂
- 已落实的部分（属实）：`.env` 未被 git 跟踪且在 `.gitignore` 中；`src/mindflow_map/secrets/` 实现了 env/kubernetes/vault 三种 Provider 及工厂；`docs/SECRETS_MANAGEMENT.md` 与实现一致。
- 断裂处：
  - `.pre-commit-config.yaml` 的 detect-secrets 钩子要求 `--baseline .secrets.baseline`，但**该文件不存在**，钩子一旦启用必失败——说明 pre-commit 从未真正装过。
  - pre-commit 里同时配置了 `ruff` 与 `mypy --strict`，而 `src/` 当前有 951 个 ruff 错误（其中 55 个 F401 未用导入），mypy 严格模式更不可能过。钩子配置与代码现状完全脱节。
  - 根目录存在两个被 git 跟踪的垃圾脚本 `create_secrets.py`（内容仅 `x=1`）和 `temp_create.py`（语法残缺的 `print(...))`，工作区已删后者），名字像密钥相关、实为垃圾，容易误导。
- 处置：垃圾文件列入待确认删除清单。

### 5. 依赖声明双轨漂移
- 证据：`requirements.txt`（12 个包）缺 `alembic`、`asyncpg`、`redis`，而 `pyproject.toml` 的 `dependencies`（16 个包）包含它们。按 README 用 pip 安装与按 requirements 安装得到两套不同环境，Alembic 迁移在 requirements 安装下直接缺包。
- 处置：建议二选一（保留 pyproject 为唯一来源），见提案 P3。

### 其他值得记录的设计问题（未改）

- **CircuitBreaker 全局串行化**：`src/mindflow_map/ai/circuit_breaker.py:63` 用一把 `asyncio.Lock` 包住整个 `await fn()`，共享一个熔断器时所有 LLM 调用被强制串行，高并发下成为瓶颈；且所有异常一律吞掉返回 `None`，调用方无法区分「熔断拒绝」与「业务失败」。
- **飞书长连接依赖私有 API monkeypatch**：`src/mindflow_map/api/feishu.py:150-184` 劫持 `lark_oapi` 的 `_handle_control_frame` 补 PONG 回复，属上游 SDK 私有方法，lark-oapi 升级即可能静默失效。注释已说明原因（v1.7.1 缺陷），建议跟进上游 issue 并固定依赖版本。
- **测试告警 37 条**：`datetime.utcnow()` 弃用警告（`tests/unit/test_audit.py`、`test_auth.py`、`test_events.py`），来自 `schemas`/模型层，Python 3.14 下应迁移到 `datetime.now(UTC)`。
- **抖音自动化真实可用性低**：`src/mindflow_map/automation/douyin.py` 选择器是「逐个碰运气」式（`input`、`textarea` 兜底），页面结构一变就废；发布成功与否以「没看到成功提示也返回 success」收尾（244-251 行），会谎报成功。

---

## 三、本次已应用的安全修复（全部为非破坏性小改动）

| 文件 | 改动 | 原因 |
|------|------|------|
| `src/mindflow_map/workflows/engine.py` | 删除重复的 `ChatTool` 类、重复的 `"chat"` 字典键、重复的 `typing` 导入行 | 修复 ruff F811/F601/I001，消除复制粘贴事故 |
| `src/mindflow_map/models/session.py` | 补 `import asyncio` | 修复 PostgreSQL 路径必现 NameError（F821） |
| `src/mindflow_map/middleware/rate_limit.py` | `typing` 导入补 `Any` | 修复 F821 |
| `src/mindflow_map/api/workflow.py` | 补模块级 `workflow_engine: WorkflowEngine \| None = None` 声明 | 修复 F821；lifespan 注入前调用从 NameError 变为可诊断的 AttributeError |
| `src/mindflow_map/api/wechat.py` | 补模块级 `workflow_engine = None` 声明 | 同上 |
| `tests/unit/test_plugins.py` | 内建工具断言加入 `"chat"` | 与 engine 新内建工具对齐，修复唯一失败用例 |
| `README.md` | badge 与两处「218 passed」更正为 221 | 与实测一致 |

未改动任何 git 状态、未删除任何文件、未触碰 `.env`。

---

## 四、待确认的高风险提案（未执行）

### P0 - 删除垃圾文件（影响面：无运行时影响；工作量：10 分钟）
- `create_secrets.py`（已跟踪，内容 `x=1`）
- `temp_create.py`（工作区已删，尚需 `git rm` 落锤）
- `scripts/fix_exceptions.py`、`scripts/fix_feishu_imports.py`、`scripts/fix_run_ws.py`：一次性字符串替换补丁脚本，硬编码 `D:/MW/...`、`D:\mindflow-workspace\...` 绝对路径，其中 `fix_exceptions.py` 甚至操作的是 **AID 项目**的源码，留在本仓库只有害处
- `-p/`（空目录，`mkdir -p` 在 Windows 下的误产物）

### P1 - 全仓 lint 清偿（影响面：约 60+ 文件；工作量：1-2 小时含回归）
- `ruff check src --fix` 可自动修 464 个（F401 未用导入、I001 导入排序、UP 系列现代化写法）；剩余 RUF001/002/003（中文标点触发的 ambiguous-unicode，多为误报）建议在 `pyproject.toml` 中 ignore。
- 前提：先跑一次全量测试做基线，修完再跑一轮对比（当前基线 221/221）。

### P2 - 头认证加共享密钥或默认关闭（影响面：`middleware/auth.py` 及所有调用方；工作量：半天）
- 方案 A：头认证仅在 `settings.debug` 或显式 `TRUST_PROXY_HEADERS=true` 时启用，生产默认只认 Bearer Token。
- 方案 B：头认证增加网关共享密钥（如 `X-Auth-Gateway-Key`）校验。
- 需要同步更新 `docs/` 中的部署说明。

### P3 - 依赖声明收口（影响面：部署文档；工作量：30 分钟）
- 删除 `requirements.txt` 或改为 `pip install -e ".[dev]"` 的一行说明；`Dockerfile`/文档统一到 pyproject。

### P4 - Alembic 迁移闭环（影响面：`models/session.py`、`alembic/env.py`；工作量：半天）
- 改用 Alembic Python API 替代子进程调用；把 `memory.store.Base` 的 metadata 纳入 `target_metadata`（或明确文档化「记忆库不走迁移」）；补一个 PostgreSQL 路径的初始化测试（当前测试只覆盖 SQLite 分支）。

### P5 - 飞书 monkeypatch 解除（影响面：`api/feishu.py`；工作量：取决于上游）
- 升级 lark-oapi 并验证上游是否已修复 PING/PONG；未修复则向 lark-oapi 提 issue/PR，代码中用 `packaging.version` 对 SDK 版本做断言，避免静默失效。

---

## 五、无法验证/未完成项

- 未实际启动 uvicorn 服务做 HTTP 级验证（测试已覆盖 lifespan 关键路径，但 `/health` 等端点未实测）。
- mypy 未运行（系统 Python 未安装 mypy，且规则禁止全局安装；以 ruff F 类检查替代）。
- 密钥是否真实泄露未做全文扫描验证：`.env` 文件存在但未被 git 跟踪（已用 `git ls-files` 核实），其内容按规则未读取；`scripts/scan_secrets.py` 未执行。
- 飞书/微信/抖音/百度地图的真实第三方连通性未验证（需要真实凭证）。
- workflow-editor（前端子目录）不在本次范围，仅确认 `dist/` 存在与否决定 `/editor` 挂载。
