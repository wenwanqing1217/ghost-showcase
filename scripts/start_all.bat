@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo   Ghost Workspace - Start All Services
echo ========================================
echo.

:: 启动 AlphaID (Python FastAPI :8000)
echo [1/3] Starting AlphaID (Identity Layer :8000)...
start "AlphaID" cmd /k "cd /d D:\MW\alphaid\projects && ..\.venv\Scripts\python -m src.entrypoints.api --reload --port 8000"

timeout /t 3 /nobreak >nul

:: 启动 Nebula (Python FastAPI :2002)
echo [2/3] Starting Nebula (Workflow Engine :2002)...
start "Nebula" cmd /k "cd /d D:\MW\nebula && ..\.venv\Scripts\python -m mindflow_map.main --reload --port 2002"

timeout /t 3 /nobreak >nul

:: 启动 Gateway (Unified API Gateway :18080)
echo [3/3] Starting Gateway (Unified API :18080)...
start "Gateway" cmd /k "cd /d D:\MW\ghost-main\gateway && ..\.venv\Scripts\python app.py"

echo.
echo ========================================
echo   All services started!
echo   Gateway: http://localhost:18080
echo   AlphaID: http://localhost:8000
echo   Nebula:  http://localhost:2002
echo ========================================
echo.
echo Press any key to run Health Check...
pause >nul

python D:\MW\scripts\health_check.py
