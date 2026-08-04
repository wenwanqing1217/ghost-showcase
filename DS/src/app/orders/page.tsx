'use client';

import { useEffect, useState, useCallback } from 'react';
import StatusBadge from '@/components/StatusBadge';
import Pagination from '@/components/Pagination';
import FulfillModal from '@/components/FulfillModal';
import TopBar from '@/components/layout/TopBar';
import AuthGuard from '@/components/layout/AuthGuard';
import { getApiUrl } from '@/lib/gateway-client';

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

  const fetchOrders = useCallback(async (page: number = 1) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: String(page), limit: '20' });
      if (statusFilter) params.set('status', statusFilter);
      if (search) params.set('search', search);

      const res = await fetch(getApiUrl('/api/orders', params));
      if (res.ok) {
        const data = await res.json();
        setOrders(data.items);
        setPagination(data.pagination);
        setStatusCounts(data.statusCounts || {});
      } else {
        console.error('[OrdersPage] fetch failed:', res.status, res.statusText);
      }
    } catch (err) {
      console.error('[OrdersPage] fetch error:', err);
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
      <div className="flex gap-2 mb-3" style={{ flexWrap: 'wrap' }}>
        <button
          className={`btn btn-sm${statusFilter === '' ? ' btn-primary' : ''}`}
          onClick={() => setStatusFilter('')}
        >
          全部 ({Object.values(statusCounts).reduce((a, b) => a + b, 0)})
        </button>
        {STATUS_OPTIONS.filter(o => o.value).map((opt) => (
          <button
            key={opt.value}
            className={`btn btn-sm${statusFilter === opt.value ? ' btn-primary' : ''}`}
            onClick={() => setStatusFilter(opt.value)}
          >
            {opt.label} ({statusCounts[opt.value] || 0})
          </button>
        ))}
      </div>

      {/* 搜索 */}
      <div className="card mb-3" style={{ padding: '12px 16px' }}>
        <form onSubmit={handleSearch} className="flex gap-2">
          <input
            className="input"
            placeholder="搜索订单号 / 客户名 / 邮箱..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ maxWidth: 320 }}
          />
          <button type="submit" className="btn btn-sm">搜索</button>
        </form>
      </div>

      {/* 订单列表 */}
      <div className="card">
        {loading ? (
          <p style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>加载中...</p>
        ) : orders.length === 0 ? (
          <p style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>暂无订单数据</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>订单号</th>
                  <th>客户</th>
                  <th>商品数</th>
                  <th>金额</th>
                  <th>状态</th>
                  <th>付款时间</th>
                  <th>发货时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((o) => (
                  <tr key={o.id}>
                    <td style={{ fontWeight: 500 }}>{o.orderNo}</td>
                    <td>
                      <div>{o.customerName || '—'}</div>
                      {o.customerEmail && (
                        <div className="text-muted text-sm">{o.customerEmail}</div>
                      )}
                    </td>
                    <td>{o.itemCount}</td>
                    <td style={{ fontWeight: 600 }}>${o.amount.toFixed(2)}</td>
                    <td><StatusBadge status={o.status} /></td>
                    <td className="text-muted text-sm">
                      {o.paidAt ? new Date(o.paidAt).toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'}
                    </td>
                    <td className="text-muted text-sm">
                      {o.fulfilledAt ? new Date(o.fulfilledAt).toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'}
                    </td>
                    <td>
                      {o.status === 'paid' && (
                        <button
                          className="btn btn-sm btn-primary"
                          onClick={() => setFulfillOrder({ id: o.id, orderNo: o.orderNo })}
                        >
                          发货
                        </button>
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
