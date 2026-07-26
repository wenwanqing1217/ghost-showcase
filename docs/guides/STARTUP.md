# Ghost 项目启动指南

> 最后更新: 2026-07-26

## 前置要求

- Python ≥ 3.12
- Node.js ≥ 18
- 支付宝密钥文件置于 `D:/MW/`（如有）

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

**功能：** 统一入口，代理到 alphaid 所有后端服务（身份/记忆/注册/聊天）

**验证：** `curl http://localhost:18080/health`

### 3. Flow/API（AI 路由 + Computer Use，:3001，可选）

```bash
cd D:/MW/flow/apps/api
npm install         # 首次运行需要
npx tsx src/index.ts
```

**功能：** AI 多 Provider 路由、Computer Use 浏览器自动化（注册功能已迁移到 alphaid）

**验证：** `curl http://localhost:3001/api/health`

## 环境变量

所有配置统一在 `D:/MW/.env` 中管理。

主要变量：

| 变量 | 说明 |
|:-----|:------|
| `AUTH_MASTER_KEY` | JWT 签名密钥（生产环境必须修改） |
| `OPENAI_API_KEY` | DeepSeek API Key（Agent 使用） |
| `FOUNDER_CODE_HASH` | 创始人注册码 SHA256 |
| `ALIBABA_ACCESS_KEY_ID/SECRET` | 阿里云短信 |
| `ALIPAY_APP_ID` | 支付宝应用 ID |
| `ALIPAY_PRIVATE_KEY_PATH` | 支付宝应用私钥路径 |
| `ALIPAY_PUBLIC_KEY_PATH` | 支付宝公钥路径 |

## 浏览器访问

- Ghost 官网: `http://localhost:8000/`
- 注册流程: 点击页面「注册」按钮，SMS → 支付宝人脸 → DID 生成

## 测试

```bash
cd D:/MW/alphaid/projects
PYTHONPATH=src python -m pytest tests/test_registration.py -v --noconftest
```

## 常见问题

| 问题 | 原因 | 解决 |
|:-----|:------|:------|
| 注册返回 404 | `registration.py` 未加载 | 重启 alphaid API |
| Gateway 返回 502 | 后端服务未启动 | 检查 alphaid 是否在 :8000 运行 |
| 支付宝人脸一直演示模式 | 密钥文件缺失或 `ALIPAY_DEMO_MODE=true` | 确认 `D:/MW/alipay_private_pkcs1.pem` 存在 |
| 短信一直演示模式 | 阿里云账户余额不足或模板未过审 | 登录阿里云控制台充值/审核 |
| `ModuleNotFoundError` | Python 路径未设置 | 运行时加 `PYTHONPATH=src` |
