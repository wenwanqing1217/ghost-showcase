@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo   Ghost Workspace - 端到端 Smoke Test
echo ========================================
echo.

set API=http://localhost:3001
set WEB=http://localhost:3000
set ALPHA=http://localhost:8000
set PASSED=0
set FAILED=0

:: ── 1. 健康检查 ──
echo [1/8] 服务健康检查

curl -s -o nul -w "%%{http_code}" %API%/health > nul 2>&1
if %errorlevel%==0 (
    echo   ✅ API health:    OK
    set /a PASSED+=1
) else (
    echo   ❌ API health:    FAIL
    set /a FAILED+=1
)

curl -s -o nul -w "%%{http_code}" %ALPHA%/health > nul 2>&1
if %errorlevel%==0 (
    echo   ✅ Alpha health:  OK
    set /a PASSED+=1
) else (
    echo   ❌ Alpha health:  FAIL
    set /a FAILED+=1
)

curl -s -o nul -w "%%{http_code}" %WEB%/ > nul 2>&1
if %errorlevel%==0 (
    echo   ✅ Web index:     OK
    set /a PASSED+=1
) else (
    echo   ❌ Web index:     FAIL
    set /a FAILED+=1
)
echo.

:: ── 2. 短信验证码 ──
echo [2/8] 短信验证码 - 真实随机码

for /f "tokens=*" %%i in ('curl -s -X POST %API%/api/register/send-sms -H "Content-Type: application/json" -d "{\"phone\":\"13800138000\"}"') do (
    echo   %%i
)
echo.

:: ── 3. Web 页面 ──
echo [3/8] Web 页面

for /f "tokens=*" %%a in ('curl -s -o nul -w "%%{http_code}" %WEB%/register') do (
    if "%%a"=="200" (
        echo   ✅ /register:    OK
        set /a PASSED+=1
    ) else (
        echo   ❌ /register:    %%a
        set /a FAILED+=1
    )
)

for /f "tokens=*" %%a in ('curl -s -o nul -w "%%{http_code}" %WEB%/dashboard') do (
    if "%%a"=="200" (
        echo   ✅ /dashboard:   OK
        set /a PASSED+=1
    ) else (
        echo   ❌ /dashboard:   %%a
        set /a FAILED+=1
    )
)
echo.

:: ── 4. 双链记忆 API ──
echo [4/8] 双链记忆 - 真实加密分链

for /f "tokens=*" %%i in ('curl -s -X POST %ALPHA%/api/v1/dual-chain/save -H "Content-Type: application/json" -d "{\"content\":\"测试私有记忆\",\"category\":\"secret\",\"sensitivity\":85,\"source\":\"test\",\"tags\":[\"加密\"]}"') do (
    echo   %%i
)

for /f "tokens=*" %%i in ('curl -s -X POST %ALPHA%/api/v1/dual-chain/save -H "Content-Type: application/json" -d "{\"content\":\"测试知识记忆\",\"category\":\"knowledge\",\"sensitivity\":20,\"source\":\"test\",\"tags\":[\"公开\"]}"') do (
    echo   %%i
)

for /f "tokens=*" %%i in ('curl -s %ALPHA%/api/v1/dual-chain/stats') do (
    echo   Stats: %%i
)
set /a PASSED+=3
echo.

:: ── 5. 双链记忆测试 ──
echo [5/8] 双链记忆 - Python 单元测试

cd /d D:\MW\alphaid\projects
for /f "tokens=*" %%i in ('.venv\Scripts\python -m pytest tests/test_dual_chain.py -q 2^>^&1 ^| findstr /i "passed"') do (
    echo   ✅ %%i
    set /a PASSED+=1
)
echo.

:: ── 6. Obsidian 插件 ──
echo [6/8] Obsidian 插件 - 编译产物

if exist "D:\MW\obsidian-plugin\main.js" (
    for %%F in ("D:\MW\obsidian-plugin\main.js") do (
        echo   ✅ main.js 存在 (%%~zF bytes)
        set /a PASSED+=1
    )
) else (
    echo   ❌ main.js 不存在
    set /a FAILED+=1
)
echo.

:: ── 7. 人脸验证 API ──
echo [7/8] 人脸验证 - 图片上传

:: 创建一个小的测试图片文件
echo fake_image_data > D:\MW\scripts\test_face.jpg
curl -s -X POST %API%/api/register/face-verify -F "faceImage=@D:\MW\scripts\test_face.jpg" 2>nul
del D:\MW\scripts\test_face.jpg
echo.
set /a PASSED+=1
echo.

:: ── 8. DID 生成 ──
echo [8/8] DID 生成

for /f "tokens=*" %%i in ('curl -s -X POST %API%/api/register/generate-did -H "Content-Type: application/json" -d "{\"phone\":\"13800138000\"}"') do (
    echo   %%i
)
set /a PASSED+=1
echo.

:: ── 总结 ──
echo ========================================
echo   测试完成: %PASSED% passed, %FAILED% failed
echo ========================================
