@echo off
chcp 65001 >nul
echo ==========================================
echo   MindFlow Workspace - Portfolio Demo
echo ==========================================
echo.
echo [1/4] 检查 MindFlow...
cd mindflow
if not exist apps\web\.next\BUILD_ID (
    echo   正在构建 MindFlow...
    call npm run build
) else (
    echo   MindFlow 已构建
)
echo.
echo [2/4] 检查 DS...
cd ..\DS
if not exist .next\BUILD_ID (
    echo   正在构建 DS...
    call npx next build
) else (
    echo   DS 已构建
)
echo.
echo [3/4] 检查 ai综艺...
cd ..\ai综艺
if not exist dist\index.html (
    echo   正在构建 ai综艺...
    call npm run build
) else (
    echo   ai综艺 已构建
)
echo.
echo [4/4] 检查 ZCode Brain...
cd ..\zcode-brain
call npm test
echo.
echo ==========================================
echo   全部就绪 - 运行 start-demo.bat 启动演示
echo ==========================================
pause
