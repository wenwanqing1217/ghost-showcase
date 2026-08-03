# Ghost 用户手册

> 目标：从零开始，让一个人能装包、注册、连飞书、完成第一次数据采集
> 适用版本：alpha-id-zix >= 0.3.2
> 更新日期：2026-07-27

---

## 一、安装

```bash
pip install alpha-id-zix
```

验证安装：

```bash
aid --help
```

---

## 二、创建你的数字身份

```bash
aid init
```

这会在 `~/.alpha-id/` 下生成你的 DID 身份文件（私钥 + 公钥 + DID Document）。这是你的数字身份基础，不要删除。

查看身份：

```bash
aid identity show
```

---

## 三、采集你的数据

### 从 ChatGPT 导入

1. 打开 chat.openai.com → Settings → Data Controls → Export Data
2. 等待邮件通知，下载 ZIP 文件
3. 运行：

```bash
aid collect chatgpt ~/Downloads/chatgpt-data-export.zip
```

### 从其他来源导入

```bash
aid collect trae          # 从 Trae IDE 取回代码痕迹
aid detect                # 自动扫描本机有哪些数据可用
```

### 查看你的数字画像

```bash
aid profile show          # 终端显示
aid profile web           # 浏览器查看
```

---

## 四、注册 Web 账号

Alpha-ID 提供 Web 服务（DID 注册 + 双链记忆）。

### 启动服务

```bash
export AUTH_MASTER_KEY="你的随机密钥（32位以上）"
aid-api
```

浏览器打开 `http://localhost:8000`

### 注册流程

1. 点击「注册」
2. 输入手机号 → 获取验证码（演示模式自动填入）
3. 人脸认证（演示模式自动通过）
4. 生成 Alpha-ID（格式：`Alpha-XXX-YYY`）
5. 进入 A2A 生态区（可切换至 Mindflow 协作台）

---

## 五、Gateway API 调用

Gateway（`:18080`）是所有 API 的统一入口。以下为 curl 示例：

### 健康检查

```bash
curl http://localhost:18080/health
```

### 获取身份

```bash
curl "http://localhost:18080/v1/human/identity?alpha_id=Alpha-001"
```

### 聊天

```bash
curl -X POST http://localhost:18080/v1/human/chat \
  -H "Content-Type: application/json" \
  -d '{"alpha_id": "Alpha-001", "message": "你好"}'
```

### 意图解析

```bash
curl -X POST http://localhost:18080/v1/human/intent/parse \
  -H "Content-Type: application/json" \
  -d '{"text": "我是谁"}'
```

### 记忆图谱

```bash
curl "http://localhost:18080/v1/human/memory/graph"
```

### 搜索知识库

```bash
curl "http://localhost:18080/v1/human/memory/search?keyword=架构&limit=10"
```

### 存储记忆

```bash
curl -X POST http://localhost:18080/v1/human/memory/store \
  -H "Content-Type: application/json" \
  -d '{
    "alpha_id": "Alpha-001",
    "content": "今天学到了新东西",
    "category": "general",
    "tags": ["学习"]
  }'
```

### 仪表盘

```bash
curl http://localhost:18080/v1/human/dashboard
```

### 行业资讯

```bash
curl "http://localhost:18080/v1/agent/feeds/latest?industry=跨境电商&limit=5"
```

### 响应信封示例

所有 API 返回统一格式：

```json
{
  "success": true,
  "data": { ... },
  "ts": 1721890000,
  "request_id": "abc123def456"
}
```

| 字段 | 说明 |
|:-----|:-----|
| `success` | 请求是否成功 |
| `data` | 业务数据 |
| `ts` | Unix 时间戳 |
| `request_id` | 关联 ID（可用于追踪） |

### API 文档

- Swagger UI: `http://localhost:18080/docs`
- ReDoc: `http://localhost:18080/redoc`

完整 API 参考见：`docs/architecture/GATEWAY_API_REFERENCE.md`

---

## 六、连接飞书机器人

### 前提

你需要在[飞书开放平台](https://open.feishu.cn)创建一个应用，获取以下凭证：

| 凭证 | 说明 |
|:-----|:------|
| `FEISHU_APP_ID` | 飞书应用的 App ID |
| `FEISHU_APP_SECRET` | 飞书应用的 App Secret |

### 配置

```bash
export FEISHU_APP_ID=cli_xxxxxxxxxxxx
export FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 启动机器人

```bash
cd nebula
pip install -r requirements.txt
python src/mindflow_map/main.py
```

机器人将在后台运行，通过 Gateway（`:18080`）与 alphaid 通信。

---

## 七、完整架构

```
你
 ├── 终端 → aid (CLI) → DID 身份 / 采集器 / 画像
 ├── 浏览器 → :8000   → Ghost.html / Web API
 ├── 飞书   → 机器人  → Gateway(:18080) → alphaid / nebula
 └── API 调用 → :18080 → Gateway → 各后端服务
```

### 服务端口一览

| 服务 | 端口 | 说明 |
|:-----|:-----|:-----|
| Alpha-ID | 8000 | 身份/记忆/注册 |
| Gateway | 18080 | 统一 API 入口 |
| Nebula | 2002 | 工作流 |
| Flow/API | 3001 | AI 路由 |
| Net-Agent | 18180 | 路由器管理 |
| Orchestrator | 19090 | 任务调度 |

---

## 八、常见问题

| 问题 | 原因 | 解决 |
|:-----|:------|:------|
| `aid: command not found` | 未安装或 PATH 未更新 | `pip install alpha-id-zix` |
| `AUTH_MASTER_KEY 未配置` | 启动 Web 服务前未设置环境变量 | `export AUTH_MASTER_KEY=...` |
| 注册时验证码一直转圈 | alphaid API 未启动 | `cd D:/MW/alphaid/projects && PYTHONPATH=src python -m uvicorn main:app --port 8000` |
| 飞书机器人收不到消息 | Event Subscription 未配置 | 在飞书开放平台 App → 事件订阅 → 添加 `im.message.receive_v1` |
| Gateway 返回 502 | 后端服务未启动 | 检查 alphaid 是否在 :8000 运行 |
| API 返回 429 | 触发限流 | 降低请求频率（默认 5 次/60秒） |
| CORS 错误 | 来源不在白名单 | 设置 `AID_ALLOWED_ORIGINS` 或检查 `ENVIRONMENT` |
