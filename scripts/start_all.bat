@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo   Ghost Workspace - 启动全部服务
echo ========================================
echo.

:: 启动 AlphaID (Python FastAPI :8000)
echo [1/4] 启动 AlphaID (身份层 :8000)...
start "AlphaID" cmd /k "cd /d D:\MW\alphaid\projects && ..\.venv\Scripts\python -m src.entrypoints.api --reload --port 8000"

timeout /t 3 /nobreak >nul

:: 启动 Nebula (Python FastAPI :2002)
echo [2/4] 启动 Nebula (执行层 :2002)...
start "Nebula" cmd /k "cd /d D:\MW\nebula && ..\.venv\Scripts\python -m mindflow_map.main --reload --port 2002"

timeout /t 3 /nobreak >nul

:: 启动 DS (Next.js :3004)
echo [3/4] 启动 DS (电商后端 :3004)...
start "DS" cmd /k "cd /d D:\MW\DS && npm run dev"

timeout /t 3 /nobreak >nul

:: 启动 Gateway (统一 API 网关 :18080)
echo [4/4] 启动 Gateway (统一 API 网关 :18080)...
start "Gateway" cmd /k "cd /d D:\MW\ghost-main\gateway && ..\.venv\Scripts\python app.py"

echo.
echo ========================================
echo   全部服务已启动!
echo   Gateway: http://localhost:18080
echo   AlphaID: http://localhost:8000
echo   Nebula:  http://localhost:2002
echo   DS:      http://localhost:3004
echo ========================================
echo.
echo 按任意键运行 Health Check...
pause >nul

python D:\MW\scripts\health_check.py
