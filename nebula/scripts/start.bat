@echo off
chcp 65001 >nul
echo ========================================
echo MindFlow Map - 统一启动脚本
echo ========================================
echo.

cd /d "%~dp0.."

echo [1/4] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

echo [2/4] 安装依赖...
pip install -e .
playwright install chromium >nul 2>&1

echo [3/4] 启动后端服务...
echo 检查端口 2002 是否被占用...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :2002 ^| findstr LISTENING') do (
    echo 发现端口 2002 被进程 %%a 占用，正在终止...
    taskkill /PID %%a /F >nul 2>&1
    timeout /t 2 /nobreak >nul
)

echo MindFlow Map 已启动！
echo API 文档：http://localhost:2002/docs
echo Workspace：http://localhost:2002/workspace
echo 健康检查：http://localhost:2002/health
echo.
echo 按 Ctrl+C 停止服务
echo.

set PYTHONPATH=src
uvicorn mindflow_map.main:app --reload --port 2002 --host 0.0.0.0

pause
