# MindFlow Map - SLO / 性能基线

## 1. 性能基线

| 指标 | 目标值 | 测量方法 |
|------|--------|----------|
| API p95 延迟 | < 300ms | `GET /`、`GET /health` 等轻量端点 |
| API p99 延迟 | < 800ms | 同上 |
| 健康检查成功率 | 99.9% | `/health/livez`、`/health/readyz` |
| 错误率 | < 0.1% | 5xx 响应占比 |
| 吞吐量 | > 100 RPS | 单副本并发压测 |
| 启动时间 | < 15s | 冷启动到 `/health/livez` 就绪 |

## 2. SLO 定义

| SLO | 目标 | 说明 |
|-----|------|------|
| 可用性 | 99.9% | 月度停机时间 ≤ 43.8 分钟 |
| 延迟 SLO | p95 < 300ms | 超过即触发告警 |
| 错误率 SLO | < 0.1% | 5xx 错误率 |
| 限流触发率 | < 1% | 正常业务不应频繁触发 429 |

## 3. 压测方法

### 本地压测

```bash
# 启动服务
python -m mindflow_map.main

# 另开终端执行压测
python scripts/load_test.py --base-url http://localhost:2002 --users 50 --duration 60 --output load_report.json
```

### CI 中的压测（可选）

在 `.github/workflows/ci.yml` 中增加 job，对 `localhost:2002` 执行短时压测，
并将 `load_report.json` 上传为 artifact 留档。

## 4. 性能分析建议

- 使用 `python -m cProfile` 对热点接口采样
- 数据库慢查询日志 + `EXPLAIN ANALYZE`
- Redis 命中率监控（`keyspace_hits / (keyspace_hits + keyspace_misses)`）
- LLM 调用延迟与熔断状态监控（`llm_request_duration_seconds` 直方图）
