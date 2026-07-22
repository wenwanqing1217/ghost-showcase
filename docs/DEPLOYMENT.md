# 生产部署指南

## 架构

```
Internet
    │
    ▼
┌─────────────────────────────────────────┐
│  Caddy (:80, :443)                      │
│  ┌─────────┬──────────┬───────────────┐ │
│  │ /api/map│ /ds/*    │ /api/aid/*    │ │
│  │ /workspace│         │               │ │
│  └────┬─────┴────┬─────┴──────┬────────┘ │
└───────┼──────────┼────────────┼──────────┘
        │          │            │
   ┌────▼────┐ ┌──▼───┐  ┌────▼────┐
   │mindflow │ │  DS  │  │   AID   │
   │-map:2002│ │:3000 │  │ :8000   │
   └────┬────┘ └──┬───┘  └────┬────┘
        │         │           │
   ┌────▼─────────▼───────────▼────┐
   │      PostgreSQL 16 (:5432)    │
   │  mindflow_map │ ds │ alpha_id │
   └──────────────────────────────┘
```

## 前置条件

- Docker Engine 24+
- Docker Compose v2
- 一个公网 IP（生产 TLS 需要）
- 域名（可选，自签名证书也可用）

## 快速部署

### 1. 准备生产环境变量

```bash
# 复制模板
cp .env.production.example .env.production

# 编辑（必须修改标记为 CHANGE_ME 的值）
# - DB_PASSWORD（至少 32 字符）
# - DS_API_KEY（服务间认证密钥）
# - DASH_PASS（Dashboard 登录密码）
# - AID_AUTH_MASTER_KEY（AID 加密主密钥）
```

### 2. 生成强密钥

```bash
# Linux/Mac
openssl rand -hex 24    # API Key
openssl rand -hex 32    # DB Password
openssl rand -hex 64    # Auth Master Key

# Windows PowerShell
[Convert]::ToByteString((1..24 | ForEach-Object { Get-Random -Max 256 }))  # 24 bytes hex
# 或直接用 Python
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. 启动生产服务

```bash
# 构建 + 启动
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build

# 查看日志
docker compose -f docker-compose.prod.yml logs -f

# 检查健康状态
docker compose -f docker-compose.prod.yml ps
```

### 4. 验证

```bash
# 统一入口（Caddy）
curl http://localhost/api/map/health
curl http://localhost/ds/api/health
curl http://localhost/api/aid/health

# 直连各服务（仅内部网络）
docker exec ghost-mindflow-map python -c "import urllib.request; urllib.request.urlopen('http://localhost:2002/health/livez')"
```

## 生产 TLS（有域名）

1. 编辑 `Caddyfile`，取消注释生产域名块
2. 修改域名为你的实际域名
3. 确保 DNS 指向你的服务器 IP
4. 开放 80/443 端口
5. 重启 Caddy：`docker compose -f docker-compose.prod.yml restart caddy`

```caddyfile
map.example.com {
    encode gzip
    reverse_proxy mindflow-map:2002
}

ds.example.com {
    encode gzip
    reverse_proxy ds:3000
}

aid.example.com {
    encode gzip
    reverse_proxy aid:8000
}
```

## 常用操作

### 更新服务
```bash
# 拉取最新代码
git pull --recurse-submodules

# 重建并重启
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

### 备份数据库
```bash
# 全部备份
docker exec ghost-db pg_dumpall -U ghost > backup_$(date +%Y%m%d).sql

# 单库备份
docker exec ghost-db pg_dump -U ghost mindflow_map > mindflow_map_backup.sql

# 恢复
docker exec -i ghost-db psql -U ghost < backup.sql
```

### 查看日志
```bash
docker compose -f docker-compose.prod.yml logs -f caddy
docker compose -f docker-compose.prod.yml logs -f mindflow-map
docker compose -f docker-compose.prod.yml logs -f ds
docker compose -f docker-compose.prod.yml logs -f aid
```

### 资源监控
```bash
docker stats ghost-db ghost-mindflow-map ghost-ds ghost-aid ghost-caddy
```

## 故障排查

| 问题 | 排查命令 |
|------|---------|
| 服务未启动 | `docker compose -f docker-compose.prod.yml ps` |
| 数据库连接失败 | `docker exec ghost-db pg_isready -U ghost` |
| 查看错误日志 | `docker compose -f docker-compose.prod.yml logs --tail=100 <service>` |
| 网络问题 | `docker network inspect ghost_default` |
| 端口冲突 | `netstat -tlnp \| grep -E '80\|443\|2002\|3000\|8000\|5432'` |

## 安全清单

- [ ] `.env.production` 已配置且未提交到 Git
- [ ] DB_PASSWORD ≥ 32 字符
- [ ] DS_API_KEY 已生成且一致
- [ ] AID_AUTH_MASTER_KEY 已生成
- [ ] DASH_PASS 已修改（非默认值）
- [ ] 生产环境开放端口仅限 80/443
- [ ] 内部服务端口（2002/3000/8000/5432）不对外暴露
- [ ] Caddy 安全头已启用
- [ ] 数据库定期备份已配置
