# Monitoring

Grafana + Prometheus 监控栈。

| 服务 | 端口 | 说明 |
|:-----|:-----|:-----|
| Prometheus | 9090 | 指标采集 |
| Grafana | 3005 | 仪表盘 |

## 启动

```bash
docker compose up prometheus grafana
```

## 数据源

- 各服务 `/metrics` 端点
- PostgreSQL exporter
- Redis exporter
