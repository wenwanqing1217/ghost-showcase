# Secrets Management

## 本地开发

默认读取 `.env` 文件。`.env` 已加入 `.gitignore`，禁止提交到版本库。

## Kubernetes

```bash
export SECRET_PROVIDER=kubernetes
export K8S_SECRET_NAME=mindflow-map-secrets

kubectl create secret generic mindflow-map-secrets \
  --from-literal=FEISHU_APP_ID=cli_xxx \
  --from-literal=FEISHU_APP_SECRET=xxx \
  -n mindflow
```

## HashiCorp Vault

```bash
export SECRET_PROVIDER=vault
export VAULT_URL=https://vault.example.com
export VAULT_TOKEN=hvs.xxx
export VAULT_PATH_PREFIX=secret/mindflow-map
```

## 轮换策略

- API Key：每 90 天轮换
- 告警：轮换前 7 天提醒
- 紧急轮换：立即吊销旧 key，更新 secret store，滚动重启

## 扫描

```bash
python scripts/scan_secrets.py
```
