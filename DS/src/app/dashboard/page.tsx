'use client';

import TopBar from '@/components/layout/TopBar';
import AuthGuard from '@/components/layout/AuthGuard';
import RevenueChart from '@/components/RevenueChart';
import { useEffect, useState } from 'react';
import { getApiUrl } from '@/lib/gateway-client';
import { DEMO_STATS } from '@/lib/demo-data';

interface DashboardStats {
  overview: {
    productCount: number;
    productActiveCount: number;
    orderCount: number;
    totalRevenue: number;
    lowInventoryCount: number;
  };
  orderStatus: { status: string; count: number; amount: number }[];
  dailyRevenue: { date: string; amount: number }[];
}

interface ServiceHealth {
  [key: string]: string;
}

interface MonitoringData {
  overall: string;
  services: ServiceHealth;
  details: Record<string, {
    ok: boolean;
    status: number;
    duration_ms: number;
    size_bytes: number;
    metrics?: string;
    error?: string;
  }>;
}

type Tab = 'business' | 'monitoring';

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [monitoring, setMonitoring] = useState<MonitoringData | null>(null);
  const [loading, setLoading] = useState(true);
  const [monitoringLoading, setMonitoringLoading] = useState(true);
  const [tab, setTab] = useState<Tab>('business');
  const [isDemo, setIsDemo] = useState(false);

  useEffect(() => {
    if (tab === 'business') {
      fetch(getApiUrl('/api/stats'))
        .then((r) => r.json())
        .then((data) => { setStats(data); setIsDemo(false); setLoading(false); })
        .catch(() => {
          // API 失败 → 使用演示数据
          setStats({
            overview: {
              productCount: DEMO_STATS.totalProducts,
              productActiveCount: DEMO_STATS.activeProducts,
              orderCount: DEMO_STATS.totalOrders,
              totalRevenue: DEMO_STATS.totalRevenue,
              lowInventoryCount: 1,
            },
            orderStatus: [
              { status: 'pending', count: 1, amount: 29.99 },
              { status: 'processing', count: 1, amount: 149.98 },
              { status: 'shipped', count: 1, amount: 49.99 },
              { status: 'delivered', count: 1, amount: 99.99 },
              { status: 'cancelled', count: 1, amount: 0 },
            ],
            dailyRevenue: [
              { date: '2026-07-29', amount: 45.99 },
              { date: '2026-07-30', amount: 128.50 },
              { date: '2026-07-31', amount: 329.96 },
              { date: '2026-08-01', amount: 89.00 },
              { date: '2026-08-02', amount: 198.75 },
              { date: '2026-08-03', amount: 249.99 },
              { date: '2026-08-04', amount: 199.97 },
            ],
          });
          setIsDemo(true);
          setLoading(false);
        });
    } else {
      fetch('/api/internal/monitoring/metrics')
        .then((r) => r.json())
        .then((d) => {
          if (d.success && d.data) setMonitoring(d.data);
          setMonitoringLoading(false);
        })
        .catch(() => setMonitoringLoading(false));
    }
  }, [tab]);

  const serviceNames: Record<string, string> = {
    gateway: 'Gateway', alphaid: 'Alpha-ID', nebula: 'Nebula',
    flow: 'Flow', orchestrator: 'Orchestrator', netagent: 'Net-Agent',
    'ghost-ds': 'Ghost DS', obsidian: 'Obsidian',
  };

  return (
    <AuthGuard>
      <TopBar title="运营看板" subtitle="Ghost Platform 统一监控" />

      {/* Tab 切换 */}
      <div style={{ padding: '16px 24px 0' }}>
        <div className="flex gap-2">
          {[
            { key: 'business' as Tab, label: '📈 业务数据' },
            { key: 'monitoring' as Tab, label: '📊 基础设施监控' },
          ].map((t) => (
            <button
              key={t.key}
              onClick={() => { setTab(t.key); setLoading(true); setMonitoringLoading(true); }}
              className={`btn btn-sm${tab === t.key ? ' btn-primary' : ' secondary'}`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <div className="p-6">
        {/* 演示模式横幅 */}
        {isDemo && tab === 'business' && (
          <div className="p-3 rounded-xl mb-4 animate-slide-up" style={{
            background: 'rgba(245,158,11,0.08)',
            border: '1px solid rgba(245,158,11,0.15)',
            color: '#fbbf24',
            fontSize: 13,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}>
            <span style={{
              width: 6, height: 6,
              borderRadius: '50%',
              background: '#fbbf24',
              opacity: 0.7,
            }} />
            ⚠ 演示模式 — 未连接到数据源，显示示例运营数据
          </div>
        )}
        {tab === 'business' ? (
          /* ── 业务数据 ── */
          loading ? (
            <div style={{ textAlign: 'center', padding: 60 }}>
              <div style={{ fontSize: 28, marginBottom: 16, opacity: 0.4 }}>📊</div>
              <p className="text-muted">加载运营数据...</p>
            </div>
          ) : !stats ? (
            <div className="card" style={{ padding: 60, textAlign: 'center' }}>
              <div style={{ fontSize: 40, marginBottom: 16, opacity: 0.3 }}>📭</div>
              <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>暂无数据，请先连接店铺并同步数据</p>
            </div>
          ) : (
            <div className="max-w-6xl mx-auto">
              {/* 概览卡片 */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
                {[
                  { label: '商品总数', value: stats.overview.productCount, color: 'var(--nebula)' },
                  { label: '在售商品', value: stats.overview.productActiveCount, color: 'var(--success)' },
                  { label: '订单总数', value: stats.overview.orderCount, color: 'var(--cosmic)' },
                  { label: '总收入', value: `$${stats.overview.totalRevenue.toFixed(2)}`, color: '#a78bfa' },
                  { label: '低库存', value: stats.overview.lowInventoryCount, color: 'var(--warning)' },
                ].map((item, i) => (
                  <div key={i} className="card" style={{ padding: 16, textAlign: 'center' }}>
                    <div style={{ fontSize: 24, fontWeight: 800, color: item.color, marginBottom: 4 }}>
                      {item.value}
                    </div>
                    <div className="text-muted" style={{ fontSize: 11 }}>{item.label}</div>
                  </div>
                ))}
              </div>

              {/* 收入趋势 */}
              <div className="card mb-6">
                <div className="card-header">
                  <span className="card-title">近 7 日收入趋势</span>
                </div>
                <div style={{ padding: '16px' }}>
                  <RevenueChart data={stats.dailyRevenue} />
                </div>
              </div>

              {/* 订单状态分布 */}
              <div className="card">
                <div className="card-header">
                  <span className="card-title">订单状态分布</span>
                </div>
                <div style={{ padding: 16 }}>
                  {stats.orderStatus.length === 0 ? (
                    <p className="text-muted" style={{ textAlign: 'center', padding: 20 }}>暂无订单数据</p>
                  ) : (
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                      {stats.orderStatus.map((s) => (
                        <div key={s.status} style={{ textAlign: 'center', padding: 12, background: 'var(--bg-hover)', borderRadius: 8 }}>
                          <div style={{ fontSize: 20, fontWeight: 700 }}>{s.count}</div>
                          <div className="text-muted" style={{ fontSize: 11 }}>{s.status}</div>
                          <div style={{ fontSize: 12, color: 'var(--nebula-300)' }}>${s.amount.toFixed(2)}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )
        ) : (
          /* ── 基础设施监控 ── */
          monitoringLoading ? (
            <div style={{ textAlign: 'center', padding: 60 }}>
              <div style={{ fontSize: 28, marginBottom: 16, opacity: 0.4 }}>🔧</div>
              <p className="text-muted">加载监控数据...</p>
            </div>
          ) : !monitoring ? (
            <div className="card" style={{ padding: 60, textAlign: 'center' }}>
              <div style={{ fontSize: 40, marginBottom: 16, opacity: 0.3 }}>⚠️</div>
              <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>无法获取监控数据，请检查 Gateway 连接</p>
            </div>
          ) : (
            <div className="max-w-6xl mx-auto">
              {/* 服务健康 */}
              <div className="card mb-4">
                <h3 style={{ fontSize: 12, color: '#94a3b8', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.3px' }}>
                  服务健康 — 整体: {monitoring.overall === 'ok' ? '✅ 正常' : '⚠️ 部分异常'}
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {Object.entries(monitoring.services).map(([svc, status]) => (
                    <div key={svc} className="service-item" style={{ textAlign: 'center', padding: 12, background: 'var(--bg-hover)', borderRadius: 8 }}>
                      <div style={{ fontSize: 11, color: '#64748b', marginBottom: 4 }}>{serviceNames[svc] || svc}</div>
                      <div style={{ fontSize: 13, fontWeight: 500, color: status === 'ok' ? 'var(--success)' : status === 'not_found' ? '#eab308' : 'var(--danger)' }}>
                        {status === 'ok' ? '正常' : status === 'not_found' ? '未配置' : '异常'}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* 各服务指标详情 */}
              <div className="card">
                <h3 style={{ fontSize: 12, color: '#94a3b8', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.3px' }}>
                  服务指标详情
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {Object.entries(monitoring.details).map(([svc, info]) => (
                    <div key={svc} style={{ background: 'rgba(15,23,42,0.6)', borderRadius: 8, padding: 12, border: '1px solid rgba(148,163,184,0.06)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                        <span style={{ fontWeight: 600, fontSize: 13 }}>{serviceNames[svc] || svc}</span>
                        <div style={{ display: 'flex', gap: 12, fontSize: 11, color: '#64748b' }}>
                          <span style={{ color: info.ok ? '#22c55e' : '#ef4444' }}>{info.ok ? '✓ 正常' : '✗ 异常'}</span>
                          <span>HTTP {info.status}</span>
                          <span>{info.duration_ms}ms</span>
                          {info.size_bytes && <span>{info.size_bytes}B</span>}
                        </div>
                      </div>
                      {info.metrics && (
                        <pre style={{
                          fontFamily: "'Courier New',monospace", fontSize: 10, color: '#7dd3fc',
                          background: 'rgba(10,14,26,0.6)', padding: 10, borderRadius: 6,
                          maxHeight: 200, overflowY: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-all',
                          marginTop: 6,
                        }}>
                          {info.metrics}
                        </pre>
                      )}
                      {info.error && (
                        <div style={{ fontSize: 11, color: '#ef4444', marginTop: 4 }}>错误: {info.error}</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )
        )}
      </div>
    </AuthGuard>
  );
}
