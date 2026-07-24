@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo   Ghost Workspace - 启动全部服务
echo ========================================
echo.

:: 启动 AlphaID (Python FastAPI :8000)
echo [1/3] 启动 AlphaID (Python :8000)...
start "AlphaID" cmd /k "cd /d D:\MW\alphaid\projects && ..\.venv\Scripts\python -m src.entrypoints.api --reload --port 8000"

timeout /t 3 /nobreak >nul

:: 启动 API (Fastify :3001)
echo [2/3] 启动 API (Fastify :3001)...
start "API" cmd /k "cd /d D:\MW\flow\apps\api && npm run dev"

timeout /t 3 /nobreak >nul

:: 启动 Web (Next.js :3000)
echo [3/3] 启动 Web (Next.js :3000)...
start "Web" cmd /k "cd /d D:\MW\flow\apps\web && npm run dev"

echo.
echo ========================================
echo   全部服务已启动!
echo   Web:     http://localhost:3000
echo   API:     http://localhost:3001
echo   AlphaID: http://localhost:8000
echo ========================================
echo.
echo 按任意键运行 Smoke Test...
pause >nul

call D:\MW\scripts\smoke_test.bat
