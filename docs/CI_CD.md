# CI/CD 指南

## 概述

本仓库使用 **GitHub Actions** 实现持续集成，采用"变更检测 → 按需触发"的分层策略。

```
┌─────────────────────────────────────────────┐
│         根目录 .github/workflows/ci.yml       │
│                                             │
│  1. 检测哪些子项目有变更                        │
│  2. 触发对应子项目的 CI 流程                    │
│  3. 汇总所有结果作为最终门禁                     │
└───────────┬─────────┬──────────┬────────────┘
            │         │          │
     ┌──────▼──┐ ┌────▼────┐ ┌───▼──────────┐
     │mindflow │ │   DS    │ │  zcode-brain │
     │  -map   │ │(Next.js)│ │   (Node/TS)  │
     │(Python) │ │         │ │              │
     └─────────┘ └─────────┘ └──────────────┘
           │
     ┌─────▼─────┐
     │    AID    │
     │  (Python) │
     └───────────┘
```

## 各子项目 CI 状态

| 项目 | CI | Lint | Test | Pre-commit | 触发条件 |
|------|-----|------|------|------------|---------|
| **mindflow-map** | ✅ | ruff + mypy | pytest + coverage | ✅ | `mindflow-map/**` 变更 |
| **DS** | ✅ | ESLint (next) | vitest + coverage | ✅ | `DS/**` 变更 |
| **AID/projects** | ✅ | ruff + pyright | pytest + coverage (≥67%) | ✅ | `AID/**` 变更 |
| **zcode-brain** | ✅ | ESLint | vitest | ✅ | `zcode-brain/**` 变更 |
| **mindflow** | ✅ | ESLint | vitest | ❌ | 已有独立 CI |

## 工作流文件

### 根目录编排 (`/.github/workflows/ci.yml`)
- 使用 `dorny/paths-filter` 检测变更范围
- 仅对有变更的子项目触发 CI
- 最终 `all-pass` 门禁汇总所有结果

### 复用模板

| 模板 | 适用 | 输入参数 |
|------|------|---------|
| `reusable-python-ci.yml` | mindflow-map, AID | `project-dir`, `python-versions`, `lint-command`, `test-command` |
| `reusable-node-ci.yml` | DS, zcode-brain | `project-dir`, `node-version`, `lint-command`, `test-command`, `build-command` |

### 子项目独立 CI
- `mindflow-map/.github/workflows/ci.yml` — 已有，含 test/frontend/security/docker 4 个 job
- `AID/projects/.github/workflows/ci.yml` — 已有，含 lint/typecheck/test 3 个 job
- `mindflow/.github/workflows/ci.yml` — 已有，含 test/lint/deploy 4 个 job

## 本地开发

### 安装 pre-commit
```bash
pip install pre-commit
pre-commit install
```

### 子项目单独安装依赖
```bash
# mindflow-map
cd mindflow-map && pip install -e ".[dev]"

# DS
cd DS && npm ci

# AID
cd AID/projects && pip install -e ".[test]"

# zcode-brain
cd zcode-brain && npm ci
```

### 手动运行 CI 等价命令
```bash
# Python 项目
ruff check src/ tests/       # lint
mypy src/                    # type check
pytest tests/ -v --tb=short  # test

# Node 项目
npm run lint                 # lint
npm run typecheck            # type check (如果有)
npm test                     # test
```

## 依赖自动更新

Dependabot (`.github/dependabot.yml`) 每周检查：
- GitHub Actions 版本
- npm 依赖 (DS, zcode-brain, mindflow)
- pip 依赖 (mindflow-map, AID)

## 分支保护建议

在 GitHub Settings → Branches 中为 `main`/`master` 配置：
1. 要求 PR 合并前通过状态检查
2. 要求 `all-pass` job 通过
3. 要求分支最新
