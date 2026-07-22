@echo off
chcp 65001 >nul
echo ==========================================
echo   Ghost - Portfolio Demo
echo ==========================================
echo.
echo [1/4] 检查 Flow...
cd flow
if not exist apps\web\.next\BUILD_ID (
    echo   正在构建 Flow...
    call npm run build
) else (
    echo   Flow 已构建
)
echo.
echo [2/4] 检查 Pulse...
cd ..\pulse
if not exist .next\BUILD_ID (
    echo   正在构建 Pulse...
    call npx next build
) else (
    echo   Pulse 已构建
)
echo.
echo [3/4] 检查 Stage...
cd ..\stage
if not exist dist\index.html (
    echo   正在构建 Stage...
    call npm run build
) else (
    echo   Stage 已构建
)
echo.
echo [4/4] 检查 Core...
cd ..\core
call npm test
echo.
echo ==========================================
echo   全部就绪 - 运行 start-demo.bat 启动演示
echo ==========================================
pause
