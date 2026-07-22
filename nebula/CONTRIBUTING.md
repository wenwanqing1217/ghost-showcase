# 贡献指南

感谢你对 MindFlow Map 的关注！以下是快速上手指南。

## 环境要求

- Python >= 3.10
- pip
- (可选) Docker & Docker Compose
- (可选) Helm 3（Kubernetes 部署）

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/mindflow/mindflow-map.git
cd mindflow-map

# 2. 安装依赖
make install

# 3. 启动开发服务器
make dev
```

## 常用命令

```bash
make test       # 运行测试
make lint       # 代码检查
make format     # 代码格式化
make typecheck  # 类型检查
make pre-commit # 运行所有检查
```

## 提交规范

请遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档更新
- `style:` 代码格式（不影响逻辑）
- `refactor:` 重构
- `perf:` 性能优化
- `test:` 测试相关
- `chore:` 构建/工具链变更

示例：`feat(api): add OpenAPI schema enhancement`

## 代码规范

- 使用 [ruff](https://docs.astral.sh/ruff/) 进行 lint 和格式化
- 使用 [mypy](https://mypy.readthedocs.io/) 进行类型检查
- 新功能必须包含单元测试
- API 变更需更新文档

## 项目结构

```
mindflow-map/
├── src/mindflow_map/          # 主代码
│   ├── api/                   # API 路由
│   ├── middleware/            # 中间件
│   ├── models/                # 数据模型与存储
│   ├── schemas/               # Pydantic 模型
│   └── core/                  # 核心功能（事件、缓存、指标）
├── tests/                     # 测试
├── docs/                      # 文档
├── helm/                      # Helm Chart
├── scripts/                   # 工具脚本
└── Makefile                   # 构建任务
```

## 问题反馈

- 提交 Issue：https://github.com/mindflow/mindflow-map/issues
- 安全漏洞：请发送邮件至 security@mindflow.ai
