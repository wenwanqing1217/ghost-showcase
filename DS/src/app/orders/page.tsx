'use client';

import { useEffect, useState, useCallback } from 'react';
import StatusBadge from '@/components/StatusBadge';
import Pagination from '@/components/Pagination';
import FulfillModal from '@/components/FulfillModal';
import TopBar from '@/components/layout/TopBar';
import AuthGuard from '@/components/layout/AuthGuard';
import { getApiUrl } from '@/lib/gateway-client';
import { DEMO_ORDERS } from '@/lib/demo-data';

interface Order {
  id: string;
  externalId: string;
  orderNo: string;
  amount: number;
  currency: string;
  status: string;
  customerName: string | null;
  customerEmail: string | null;
  itemCount: number;
  paidAt: string | null;
  fulfilledAt: string | null;
  createdAt: string;
}

interface PaginationInfo {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

const STATUS_OPTIONS = [
  { value: '', label: '全部状态' },
  { value: 'pending', label: '待付款' },
  { value: 'paid', label: '已付款' },
  { value: 'fulfilled', label: '已发货' },
  { value: 'refunded', label: '已退款' },
  { value: 'cancelled', label: '已取消' },
];

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [pagination, setPagination] = useState<PaginationInfo>({ page: 1, limit: 20, total: 0, totalPages: 0 });
  const [statusCounts, setStatusCounts] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [fulfillOrder, setFulfillOrder] = useState<{ id: string; orderNo: string } | null>(null);
  const [isDemo, setIsDemo] = useState(false);

  const fetchOrders = useCallback(async (page: number = 1) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: String(page), limit: '20' });
      if (statusFilter) params.set('status', statusFilter);
      if (search) params.set('search', search);

      const res = await fetch(getApiUrl('/api/orders', params));
      if (res.ok) {
        const data = await res.json();
        if (data.items && data.items.length > 0) {
          setOrders(data.items);
          setPagination(data.pagination);
          setStatusCounts(data.statusCounts || {});
          setIsDemo(false);
        } else {
          // API 返回空数据 → 使用演示数据
          setIsDemo(true);
          setOrders(DEMO_ORDERS.map(o => ({ ...o, fulfilledAt: null, paidAt: o.status === 'paid' ? new Date(o.createdAt).toISOString() : null })) as Order[]);
          setPagination({ page: 1, limit: 20, total: DEMO_ORDERS.length, totalPages: 1 });
          setStatusCounts({ pending: 1, processing: 1, shipped: 1, delivered: 1, cancelled: 1 });
        }
      } else {
        console.error('[OrdersPage] fetch failed:', res.status, res.statusText);
        setIsDemo(true);
        setOrders(DEMO_ORDERS.map(o => ({ ...o, fulfilledAt: null, paidAt: o.status === 'paid' ? new Date(o.createdAt).toISOString() : null })) as Order[]);
        setPagination({ page: 1, limit: 20, total: DEMO_ORDERS.length, totalPages: 1 });
        setStatusCounts({ pending: 1, processing: 1, shipped: 1, delivered: 1, cancelled: 1 });
      }
    } catch (err) {
      console.error('[OrdersPage] fetch error:', err);
      setIsDemo(true);
      setOrders(DEMO_ORDERS.map(o => ({ ...o, fulfilledAt: null, paidAt: o.status === 'paid' ? new Date(o.createdAt).toISOString() : null })) as Order[]);
      setPagination({ page: 1, limit: 20, total: DEMO_ORDERS.length, totalPages: 1 });
      setStatusCounts({ pending: 1, processing: 1, shipped: 1, delivered: 1, cancelled: 1 });
    } finally {
      setLoading(false);
    }
  }, [statusFilter, search]);

  useEffect(() => {
    fetchOrders(1);
  }, [fetchOrders]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchOrders(1);
  };

  const handleSync = async () => {
    setSyncing(true);
    setSyncMsg(null);
    try {
      const res = await fetch(getApiUrl('/api/sync'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ entity: 'orders' }),
      });
      const data = await res.json();
      if (data.ok) {
        setSyncMsg(`同步完成 · ${data.results?.orders?.count || 0} 笔订单`);
        fetchOrders(1);
      } else {
        setSyncMsg(data.error || '同步失败');
      }
    } catch {
      setSyncMsg('同步请求失败');
    } finally {
      setSyncing(false);
      setTimeout(() => setSyncMsg(null), 4000);
    }
  };

  const totalAmount = orders.reduce((sum, o) => sum + o.amount, 0);

  return (
    <AuthGuard>
      <TopBar title="订单管理" subtitle="OneBound 订单同步与履约" />
      <div className="p-6">
      <div className="max-w-6xl mx-auto">
        {/* 演示模式横幅 */}
        {isDemo && (
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
            ⚠ 演示模式 — 未连接到订单系统，显示示例订单数据
          </div>
        )}
        <div className="flex-between mb-3">
        <h2 style={{ fontSize: 20, fontWeight: 700 }}>订单管理</h2>
        <div className="flex-between" style={{ gap: 12 }}>
          <span className="text-muted text-sm">
            共 {pagination.total} 笔订单
          </span>
          <button
            onClick={handleSync}
            disabled={syncing}
            className="btn btn-sm"
            style={{ fontSize: 12 }}
          >
            {syncing ? '⟳ 同步中...' : '⟳ 同步'}
          </button>
        </div>
      </div>

      {syncMsg && (
        <div style={{
          padding: '8px 12px',
          marginBottom: 12,
          borderRadius: 8,
          background: syncMsg.includes('失败')
            ? 'rgba(239,68,68,0.08)'
            : 'rgba(16,185,129,0.08)',
          color: syncMsg.includes('失败') ? 'var(--danger)' : 'var(--success)',
          fontSize: 12,
          border: `1px solid ${syncMsg.includes('失败') ? 'rgba(239,68,68,0.12)' : 'rgba(16,185,129,0.12)'}`,
        }}>
          {syncMsg}
        </div>
      )}

      {/* 状态筛选标签 */}
      <div className="flex gap-2 mb-4" style={{ flexWrap: 'wrap' }}>
        {STATUS_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            className={`btn btn-sm${statusFilter === opt.value ? ' btn-primary' : ''}`}
            onClick={() => setStatusFilter(opt.value)}
          >
            {opt.label} {opt.value && <span style={{ opacity: 0.6, marginLeft: 2 }}>({statusCounts[opt.value] || 0})</span>}
          </button>
        ))}
      </div>

      {/* 搜索 */}
      <div className="card mb-4" style={{ padding: '14px 18px' }}>
        <form onSubmit={handleSearch} className="flex gap-2">
          <div style={{ position: 'relative', flex: '1 1 240px' }}>
            <span style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', fontSize: 14 }}>🔍</span>
            <input
              className="input"
              placeholder="搜索订单号 / 客户名 / 邮箱..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ paddingLeft: 36, maxWidth: 340, width: '100%' }}
            />
          </div>
          <button type="submit" className="btn btn-sm">搜索</button>
        </form>
      </div>

      {/* 订单列表 */}
      <div className="card" style={{ overflow: 'hidden', padding: 0 }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: 60 }}>
            <div style={{ fontSize: 24, marginBottom: 12, opacity: 0.4 }}>📋</div>
            <p className="text-muted">加载订单数据...</p>
          </div>
        ) : orders.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 60 }}>
            <div style={{ fontSize: 40, marginBottom: 12, opacity: 0.3 }}>📭</div>
            <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>暂无订单数据</p>
            <p className="text-xs text-muted" style={{ marginTop: 4 }}>连接 OneBound 货源后同步订单</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <th style={{ padding: '14px 18px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>订单号</th>
                  <th style={{ padding: '14px 18px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>客户</th>
                  <th style={{ padding: '14px 18px', textAlign: 'center', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>商品数</th>
                  <th style={{ padding: '14px 18px', textAlign: 'right', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>金额</th>
                  <th style={{ padding: '14px 18px', textAlign: 'center', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>状态</th>
                  <th style={{ padding: '14px 18px', textAlign: 'right', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>付款时间</th>
                  <th style={{ padding: '14px 18px', textAlign: 'right', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>发货时间</th>
                  <th style={{ padding: '14px 18px', textAlign: 'center', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>操作</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((o) => (
                  <tr key={o.id} style={{ borderBottom: '1px solid rgba(148,163,184,0.06)', transition: 'background 0.15s ease' }}
                    onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(139,92,246,0.03)'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
                  >
                    <td style={{ padding: '14px 18px' }}>
                      <span style={{ fontWeight: 500, fontSize: 13, fontFamily: "'JetBrains Mono', monospace", color: 'var(--text-primary)' }}>{o.orderNo}</span>
                    </td>
                    <td style={{ padding: '14px 18px' }}>
                      <div style={{ fontSize: 13, color: 'var(--text-primary)' }}>{o.customerName || '—'}</div>
                      {o.customerEmail && (
                        <div className="text-muted" style={{ fontSize: 11 }}>{o.customerEmail}</div>
                      )}
                    </td>
                    <td style={{ padding: '14px 18px', textAlign: 'center' }}>
                      <span style={{ fontSize: 13, color: 'var(--text-primary)' }}>{o.itemCount}</span>
                    </td>
                    <td style={{ padding: '14px 18px', textAlign: 'right' }}>
                      <span style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-primary)' }}>${o.amount.toFixed(2)}</span>
                    </td>
                    <td style={{ padding: '14px 18px', textAlign: 'center' }}><StatusBadge status={o.status} /></td>
                    <td style={{ padding: '14px 18px', textAlign: 'right' }}>
                      <span className="text-muted" style={{ fontSize: 12 }}>
                        {o.paidAt ? new Date(o.paidAt).toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'}
                      </span>
                    </td>
                    <td style={{ padding: '14px 18px', textAlign: 'right' }}>
                      <span className="text-muted" style={{ fontSize: 12 }}>
                        {o.fulfilledAt ? new Date(o.fulfilledAt).toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'}
                      </span>
                    </td>
                    <td style={{ padding: '14px 18px', textAlign: 'center' }}>
                      {o.status === 'paid' && (
                        <button
                          className="btn btn-sm btn-primary"
                          onClick={() => setFulfillOrder({ id: o.id, orderNo: o.orderNo })}
                          style={{ fontSize: 11, padding: '4px 14px' }}
                        >
                          发货
                        </button>
                      )}
                      {o.status === 'fulfilled' && (
                        <span className="text-xs" style={{ color: 'var(--success)' }}>✓ 已发货</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <Pagination
          page={pagination.page}
          totalPages={pagination.totalPages}
          onPageChange={(page) => fetchOrders(page)}
        />
      </div>

      {/* 发货弹窗 */}
      {fulfillOrder && (
        <FulfillModal
          orderId={fulfillOrder.id}
          orderNo={fulfillOrder.orderNo}
          onClose={() => setFulfillOrder(null)}
          onSuccess={() => {
            setFulfillOrder(null);
            fetchOrders(pagination.page);
          }}
        />
      )}
      </div>
    </div>
    </AuthGuard>
  );
}
