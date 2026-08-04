<!-- ════════════════════════════════════════════════════════════════════ -->
<!-- STATUS: ACTIVE -->
<!-- 贡献规范文件，所有贡献者必须阅读。开发规范详见 AGENTS.md。 -->
<!-- ════════════════════════════════════════════════════════════════════ -->

# Ghost Platform — CONTRIBUTING.md

> 参与 Ghost Platform 开发前请阅读本文件。

---

## 开发流程

1. Fork / Clone 仓库（含 submodule）：
   ```bash
   git clone --recursive https://github.com/wenwanqing1217/ghost-platform.git
   ```
2. 创建功能分支：`git checkout -b feat/your-feature`
3. 遵循提交信息规范（见 AGENTS.md 第 4 节）
4. 确保 CI 通过后再提交 PR
5. PR 描述中必须包含：改动摘要、影响的服务、是否需要更新文档

---

## 环境搭建

### 前提条件

- Docker + Docker Compose
- Python 3.12+
- Node.js 20+
- Redis 7+
- PostgreSQL 16+

### 快速启动（全栈）

```bash
# 1. 克隆（含 submodule）
git clone --recursive <repo-url>
cd ghost-platform

# 2. 配置环境变量
cp DS/.env.example DS/.env
cp ghost-main/gateway/.env.example ghost-main/gateway/.env
cp alphaid/projects/.env.example alphaid/projects/.env

# 3. 启动所有服务
make up

# 4. 检查状态
make ps
```

### 单服务开发

```bash
# Python 服务（Alpha-ID / Gateway / Nebula / Orchestrator）
cd <service-dir>
pip install -e ".[dev]"
python -m pytest tests/ -v

# TypeScript 服务（Ghost DS / Flow）
cd DS  # 或 cd flow
npm install
npm run dev
```

---

## 代码规范

### Python

- 格式化：`ruff format .`
- Lint：`ruff check .`
- 类型检查：`pyright .`
- 行长度：100 字符

### TypeScript

- Lint：`npx eslint src --ext .ts,.tsx`
- 格式化：`npx prettier --write "src/**/*.{ts,tsx}"`

---

## 测试

```bash
# 运行所有测试
make test

# 运行 Python 测试
make test-py

# 运行 TypeScript 检查
make test-ts
```

---

## 常见问题

### Submodule 未初始化

```bash
git submodule update --init --recursive
```

### Redis 连接失败

确保 `docker compose up redis` 已启动，且 `REDIS_URL` 配置正确。

### EventBus 事件不消费

检查 `eventbus-init.ts` 是否调用了 `startConsuming()`，以及 Redis consumer group 是否已创建。

---

## 联系方式

- 项目负责人：@wenwanqing1217
- 问题反馈：[GitHub Issues](https://github.com/wenwanqing1217/ghost-platform/issues)
