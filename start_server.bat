@echo off
chcp 65001 >nul
echo =====================================
echo   MindFlow Map - 飞书机器人后端
echo =====================================
echo.
echo 启动服务...
echo 访问 http://localhost:2002/docs 查看 API
echo 访问 http://localhost:2002/api/v1/webhook/feishu 是 Webhook 端点
echo.
cd /d D:\MW\mindflow-map
set PYTHONPATH=D:\MW\mindflow-map\src
python -m uvicorn mindflow_map.main:app --host 0.0.0.0 --port 2002 --log-level info
pause
