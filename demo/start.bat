@echo off
chcp 65001 >nul
echo ==========================================
echo   Ghost — 演示启动
echo ==========================================
echo.
echo 正在启动演示服务器...
echo 浏览器打开: http://localhost:8080
echo 按 Ctrl+C 停止
echo.
python -m http.server 8080 --bind 127.0.0.1
