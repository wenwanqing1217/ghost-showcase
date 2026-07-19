FROM python:3.11-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 安装 Playwright 浏览器（可选，按需启用）
# RUN playwright install chromium

# 暴露端口
EXPOSE 8000

# 启动服务
CMD ["uvicorn", "mindflow_map.main:app", "--host", "0.0.0.0", "--port", "8000"]
