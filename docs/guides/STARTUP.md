# Ghost 项目启动指南

> 最后更新: 2026-07-27

## 前置要求

- Python ≥ 3.12
- Node.js ≥ 18
- 支付宝密钥文件置于 `D:/MW/`（如有）

---

## 快速启动（3 个服务）

### 1. Alpha-ID API（核心服务，:8000）

```bash
cd D:/MW/alphaid/projects
PYTHONPATH=src python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

**功能：** 身份注册、双链记忆、Ghost.html 前端、注册流程（SMS + 支付宝人脸 + DID 生成）

**验证：** `curl http://localhost:8000/health`

### 2. Gateway 网关（统一入口，:18080）

```bash
cd D:/MW/ghost-main/gateway
python app.py
```

**功能：** 四层路由（/agent/net/internal/human），代理到所有后端，限流，关联 ID 追踪

**验证：** `curl http://localhost:18080/health`

**启动输出示例：**
```
╔══════════════════════════════════════════════════╗
║           Ghost Gateway v2.0.0                   ║
║   Unified API Gateway                            ║
╠══════════════════════════════════════════════════╣
║   Port:     18080                                ║
║   Alpha-ID: http://localhost:8000                ║
║   Nebula:   http://localhost:2002                ║
║   Flow:     http://localhost:3001                ║
║   NetAgent: http://localhost:18180               ║
╚══════════════════════════════════════════════════╝
```

### 3. Flow/API（AI 路由 + Computer Use，:3001，可选）

```bash
cd D:/MW/flow/apps/api
npm install         # 首次运行需要
npx tsx src/index.ts
```

**功能：** AI 多 Provider 路由、Computer Use 浏览器自动化（注册功能已迁移到 alphaid）

**验证：** `curl http://localhost:3001/api/health`

---

## Gateway 配置

Gateway 所有配置通过环境变量（`.env`）控制：

| 变量 | 默认值 | 说明 |
|:-----|:-------|:-----|
| `ALPHAID_URL` | `http://localhost:8000` | Alpha-ID 后端地址 |
| `NEBULA_URL` | `http://localhost:2002` | Nebula 工作流地址 |
| `ORCHESTRATOR_URL` | `http://localhost:19090` | 编排器地址 |
| `FLOW_URL` | `http://localhost:3001` | Flow/API 地址 |
| `NETAGENT_URL` | `http://localhost:18180` | Net-Agent 地址 |
| `DEFAULT_ALPHA_ID` | `` | 默认 Alpha-ID |
| `GATEWAY_PORT` | `18080` | Gateway 监听端口 |
| `ENVIRONMENT` | `development` | 环境：`development` 或 `production` |
| `RATE_LIMIT_MAX` | `5` | 默认限流次数 |
| `RATE_LIMIT_WINDOW` | `60` | 限流窗口（秒） |
| `AID_ALLOWED_ORIGINS` | `` | CORS 白名单（逗号分隔，`*` 仅开发环境） |
| `OBSIDIAN_VAULT` | `D:\Obsidian\Ghost知识库` | Obsidian vault 路径 |

### CORS 策略

- 默认：仅允许 `http://localhost:3000/3001/18080/8000`
- 生产环境：`AID_ALLOWED_ORIGINS=*` 会被拦截，回退到 localhost
- 开发环境：`AID_ALLOWED_ORIGINS=*` 允许

---

## Gateway 测试

```bash
cd D:/MW/ghost-main/gateway
python -m pytest tests/ -v
```

**当前测试覆盖（13 个）：**

| 文件 | 测试数 | 覆盖内容 |
|:-----|:-------|:--------|
| `test_health.py` | 6 | 健康检查、后端宕机关联、请求 ID 传播 |
| `test_rate_limit.py` | 7 | 聊天限流、短信限流、参数校验、代理转发 |

**运行结果示例：**
```
tests/test_health.py::test_health_all_backends_healthy PASSED
tests/test_health.py::test_health_alphaid_down_returns_503 PASSED
tests/test_health.py::test_health_netagent_down_returns_error PASSED
tests/test_health.py::test_health_all_down_returns_errors PASSED
tests/test_health.py::test_health_includes_request_id PASSED
tests/test_health.py::test_health_uses_provided_request_id PASSED
tests/test_rate_limit.py::test_chat_rate_limit_blocks_after_10 PASSED
tests/test_rate_limit.py::test_chat_missing_message_returns_400 PASSED
tests/test_rate_limit.py::test_intent_parse_missing_text_returns_400 PASSED
tests/test_rate_limit.py::test_identity_proxy PASSED
tests/test_rate_limit.py::test_dashboard_returns_aggregated_data PASSED
tests/test_rate_limit.py::test_register_sms_rate_limit PASSED
tests/test_rate_limit.py::test_response_includes_request_id PASSED

13 passed in 0.56s
```

---

## 浏览器访问

- Ghost 官网: `http://localhost:8000/`
- 注册流程: 点击页面「注册」按钮，SMS → 支付宝人脸 → DID 生成
- API 文档: `http://localhost:18080/docs`（Swagger UI）
- ReDoc: `http://localhost:18080/redoc`

---

## 完整环境变量参考

所有配置统一在 `D:/MW/.env` 中管理。

| 变量 | 说明 |
|:-----|:------|
| `AUTH_MASTER_KEY` | JWT 签名密钥（生产环境必须修改） |
| `OPENAI_API_KEY` | DeepSeek API Key（Agent 使用） |
| `FOUNDER_CODE_HASH` | 创始人注册码 SHA256 |
| `ALIBABA_ACCESS_KEY_ID/SECRET` | 阿里云短信 |
| `ALIPAY_APP_ID` | 支付宝应用 ID |
| `ALIPAY_PRIVATE_KEY_PATH` | 支付宝应用私钥路径 |
| `ALIPAY_PUBLIC_KEY_PATH` | 支付宝公钥路径 |
| `ALPHAID_URL` | Alpha-ID 后端地址 |
| `NEBULA_URL` | Nebula 地址 |
| `NETAGENT_URL` | Net-Agent 地址 |
| `ORCHESTRATOR_URL` | 编排器地址 |
| `GATEWAY_PORT` | Gateway 端口 |
| `OBSIDIAN_VAULT` | Obsidian vault 路径 |

---

## 常见问题

| 问题 | 原因 | 解决 |
|:-----|:------|:------|
| 注册返回 404 | `registration.py` 未加载 | 重启 alphaid API |
| Gateway 返回 502 | 后端服务未启动 | 检查 alphaid 是否在 :8000 运行 |
| 支付宝人脸一直演示模式 | 密钥文件缺失或 `ALIPAY_DEMO_MODE=true` | 确认 `D:/MW/alipay_private_pkcs1.pem` 存在 |
| 短信一直演示模式 | 阿里云账户余额不足或模板未过审 | 登录阿里云控制台充值/审核 |
| `ModuleNotFoundError` | Python 路径未设置 | 运行时加 `PYTHONPATH=src` |
| `ModuleNotFoundError: doubao_reader` | 缺少父目录到 sys.path | 已修复：app.py 自动添加 |
| 测试失败 `assert 502 == 200` | mock 绑定问题 | 已修复：conftest 同时 patch services.proxy 和 app |
| CORS 错误 | 来源不在白名单 | 设置 `AID_ALLOWED_ORIGINS` 或检查 `ENVIRONMENT` |
