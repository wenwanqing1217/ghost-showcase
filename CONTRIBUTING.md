#  Contributing to Ghost

感谢你对 Ghost 的兴趣！本文档帮助你快速上手贡献。

---

## 开发环境搭建

### 前置要求

- Python 3.12+
- Node.js 20+
- Docker + Docker Compose
- Git (with submodule support)

### 快速开始

```bash
# 1. 克隆（含子模块）
git clone --recurse-submodules https://github.com/wenwanqing1217/monorepo.git
cd monorepo

# 2. 安装 pre-commit hooks
pip install pre-commit
pre-commit install

# 3. 启动基础设施（PostgreSQL）
docker compose up -d db

# 4. 启动你要开发的模块（选择其一）

# ── 身份层 (Alpha-ID) ──
cd alphaid/projects
pip install -e ".[dev]"
uvicorn src.main:app --reload --port 8000

# ── 执行层 (Nebula) ──
cd nebula
pip install -e ".[dev]"
uvicorn mindflow_map.main:app --reload --port 2002

# ── 电商后端 (DS) ──
cd DS
npm install
npm run dev  # → :3004

# ── 编排层 (core) ──
cd core
npm install
npm run dev  # → :3001
```

---

## 项目结构

```
monorepo/
├── Ghost.html              # 唯一官网（单文件）
├── alphaid/projects/       # 身份层 (Python FastAPI)
├── nebula/                 # 执行层 (Python FastAPI)
├── DS/                     # 电商后端 (Next.js)
├── core/                   # 编排层 (TypeScript)
├── flow/                   # 前端门户 (Next.js, 已整合到 Ghost.html)
├── Gateway/                # API 网关 (Python FastAPI)
├── docker-compose.yml      # 开发环境编排
├── docker-compose.prod.yml # 生产环境编排
├── sql/init/               # 数据库初始化脚本
├── .github/workflows/      # CI/CD
├── ARCHITECTURE.md         # 架构设计文档
├── PROJECT_BRAIN.md        # 项目大脑
└── AGENT_PLAYBOOK.md       # AI Agent 开发手册
```

---

## 开发流程

### 1. 创建分支

```bash
git checkout -b feat/your-feature-name
# 或
git checkout -b fix/your-bug-fix
```

### 2. 编写代码

遵循现有代码风格：

- **Python**: 使用 `ruff` 做 lint 和 format，类型注解全覆盖
- **TypeScript**: 使用 `eslint` + `prettier`，严格模式
- **提交前**: `pre-commit run --all-files` 自动检查

### 3. 编写测试

```bash
# Python 模块
pytest tests/ -v --tb=short --cov=src --cov-report=term-missing

# Node.js 模块
npm test
```

### 4. 提交 Commit

遵循 Conventional Commits 规范：

```
feat: 添加用户注册 API
fix: 修复记忆写入时序问题
docs: 更新架构文档
refactor: 重构意图识别模块
test: 添加双链记忆测试
chore: 更新依赖版本
```

### 5. 发起 PR

- PR 标题清晰描述变更
- 关联相关 Issue（`Closes #123`）
- 确保 CI 全部通过
- 请求代码审查

---

## 代码规范

### Python

- 类型注解：所有函数签名必须有类型
- 文档字符串：公开 API 必须有 docstring
- 错误处理：不允许空 except，必须记录日志
- 异步优先：I/O 操作必须使用 async/await
- 配置：禁止硬编码，全部走环境变量

```python
# ✅ 正确
async def get_user(user_id: str, db: AsyncSession) -> User:
    """Retrieve user by DID. Raises UserNotFound if missing."""
    user = await db.get(User, user_id)
    if not user:
        raise UserNotFound(f"DID {user_id} not registered")
    return user

# ❌ 错误
def get_user(user_id):
    user = db.query(user_id)  # 无类型注解，无错误处理
    return user
```

### TypeScript

- 严格模式（`strict: true`）
- 接口定义优先于 type
- 异步函数明确返回 Promise
- 禁止 `any`（除非必要且有注释说明）

```typescript
// ✅ 正确
async function fetchProfile(did: string): Promise<UserProfile> {
  const res = await fetch(`${API_URL}/users/${did}`);
  if (!res.ok) throw new Error(`Failed to fetch profile: ${res.status}`);
  return res.json();
}

// ❌ 错误
function fetchProfile(did) {
  return fetch(API_URL + '/users/' + did).then(r => r.json());
}
```

---

## 测试要求

| 模块 | 最低覆盖率 | 测试命令 |
|------|-----------|----------|
| alpha-id | 67% | `pytest tests/ -q --cov=src --cov-fail-under=67` |
| nebula | — | `pytest tests/ -v` |
| DS | — | `npm test` |
| core | — | `npm test` |

- 新增功能必须附带测试
- Bug 修复必须有回归测试
- CI 覆盖率不达标则 PR 无法合并

---

## 安全报告

发现安全漏洞？请 **不要** 公开 Issue，改为：

- 邮件联系: wenwanqing1217@github.com
- 或 GitHub Security Advisory 私密报告

---

## 行为准则

- 友善、包容、尊重
- 欢迎所有水平的贡献者
- 聚焦技术，避免人身攻击
- 不同意见 → 讨论 → 共识

---

## 常见问题

**Q: 我想贡献但不知道从哪里开始？**
A: 查看 Issue 标签 `good first issue` 或 `help wanted`。

**Q: 发现了一个 bug？**
A: 先搜索已有 Issue，确认未被报告后创建新 Issue，附上复现步骤。

**Q: 有功能建议？**
A: 创建 Issue 标签 `feature request`，说明使用场景和预期行为。

---

<p align="center">
  <sub>感谢每一位贡献者 — Ghost 因你而更好。</sub>
</p>
