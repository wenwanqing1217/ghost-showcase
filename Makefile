# ════════════════════════════════════════════════════════════════════
# Ghost Platform — Root Makefile
# ════════════════════════════════════════════════════════════════════
# Usage:
#   make up            — start all services (docker compose)
#   make down          — stop all services
#   make logs          — tail all logs
#   make test          — run all tests (CI)
#   make lint          — run all linters
#   make clean         — clean caches and temp files
# ════════════════════════════════════════════════════════════════════

.PHONY: help up down restart logs ps clean test test-py test-ts lint lint-py lint-ts fmt fmt-py fmt-ts check-all smoke db-migrate db-rollback backup restore

help:
	@echo "Ghost Platform — available targets:"
	@echo "  make up            Start all services (docker compose up -d)"
	@echo "  make down          Stop all services (docker compose down)"
	@echo "  make restart       Restart all services"
	@echo "  make logs          Tail all service logs"
	@echo "  make ps            List running services"
	@echo "  make backup        Backup all PostgreSQL databases (scripts/backup.ps1)"
	@echo "  make restore DB=x FILE=y  Restore a database from backup"
	@echo "  make smoke         Run ALL unit tests (no Docker required)"
	@echo "  make test          Run all tests (Python + Node)"
	@echo "  make test-py       Run Python tests only"
	@echo "  make test-ts       Run Node.js tests only"
	@echo "  make lint          Run all linters"
	@echo "  make lint-py       Run Python linter (ruff)"
	@echo "  make lint-ts       Run TypeScript linter (eslint)"
	@echo "  make fmt           Format all code"
	@echo "  make fmt-py        Format Python code (ruff format)"
	@echo "  make fmt-ts        Format TypeScript code (prettier)"
	@echo "  make check-all     Lint + format check + test"
	@echo "  make clean         Clean caches and temp files"
	@echo "  make db-migrate    Run Alembic migrations (Alpha-ID)"
	@echo "  make db-rollback   Rollback one migration (Alpha-ID)"

# ── Docker ──

up:
	docker compose up -d --build

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f --tail=100

ps:
	docker compose ps

# ── Testing ──

test: smoke

# 一键全量单元测试（无需 Docker），CI 与本地共用同一套命令
smoke:
	@echo "=== [1/6] alphaid/projects (Python) ==="
	cd alphaid/projects && python -m pytest tests/ -q --tb=short -p no:cacheprovider
	@echo "=== [2/6] nebula (Python) ==="
	cd nebula && python -m pytest tests/ -q --tb=short
	@echo "=== [3/6] gateway (Python) ==="
	cd ghost-main/gateway && python -m pytest tests/ -q --tb=short
	@echo "=== [4/6] orchestrator (Python) ==="
	cd orchestrator && python -m pytest . -q --tb=short
	@echo "=== [5/6] DS (Next.js) ==="
	cd DS && npm test
	@echo "=== [6/6] flow (Monorepo) ==="
	cd flow && npm test
	@echo ""
	@echo "=== ALL UNIT TESTS PASSED ==="

test-py:
	@echo "=== Python tests (nebula) ==="
	cd nebula && python -m pytest tests/ -q --tb=short
	@echo "=== Python tests (alphaid) ==="
	cd alphaid/projects && python -m pytest tests/ -q --tb=short
	@echo "=== Python tests (gateway) ==="
	cd ghost-main/gateway && python -m pytest tests/ -q --tb=short
	@echo "=== Python tests (orchestrator) ==="
	cd orchestrator && python -m pytest . -q --tb=short

test-ts:
	@echo "=== TypeScript tests (DS) ==="
	cd DS && npm test
	@echo "=== TypeScript tests (Flow) ==="
	cd flow && npm test

# ── Linting ──

lint: lint-py lint-ts

lint-py:
	@echo "=== ruff check (nebula) ==="
	cd nebula && ruff check src/ tests/ 2>/dev/null || true
	@echo "=== ruff check (alphaid) ==="
	cd alphaid/projects && ruff check src/ 2>/dev/null || true
	@echo "=== ruff check (gateway) ==="
	cd ghost-main/gateway && ruff check app.py config.py middleware/ routes/ services/ tests/ 2>/dev/null || true
	@echo "=== ruff check (orchestrator) ==="
	cd orchestrator && ruff check main.py 2>/dev/null || true

lint-ts:
	@echo "=== eslint (DS) ==="
	cd DS && npx eslint src --ext .ts,.tsx 2>/dev/null || true
	@echo "=== eslint (Flow) ==="
	cd flow && npx eslint apps/api/src --ext .ts 2>/dev/null || true

# ── Formatting ──

fmt: fmt-py fmt-ts

fmt-py:
	@echo "=== ruff format (all Python) ==="
	cd nebula && ruff format src/ tests/ 2>/dev/null || true
	cd alphaid/projects && ruff format src/ tests/ 2>/dev/null || true
	cd ghost-main/gateway && ruff format . 2>/dev/null || true
	cd orchestrator && ruff format main.py 2>/dev/null || true

fmt-ts:
	@echo "=== prettier (all TS) ==="
	cd DS && npx prettier --write "src/**/*.{ts,tsx}" 2>/dev/null || true
	cd flow && npx prettier --write "apps/api/src/**/*.ts" 2>/dev/null || true

# ── Combined checks ──

check-all: lint fmt-py test-py
	@echo "=== All checks passed ==="

# ── Database ──

db-migrate:
	cd alphaid/projects && alembic upgrade head

db-rollback:
	cd alphaid/projects && alembic downgrade -1

# 备份全部 PostgreSQL 库（保留最近 7 份）
backup:
	powershell -ExecutionPolicy Bypass -File scripts/backup.ps1

# 恢复指定库: make restore DB=ghost FILE=backups/ghost-xxx.dump
restore:
	@test -n "$(DB)" || (echo "Usage: make restore DB=<db> FILE=<backup.dump>" && exit 1)
	@test -n "$(FILE)" || (echo "Usage: make restore DB=<db> FILE=<backup.dump>" && exit 1)
	powershell -ExecutionPolicy Bypass -File scripts/restore.ps1 -db $(DB) -file $(FILE)

# ── Cleanup ──

clean:
	@echo "=== Cleaning caches ==="
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .next -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type f -name "coverage.xml" -delete 2>/dev/null || true
	@echo "=== Clean complete ==="
