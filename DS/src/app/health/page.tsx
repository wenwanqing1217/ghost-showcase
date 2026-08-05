'use client';

import TopBar from '@/components/layout/TopBar';
import AuthGuard from '@/components/layout/AuthGuard';
import { useCallback, useEffect, useRef, useState } from 'react';

// ── 类型 ──
interface ServiceDetail {
  ok: boolean;
  status: number;
  error?: string;
  duration_ms?: number;
  size_bytes?: number;
  metrics?: string;
}

interface MonitoringData {
  overall: 'ok' | 'degraded';
  services: Record<string, 'ok' | 'error'>;
  details: Record<string, ServiceDetail>;
  timestamp: number;
}

const REFRESH_INTERVAL = 5000;

// 各服务优先展示的运行指标名（Prometheus 文本解析）
const SERVICE_METRIC_PRIORITY: Record<string, string[]> = {
  orchestrator: ['orchestrator_engine_running', 'orchestrator_engine_loops', 'orchestrator_tasks_total'],
  flow: ['flow_up', 'flow_uptime_seconds'],
  netagent: ['netagent_up', 'netagent_uptime_seconds'],
};

// 解析 Prometheus 纯文本 → { metricName: value }
function parseMetrics(text: string | undefined): Record<string, number> {
  const out: Record<string, number> = {};
  if (!text) return out;
  for (const line of text.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const m = trimmed.match(/^([a-zA-Z_:][a-zA-Z0-9_:]*)\{?[^}]*\}?\s+(-?[0-9.e+-]+)/);
    if (m) {
      const v = Number(m[2]);
      if (!Number.isNaN(v)) out[m[1]] = v;
    }
  }
  return out;
}

// 时间格式化
function fmtUptime(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
  if (seconds < 86400) return `${(seconds / 3600).toFixed(1)}h`;
  return `${(seconds / 86400).toFixed(1)}d`;
}

export default function HealthPage() {
  const [data, setData] = useState<MonitoringData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchHealth = useCallback(async () => {
    try {
      const resp = await fetch('/api/internal/monitoring/metrics', { cache: 'no-store' });
      const json = await resp.json().catch(() => ({}));
      if (!resp.ok || !json.success) {
        throw new Error(json.error || json.message || `HTTP ${resp.status}`);
      }
      setData(json.data as MonitoringData);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : '获取服务状态失败');
    } finally {
      setLoading(false);
      setLastRefresh(new Date());
    }
  }, []);

  useEffect(() => {
    fetchHealth();
    if (autoRefresh) {
      timerRef.current = setInterval(fetchHealth, REFRESH_INTERVAL);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [fetchHealth, autoRefresh]);

  const services = data?.details ? Object.entries(data.details) : [];
  const okCount = services.filter(([, d]) => d.ok).length;
  const avgDuration = services.length
    ? services.reduce((acc, [, d]) => acc + (d.duration_ms ?? 0), 0) / services.length
    : 0;
  const allOk = data?.overall === 'ok';

  return (
    <AuthGuard>
      <div className="min-h-screen" style={{ background: 'var(--bg-primary)' }}>
        <TopBar />
        <main className="px-6 py-6 max-w-6xl mx-auto">
          {/* ── 头部 ── */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-xl font-bold text-white tracking-tight">服务健康</h1>
              <p className="text-xs mt-1 font-mono" style={{ color: 'var(--text-muted)' }}>
                全栈 7 服务可观测性 · 实时聚合
              </p>
            </div>
            <div className="flex items-center gap-3">
              {lastRefresh && (
                <span className="text-[11px] font-mono" style={{ color: 'var(--text-muted)' }}>
                  更新于 {lastRefresh.toLocaleTimeString('zh-CN', { hour12: false })}
                </span>
              )}
              <button
                onClick={() => setAutoRefresh((v) => !v)}
                className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
                style={{
                  background: autoRefresh ? 'rgba(139,92,246,0.1)' : 'rgba(255,255,255,0.03)',
                  color: autoRefresh ? 'var(--nebula-light)' : 'var(--text-secondary)',
                  border: '1px solid' + (autoRefresh ? ' rgba(139,92,246,0.25)' : ' var(--border-color)'),
                  cursor: 'pointer',
                }}
              >
                {autoRefresh ? '自动刷新 · 开' : '自动刷新 · 关'}
              </button>
              <button
                onClick={() => {
                  setLoading(true);
                  fetchHealth();
                }}
                className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
                style={{
                  background: 'rgba(255,255,255,0.03)',
                  color: 'var(--text-secondary)',
                  border: '1px solid var(--border-color)',
                  cursor: 'pointer',
                }}
              >
                立即刷新
              </button>
            </div>
          </div>

          {/* ── 总览 Hero ── */}
          <div
            className="rounded-2xl p-6 mb-6 relative overflow-hidden"
            style={{
              background: allOk
                ? 'linear-gradient(135deg, rgba(16,185,129,0.08), rgba(139,92,246,0.05))'
                : 'linear-gradient(135deg, rgba(239,68,68,0.10), rgba(139,92,246,0.05))',
              border: '1px solid ' + (allOk ? 'rgba(16,185,129,0.25)' : 'rgba(239,68,68,0.25)'),
            }}
          >
            {/* 呼吸光斑 */}
            <div
              className="absolute -top-16 -right-16 w-64 h-64 rounded-full"
              style={{
                background: allOk ? 'radial-gradient(circle, rgba(16,185,129,0.15), transparent 70%)' : 'radial-gradient(circle, rgba(239,68,68,0.15), transparent 70%)',
                pointerEvents: 'none',
              }}
            />
            <div className="flex items-center gap-5 relative">
              <div
                className="w-14 h-14 rounded-2xl flex items-center justify-center"
                style={{
                  background: allOk ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)',
                  border: '1px solid ' + (allOk ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'),
                }}
              >
                <span
                  className="w-5 h-5 rounded-full animate-pulse"
                  style={{
                    background: allOk ? 'var(--success)' : 'var(--danger)',
                    boxShadow: '0 0 20px ' + (allOk ? 'rgba(16,185,129,0.6)' : 'rgba(239,68,68,0.6)'),
                  }}
                />
              </div>
              <div className="flex-1">
                <div className="text-2xl font-bold text-white tracking-tight">
                  {loading ? '正在检查…' : allOk ? '全部系统运行正常' : '存在异常服务'}
                </div>
                <div className="text-xs mt-1 font-mono" style={{ color: 'var(--text-muted)' }}>
                  {services.length} 个服务 · {okCount} 在线 · 平均延迟 {avgDuration.toFixed(1)}ms
                </div>
              </div>
              {loading && (
                <div className="text-xs font-mono animate-pulse" style={{ color: 'var(--nebula-light)' }}>
                  聚合中…
                </div>
              )}
            </div>
          </div>

          {/* ── 错误提示 ── */}
          {error && (
            <div
              className="rounded-xl px-4 py-3 mb-6 text-sm"
              style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.25)', color: '#fca5a5' }}
            >
              ⚠ {error}
            </div>
          )}

          {/* ── 服务卡片 ── */}
          {services.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {services.map(([name, detail]) => {
                const metrics = parseMetrics(detail.metrics);
                const uptimeKey = (SERVICE_METRIC_PRIORITY[name] || []).find((k) => k in metrics);
                const uptime = uptimeKey ? metrics[uptimeKey] : null;
                const ok = detail.ok;
                return (
                  <div
                    key={name}
                    className="rounded-xl p-4 transition-all hover:translate-y-[-2px]"
                    style={{
                      background: 'var(--bg-card)',
                      border: '1px solid ' + (ok ? 'var(--border-color)' : 'rgba(239,68,68,0.3)'),
                    }}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2.5">
                        <span
                          className="w-2 h-2 rounded-full"
                          style={{
                            background: ok ? 'var(--success)' : 'var(--danger)',
                            boxShadow: ok ? '0 0 8px rgba(16,185,129,0.5)' : '0 0 8px rgba(239,68,68,0.5)',
                          }}
                        />
                        <span className="text-sm font-semibold text-white font-mono">{name}</span>
                      </div>
                      <span
                        className="text-[10px] px-2 py-0.5 rounded-full font-medium"
                        style={{
                          background: ok ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
                          color: ok ? 'var(--success)' : 'var(--danger)',
                          border: '1px solid ' + (ok ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'),
                        }}
                      >
                        {ok ? 'RUNNING' : 'DOWN'}
                      </span>
                    </div>

                    {ok ? (
                      <div className="grid grid-cols-3 gap-2 text-center">
                        <div className="rounded-lg py-2" style={{ background: 'rgba(255,255,255,0.03)' }}>
                          <div className="text-sm font-bold text-white font-mono">
                            {detail.duration_ms !== undefined ? detail.duration_ms.toFixed(0) + 'ms' : '—'}
                          </div>
                          <div className="text-[10px] mt-0.5" style={{ color: 'var(--text-muted)' }}>延迟</div>
                        </div>
                        <div className="rounded-lg py-2" style={{ background: 'rgba(255,255,255,0.03)' }}>
                          <div className="text-sm font-bold text-white font-mono">
                            {detail.size_bytes !== undefined ? (detail.size_bytes / 1024).toFixed(1) + 'KB' : '—'}
                          </div>
                          <div className="text-[10px] mt-0.5" style={{ color: 'var(--text-muted)' }}>负载</div>
                        </div>
                        <div className="rounded-lg py-2" style={{ background: 'rgba(255,255,255,0.03)' }}>
                          <div className="text-sm font-bold text-white font-mono">
                            {uptime !== null ? fmtUptime(uptime) : '200'}
                          </div>
                          <div className="text-[10px] mt-0.5" style={{ color: 'var(--text-muted)' }}>
                            {uptime !== null ? '运行时长' : 'HTTP 状态'}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div
                        className="rounded-lg px-3 py-2 text-xs font-mono"
                        style={{ background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.15)', color: '#fca5a5', wordBreak: 'break-all' }}
                      >
                        {detail.error || `HTTP ${detail.status || 'timeout'}`}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* ── 原始指标 ── */}
          {services.some(([, d]) => d.ok && d.metrics) && (
            <div className="mt-6">
              <details className="group rounded-xl" style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)' }}>
                <summary
                  className="px-4 py-3 text-sm font-medium cursor-pointer select-none"
                  style={{ color: 'var(--text-secondary)' }}
                >
                  <span className="mr-2 inline-block transition-transform group-open:rotate-90">▸</span>
                  Prometheus 原始指标（截断 5KB/服务）
                </summary>
                <div className="px-4 pb-4 grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {services
                    .filter(([, d]) => d.ok && d.metrics)
                    .map(([name, d]) => (
                      <pre
                        key={name}
                        className="rounded-lg p-3 text-[10px] leading-relaxed overflow-auto max-h-56"
                        style={{ background: 'rgba(0,0,0,0.3)', color: '#9ca3af', border: '1px solid var(--border-color)' }}
                      >
                        <div className="font-bold text-nebula-light mb-2" style={{ color: 'var(--nebula-light)' }}>
                          # {name} · /metrics
                        </div>
                        {d.metrics}
                      </pre>
                    ))}
                </div>
              </details>
            </div>
          )}
        </main>
      </div>
    </AuthGuard>
  );
}
