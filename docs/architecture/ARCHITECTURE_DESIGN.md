# Ghost / Alpha-ID 架构设计方案（锚定审计版本）

> ⚠️ **已过时** — 本文档已合并到新文档 `ARCHITECTURE.md`，请以新文档为准。
> 本方案中每一个设计决策均关联到 REGISTRY_ALL.md 中的具体问题 ID + 文件路径 + 行号

---

## Phase 1：止血（1 周）— 7 个具体动作

### 动作 1：修 PyPI 入口（S-03、S-04）

**审计证据：**
- `pyproject.toml` 第 133-136 行：`aid-api = "entrypoints.api:main"`——指向已删除的 `src/entrypoints/api.py`
- `pyproject.toml` 第 134 行：`aid-daemon = "entrypoints.daemon:main"`——指向已删除的 `src/entrypoints/daemon.py`
- 确认：`src/entrypoints/api.py` 不存在（第 3 轮审计确认）
- 确认：`src/entrypoints/daemon.py` 不存在（第 3 轮审计确认）

**修法：**
- 删 `aid-daemon` 入口
- 删 `aid-mcp` 入口（`entrypoints.aid_mcp_server.py:main` 从头到尾没启动过）
- `aid-api` 改为指向 `main:app`（`src/main.py` 第 48-53 行的 FastAPI 实例）
- 改后跑 `pip install -e .` 验证

**验证方式：** `aid-api --help` 不报错

---

### 动作 2：修百度地图 Token 硬编码（S-01）

**审计证据：**
- `src/mindflow/agents/travel.py` 第 15 行：
  ```python
  BAIDU_MAP_AUTH_TOKEN = sk-ap-5h1Eit4VKkhGRV3VmKZb4Z2dmgnex6UrRrFOMFx6HRNSXIbwfahDeq8V7HzVL0cS
  ```
  这不是从环境变量读取的，是直接写在源码中的。

**修法：**
- 第 15 行改为 `BAIDU_MAP_AUTH_TOKEN = os.getenv("BAIDU_MAP_AUTH_TOKEN", "")`
- 值移到 `.env` 中

---

### 动作 3：修 PostgreSQL 默认密码（S-02）

**审计证据：**
- `docker-compose.postgres.yml` 第 12 行：
  ```yaml
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-changeme_in_production}
  ```
  如果部署时不设置环境变量，数据库密码就是 `changeme_in_production`。

**修法：**
- 改为 `POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?error:必须设置 POSTGRES_PASSWORD}`
- 没有设置密码时启动直接报错，不会用默认值

---

### 动作 4：注册后加"啊哈时刻"（D-01）

**审计证据：**
- `ghost.html` 第 3984 行（`finishRegistration` 函数）：注册完成后只调用了 `showWorkbench()`，没有引导流程
- 工作台 9 个面板（`ghost.html` 第 2863-3149 行）：仅豆包记忆桥（第 4118-4156 行）和记忆星云（第 4208-4252 行）有真实 fetch 调用，其余面板全是空壳或硬编码假数据

**修法：**
- `finishRegistration`（`ghost.html` 第 3984 行）注册完成后改为三步引导：
  1. "欢迎！想导入 ChatGPT 数据吗？" → 调 `POST /api/v1/register/complete`
  2. "正在生成你的第一个记忆图谱…" → 调现有的 `/v1/memory/graph`（Gateway 第 543-576 行）
  3. "看！这是你的数字痕迹" → 显示图谱

---

### 动作 5：前端拆 3 文件（A-02）

**审计证据：**
- `ghost.html` 总行数：4,313 行（第 5 轮审计确认）
- 内联 `<style>` 标签：4 处（第 12 行 Tailwind + 第 14 行自定义 + 第 21 行滚动条 + 更多内联）
- 内联 `<script>` 标签：第 3364-4270 行（~906 行 JS）
- 全局变量：第 3803-3808 行（`var isLoggedIn`、`var GATEWAY_URL` 等 6 个）

**修法：**
1. `ghost.html` → 保留 HTML 结构
2. `ghost.css` → 提取所有 `<style>` 内容
3. `ghost.js` → 提取所有 `<script>` 内容

**不改变逻辑，仅做机械拆分。**

---

### 动作 6：CI 注册测试通过（T-01、T-02）

**审计证据：**
- `tests/test_registration.py`：8 个测试，全部通过（第 5 轮审计实测确认）
- `tests/conftest.py` 第 157 行：`from entrypoints.daemon import AIDFairy`——已修（try/except）
- 但 CI 配置（`.github/workflows/ci.yml`）在 GitHub 上从未跑过（第 5 轮审计确认）

**修法：**
- CI 先只跑 `pytest tests/test_registration.py -v --noconftest`
- 通过后再加更多测试文件

---

### 动作 7：`registration.py` 改用 Container DI（C-01）

**审计证据：**
- `src/api/registration.py` 第 57、70、88、98 行：4 处 `sqlite3.connect(_db_path)`
- 同一目录下 `identity.py` 第 16 行用的是 `Container.instance().identity`——不一致
- `registration.py` 直连 SQLite 导致测试无法注入 mock 数据库

**修法：**
- 删掉 `_db_path`（第 57 行）
- `_sms_store()` 和 `_face_store()` 改为通过 Container 获取存储后端
- 具体：第 57 行改为 `store = Container.instance().storage`

---

## Phase 1 验收标准

| 标准 | 验证方式 | 关联审计ID |
|:-----|:---------|:-----------|
| `pip install alpha-id-zix` 后 `aid-api` 可运行 | 手动运行 | S-03、S-04 |
| 百度地图 Token 不在源码中 | `grep -r "sk-ap-" src/` | S-01 |
| 注册后用户能导入 ChatGPT 数据 | 手动注册测试 | D-01、F-06 |
| `ghost.html` 拆为 3 文件 | 确认 3 文件存在 | A-02 |
| CI 注册测试绿色勾 | GitHub Actions | T-01、T-02 |
| `registration.py` 0 处 `sqlite3.connect` | 代码扫描 | C-01 |

---

## Phase 2：接通（2 周）— 6 个具体动作

### 动作 8：AgentLoop 接 API 路由（A-01）

**审计证据：**
- `src/core/agent.py` 第 652-813 行：`AgentLoop` 类完整，包含 `run()` 方法
- `src/core/agent_react.py` 第 25 行：`ReActEngine` 思考引擎完整
- 但在 `src/api/` 目录下没有任何路由调用这两个类（`grep -r "AgentLoop\|ReActEngine" src/api/` 返回空）

**修法：**
- 在 `src/api/identity.py` 或新建 `src/api/agent.py` 中添加：
  ```python
  @router.post("/chat")
  def chat(body: ChatRequest, alpha_id: str = Depends(require_user)):
      loop = AgentLoop(alpha_id)
      return loop.run(body.message)
  ```

### 动作 9：TwinBrain 注入 AgentLoop（A-01）

**审计证据：**
- `src/core/twin_brain.py` 第 109-127 行：`__init__` 接收 `alpha_id` 和 `storage`
- `src/core/agent.py` 第 654-658 行：`AgentLoop.__init__` 仅接收 `config`，没有接收 `TwinBrain`

**修法：**
- `AgentLoop.__init__` 加 `brain: Optional[TwinBrain] = None` 参数
- 存在时在 `run()` 中调 `brain.think()` 更新状态

### 动作 10：移除 Flow/API（A-06）

**审计证据：**
- `flow/` 目录已在子模块 deinit 后清空（第 5 轮审计确认）
- 前置条件：动作 8 完成，AI 路由已在 Python 中可用

**修法：** 删 `flow/` 目录

### 动作 11-13：面板接数据 + 飞书心跳 + 空壳标记

**审计证据：**
- `ghost.html` 第 2912 行：`"confidence: 0.94"` 硬编码
- `ghost.html` 第 2928 行：`"0.92"` 硬编码
- `ghost.html` 第 2935 行：`"0.78"` 硬编码
- `ghost.html` 第 2942 行：`"0.65"` 硬编码
- `nebula/feishu.py`：搜索 `ping\|heartbeat\|keepalive` 确认无边心跳（第 5 轮审计确认）

**修法：**
- 面板数据改为调 `mindflow/intent.py` 的 `IntentClassifier.classify(text)`（第 103 行）
- 飞书加 30 秒定时 ping
- 空壳面板加 `"🚧 开发中"` 标记

---

## 设计验证方法

| 设计决策 | 具体验证 | 审计证据参考 |
|:---------|:---------|:-------------|
| Gateway 拆双层 | 公共网关不能访问 `_chain_key_private` 路径 | `REGISTRY_ALL.md:A-03` |
| AI 路由迁 Python | `POST /api/v1/agent/chat` 返回与 Flow 一致的结构 | `REGISTRY_ALL.md:A-06` |
| 存储统一 | 全部数据操作通过 `StorageBackend` 接口 | `REGISTRY_ALL.md:C-01` |
| 前端拆文件 | 首屏加载时间不增加 | `REGISTRY_ALL.md:A-02` |
