@echo off
chcp 65001 >nul
title Ghost 桌面精灵一键安装

echo ========================================
echo   Ghost 桌面精灵 - 一键安装
echo ========================================
echo.

:: 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.11-3.13
    pause
    exit /b 1
)

:: 安装 alpha-id-zix
echo [1/4] 安装 alpha-id-zix 核心包...
pip install alpha-id-zix -q

:: 安装 Ollama（如果未安装）
echo [2/4] 检查 Ollama...
where ollama >nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] Ollama 未安装，下载地址：https://ollama.ai
) else (
    echo [OK] Ollama 已安装
)

:: 安装桌面精灵依赖
echo [3/4] 安装桌面精灵依赖...
pip install pyautogui pillow -q

:: 初始化配置
echo [4/4] 初始化配置...
aid init

echo.
echo ========================================
echo   安装完成！
echo   启动桌面精灵：aid-daemon
echo ========================================
pause
