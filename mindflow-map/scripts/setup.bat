@echo off
chcp 65001 >nul
title MindFlow Map - Setup
echo ========================================
echo   MindFlow Map 环境初始化
echo ========================================

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python ^>= 3.10
    pause
    exit /b 1
)

REM 检查虚拟环境
if not exist venv\Scripts\activate (
    echo [1/4] 创建虚拟环境...
    python -m venv venv
)

echo [2/4] 激活虚拟环境...
call venv\Scripts\activate.bat

echo [3/4] 安装依赖...
pip install -r requirements.txt -q

echo [4/4] 初始化数据库...
python -c "import asyncio; from mindflow_map.memory.store import MemoryStore; s = MemoryStore('sqlite+aiosqlite:///./mindflow_map.db'); asyncio.run(s.init()); print('数据库初始化完成')"

echo.
echo ========================================
echo   初始化完成！
echo   运行 start.bat 启动服务
echo ========================================
pause
