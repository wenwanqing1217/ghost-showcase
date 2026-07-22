@echo off
chcp 65001 >nul
echo ==========================================
echo   MindFlow Portfolio Demo Launcher
echo ==========================================
echo.
echo   [1] MindFlow - AI Workflow Platform (端口 3000 + 3001)
echo   [2] DS - AI Autonomous Shopify Shop (端口 3000)
echo   [3] ai综艺 - AI Variety Show (端口 5173)
echo   [4] ZCode Brain - Orchestration Layer (npm test)
echo   [5] MindFlow Map - AI 工作流引擎 (端口 2002)
echo   [6] AID - Alpha-ID 数字身份 (端口 8000)
echo   [7] 全部启动
echo   [0] 退出
echo.
set /p choice="请输入选项 (0-7): "

if "%choice%"=="1" goto mindflow
if "%choice%"=="2" goto ds
if "%choice%"=="3" goto ai
if "%choice%"=="4" goto zcode
if "%choice%"=="5" goto mindflowmap
if "%choice%"=="6" goto aid
if "%choice%"=="7" goto all
if "%choice%"=="0" goto end
goto end

:mindflow
echo.
echo 启动 MindFlow...
echo 前端: http://localhost:3000
echo 后端: http://localhost:3001
echo.
cd mindflow\apps\web
start "MindFlow Web" cmd /c "npm run dev"
timeout /t 3 /nobreak >nul
cd ..\..\apps\api
start "MindFlow API" cmd /c "npm run dev"
echo MindFlow 已启动！
pause
goto end

:ds
echo.
echo 启动 DS...
echo 访问: http://localhost:3000
echo.
cd DS
start "DS Dashboard" cmd /c "npm run dev"
echo DS 已启动！
pause
goto end

:ai
echo.
echo 启动 ai综艺...
echo 访问: http://localhost:5173
echo.
cd "ai综艺"
start "AI Variety Show" cmd /c "npm run dev"
echo ai综艺 已启动！
pause
goto end

:zcode
echo.
echo 运行 ZCode Brain 测试...
cd zcode-brain
call npm test
echo.
pause
goto end

:mindflowmap
echo.
echo 启动 MindFlow Map...
echo 访问: http://localhost:2002
echo API 文档: http://localhost:2002/docs
echo.
cd mindflow-map
start "MindFlow Map" cmd /c "uvicorn mindflow_map.main:app --reload --port 2002"
echo MindFlow Map 已启动！
pause
goto end

:aid
echo.
echo 启动 AID (Alpha-ID)...
echo 访问: http://localhost:8000
echo.
cd AID\projects
start "AID" cmd /c "python main.py"
echo AID 已启动！
pause
goto end

:all
echo.
echo 启动全部项目...
cd mindflow\apps\web
start "MindFlow Web" cmd /c "npm run dev"
timeout /t 2 /nobreak >nul
cd ..\..\apps\api
start "MindFlow API" cmd /c "npm run dev"
timeout /t 2 /nobreak >nul
cd ..\..\..\DS
start "DS Dashboard" cmd /c "set PORT=3004 && npm run dev"
timeout /t 2 /nobreak >nul
cd ..\"ai综艺"
start "AI Variety Show" cmd /c "npm run dev"
timeout /t 2 /nobreak >nul
cd ..\mindflow-map
start "MindFlow Map" cmd /c "uvicorn mindflow_map.main:app --reload --port 2002"
timeout /t 2 /nobreak >nul
cd ..\AID\projects
start "AID" cmd /c "python main.py"
echo.
echo 全部项目已启动！
echo.
echo   MindFlow Web:  http://localhost:3000
echo   MindFlow API:  http://localhost:3001
echo   DS Dashboard:  http://localhost:3004
echo   AI Variety:    http://localhost:5173
echo   MindFlow Map:  http://localhost:2002
echo   AID:           http://localhost:8000
echo.
pause
goto end

:end
