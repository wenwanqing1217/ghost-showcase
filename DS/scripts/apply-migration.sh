#!/bin/bash
# apply-migration.sh — 应用 tenantId + storeMode + settings 迁移
# 用法: bash apply-migration.sh
# 依赖: psql (PostgreSQL 客户端), .env 文件配置了 DB_USER/DB_PASSWORD/DB_NAME

set -e

# 加载 .env 变量
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

DB_USER="${DB_USER:-ghost}"
DB_PASSWORD="${DB_PASSWORD:?DB_PASSWORD required}"
DB_NAME="${DB_NAME:-ghost}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

echo "📦 Applying migration to ${DB_NAME}@${DB_HOST}:${DB_PORT}..."

PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "prisma/migrations/20250804_add_tenant_storemode/migration.sql"

echo "✅ Migration applied successfully!"
echo ""
echo "Next steps:"
echo "  1. cd DS && npx prisma generate    # 重新生成 Prisma Client"
echo "  2. cd DS && npm run db:seed         # 填充演示数据（可选）"
