@echo off
chcp 65001 >nul 2>&1
title Ghost Platform — 一键启动
echo ========================================
echo   Ghost Platform — 一键启动（Docker 全栈）
echo ========================================
echo.

:: 1. 检查 Docker Desktop 是否运行
docker info >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker Desktop 未运行，请先启动 Docker Desktop。
    pause
    exit /b 1
)
echo [1/4] Docker 已就绪

:: 2. 检查 .env 是否存在
if not exist ".env" (
    echo [错误] 缺少 .env 文件。请先执行: copy .env.example .env
    pause
    exit /b 1
)
echo [2/4] .env 配置已加载

:: 3. 启动全栈（14 个服务）
echo [3/4] 正在启动全栈服务（首次需构建镜像，请耐心等待）...
docker compose up -d --build
if errorlevel 1 (
    echo [错误] 服务启动失败，请查看上方日志。
    pause
    exit /b 1
)

:: 4. 等待健康检查
echo [4/4] 等待服务健康检查（约 30 秒）...
timeout /t 30 /nobreak >nul

echo.
echo ========================================
echo   服务状态
echo ========================================
docker compose ps
echo.
echo ========================================
echo   访问入口
echo ========================================
echo   Ghost DS 看板:  http://localhost:3001
echo   服务健康页:     http://localhost:3001/health
echo   Gateway API:    http://localhost:18080
echo   Alpha-ID:       http://localhost:8000
echo   Prometheus:     http://localhost:9090
echo   Grafana:        http://localhost:3000
echo ========================================
echo.
echo 飞书：给机器人发消息即可下达运营命令（文案/视频/发布）
echo 停止全部服务: docker compose down
echo 查看实时日志: docker compose logs -f
echo.
start http://localhost:3001/health
pause
