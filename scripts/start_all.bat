@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo   Ghost Workspace - Start All Services
echo ========================================
echo.

:: 1. ?? AlphaID (? demo ????? Ghost.html + ??/??/?? API)
echo [1/3] Starting AlphaID (Identity Layer :8000, demo mode)...
set PYTHONPATH=D:\MW\alphaid\projects\src
start "AlphaID" cmd /k "cd /d D:\MW\alphaid\projects\src && D:\MW\alphaid\projects\.venv\Scripts\python -m entrypoints.api --port 8000 --demo"

timeout /t 4 /nobreak >nul

:: 2. ?? Nebula (Workflow Engine)
echo [2/3] Starting Nebula (Workflow Engine :2002)...
cd /d D:\MW\nebula
start "Nebula" cmd /k "python -m uvicorn mindflow_map.main:app --host 0.0.0.0 --port 2002"

timeout /t 4 /nobreak >nul

:: 3. ?? Gateway (Unified API Gateway)
echo [3/3] Starting Gateway (Unified API :18080)...
cd /d D:\MW\ghost-main\gateway
start "Gateway" cmd /k "D:\MW\ghost-main\gateway\.venv\Scripts\python -m uvicorn app:app --host 0.0.0.0 --port 18080"

echo.
echo ========================================
echo   All services started!
echo ========================================
echo   Gateway: http://localhost:18080
echo   AlphaID: http://localhost:8000
echo   Nebula:  http://localhost:2002
echo   Ghost.html: http://localhost:8000/
echo ========================================
echo.
echo Press any key to run Health Check...
pause >nul

python D:\MW\scripts\health_check.py
pause
