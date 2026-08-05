@echo off
cd /d D:\MW\flow\apps\api
set PORT=3036
set HOST=127.0.0.1
start "FlowAPI" /MIN cmd /c "npx tsx src\index.ts"
echo Flow API starting at http://127.0.0.1:3036
echo Close that window to stop the service.
