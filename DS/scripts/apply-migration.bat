@echo off
REM apply-migration.bat — 应用 tenantId + storeMode + settings 迁移
REM 用法: 双击运行或在命令行执行
REM 依赖: psql 在 PATH 中，.env 文件配置了 DB_USER/DB_PASSWORD/DB_NAME

setlocal enabledelayedexpansion

cd /d "%~dp0"

REM 加载 .env 变量
for /f "usebackq tokens=*" %%a in (`findstr /v "^#" .env ^| findstr /v "^$"`) do (
  for /f "tokens=1,* delims==" %%b in ("%%a") do (
    set "%%b=%%c"
  )
)

if "%DB_PASSWORD%"=="" (
  echo [ERROR] DB_PASSWORD 未在 .env 中配置
  pause
  exit /b 1
)

set "DB_USER=%DB_USER:ghost%"
set "DB_NAME=%DB_NAME:ghost%"
set "DB_HOST=%DB_HOST:localhost%"
set "DB_PORT=%DB_PORT:5432%"

echo [INFO] Applying migration to %DB_NAME%@%DB_HOST%:%DB_PORT%...
echo.

set "PGPASSWORD=%DB_PASSWORD%"
psql -h "%DB_HOST%" -p "%DB_PORT%" -U "%DB_USER%" -d "%DB_NAME%" -f "prisma\migrations\20250804_add_tenant_storemode\migration.sql"

if %ERRORLEVEL% EQU 0 (
  echo.
  echo [OK] Migration applied successfully!
  echo.
  echo Next steps:
  echo   1. cd DS ^& npx prisma generate    %% 重新生成 Prisma Client
  echo   2. cd DS ^& npm run db:seed         %% 填充演示数据（可选）
) else (
  echo.
  echo [ERROR] Migration failed!
)

pause
