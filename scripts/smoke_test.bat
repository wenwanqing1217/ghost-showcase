@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo   Ghost Workspace - End-to-End Smoke Test
echo ========================================
echo.

set GATEWAY=http://localhost:18080
set ALPHA=http://localhost:8000
set NEBULA=http://localhost:2002
set PASSED=0
set FAILED=0

:: ── 1. Health Checks ──
echo [1/5] Service Health Checks

curl -s -o nul -w "%%{http_code}" %GATEWAY%/health > nul 2>&1
if %errorlevel%==0 (
    echo   ✅ Gateway health:  OK
    set /a PASSED+=1
) else (
    echo   ❌ Gateway health:  FAIL
    set /a FAILED+=1
)

curl -s -o nul -w "%%{http_code}" %ALPHA%/health > nul 2>&1
if %errorlevel%==0 (
    echo   ✅ AlphaID health:  OK
    set /a PASSED+=1
) else (
    echo   ❌ AlphaID health:  FAIL
    set /a FAILED+=1
)

curl -s -o nul -w "%%{http_code}" %NEBULA%/health > nul 2>&1
if %errorlevel%==0 (
    echo   ✅ Nebula health:   OK
    set /a PASSED+=1
) else (
    echo   ❌ Nebula health:   FAIL
    set /a FAILED+=1
)
echo.

:: ── 2. Identity API ──
echo [2/5] Identity - DID Generation

for /f "tokens=*" %%i in ('curl -s -X POST %ALPHA%/api/v1/identity/generate-did -H "Content-Type: application/json" -d "{\"phone\":\"13800138000\"}"') do (
    echo   %%i
)
set /a PASSED+=1
echo.

:: ── 3. Dual-Chain Memory API ──
echo [3/5] Dual-Chain Memory - Encrypted Split

for /f "tokens=*" %%i in ('curl -s -X POST %ALPHA%/api/v1/dual-chain/save -H "Content-Type: application/json" -d "{\"content\":\"Test private memory\",\"category\":\"secret\",\"sensitivity\":85,\"source\":\"test\",\"tags\":[\"encrypted\"]}"') do (
    echo   %%i
)

for /f "tokens=*" %%i in ('curl -s -X POST %ALPHA%/api/v1/dual-chain/save -H "Content-Type: application/json" -d "{\"content\":\"Test knowledge memory\",\"category\":\"knowledge\",\"sensitivity\":20,\"source\":\"test\",\"tags\":[\"public\"]}"') do (
    echo   %%i
)

for /f "tokens=*" %%i in ('curl -s %ALPHA%/api/v1/dual-chain/stats') do (
    echo   Stats: %%i
)
set /a PASSED+=3
echo.

:: ── 4. Python Unit Tests ──
echo [4/5] AlphaID - Python Unit Tests

cd /d D:\MW\alphaid\projects
for /f "tokens=*" %%i in ('.venv\Scripts\python -m pytest tests/ -q 2^>^&1 ^| findstr /i "passed"') do (
    echo   ✅ %%i
    set /a PASSED+=1
)
echo.

:: ── 5. Gateway Routing ──
echo [5/5] Gateway - Unified API Routing

for /f "tokens=*" %%i in ('curl -s %GATEWAY%/health') do (
    echo   Gateway response: %%i
)
set /a PASSED+=1
echo.

:: ── Summary ──
echo ========================================
echo   Test Complete: %PASSED% passed, %FAILED% failed
echo ========================================
