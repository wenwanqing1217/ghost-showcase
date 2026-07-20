.PHONY: help install dev test lint format typecheck clean run docker-build docker-up metrics openapi pre-commit

help: ## 显示帮助
	@echo "MindFlow Map - 可用命令："
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## 安装依赖
	@echo "🔧 安装依赖..."
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

dev: ## 启动开发服务器（带热重载）
	@echo "🚀 启动开发服务器..."
	uvicorn mindflow_map.main:app --reload --host 0.0.0.0 --port 8000

test: ## 运行测试
	@echo "🧪 运行测试..."
	python -m pytest tests/ -x -q

test-cov: ## 运行测试并生成覆盖率报告
	@echo "📊 生成覆盖率报告..."
	python -m pytest tests/ --cov=mindflow_map --cov-report=html

lint: ## 代码检查
	@echo "🔍 代码检查..."
	ruff check src/ tests/

format: ## 代码格式化
	@echo "✨ 格式化代码..."
	ruff check src/ tests/ --fix

typecheck: ## 类型检查
	@echo "🔎 类型检查..."
	mypy src/

clean: ## 清理临时文件
	@echo "🧹 清理..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	find . -type d -name '*.egg-info' -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .coverage -exec rm -rf {} +
	find . -type d -name htmlcov -exec rm -rf {} +

run: ## 运行生产服务器
	@echo "🚀 启动生产服务器..."
	uvicorn mindflow_map.main:app --host 0.0.0.0 --port 8000 --workers 4

docker-build: ## 构建 Docker 镜像
	@echo "🐳 构建 Docker 镜像..."
	docker build -t mindflow-map:latest .

docker-up: ## 启动 Docker Compose
	@echo "🐳 启动 Docker Compose..."
	docker-compose up -d

metrics: ## 查看 Prometheus metrics
	@echo "📊 获取 metrics..."
	curl -s http://localhost:8000/metrics

openapi: ## 导出 OpenAPI Schema
	@echo "📄 导出 OpenAPI Schema..."
	@python scripts/generate_openapi_spec.py

pre-commit: format lint typecheck test ## 运行所有 pre-commit 检查
	@echo "✅ 所有检查通过！"

# 默认目标
.DEFAULT_GOAL := help
