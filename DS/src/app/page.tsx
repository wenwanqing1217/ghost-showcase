'use client';

import { useEffect, useState, useCallback } from 'react';
import RevenueChart from '@/components/RevenueChart';

interface DailyRevenue {
  date: string;
  amount: number;
}

interface Overview {
  productCount: number;
  productActiveCount: number;
  orderCount: number;
  totalRevenue: number;
  lowInventoryCount: number;
}

interface OrderStatus {
  status: string;
  count: number;
  amount: number;
}

const STATUS_LABELS: Record<string, string> = {
  pending: '待付款',
  paid: '已付款',
  fulfilled: '已发货',
  refunded: '已退款',
  cancelled: '已取消',
};

export default function DashboardPage() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [orderStatus, setOrderStatus] = useState<OrderStatus[]>([]);
  const [dailyRevenue, setDailyRevenue] = useState<DailyRevenue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<string | null>(null);
  const [shop, setShop] = useState<{ name: string; domain: string } | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const fetchData = useCallback(async () => {
    try {
      const [statsRes, shopRes] = await Promise.all([
        fetch('/api/stats'),
        fetch('/api/shop'),
      ]);
      if (statsRes.ok) {
        const data = await statsRes.json();
        setOverview(data.overview);
        setOrderStatus(data.orderStatus || []);
        setDailyRevenue(data.dailyRevenue || []);
      }
      if (shopRes.ok) {
        const data = await shopRes.json();
        if (data.shop) setShop(data.shop);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '数据加载失败');
    } finally {
      setLoading(false);
      setLastUpdated(new Date());
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSync = async (entity: string) => {
    setSyncing(true);
    setSyncResult(null);
    try {
      const res = await fetch('/api/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ entity }),
      });
      const data = await res.json();
      if (data.ok) {
        setSyncResult(`同步成功: ${Object.entries(data.results).map(([k, v]: [string, any]) => `${k} ${v.count}条`).join(', ')}`);
        fetchData(); // 刷新数据
      } else {
        setSyncResult(`同步失败: ${Object.entries(data.results).filter(([, v]: [string, any]) => v.error).map(([k, v]: [string, any]) => `${k}: ${v.error}`).join('; ')}`);
      }
    } catch (err) {
      setSyncResult(`同步错误: ${err instanceof Error ? err.message : '未知错误'}`);
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: 60, textAlign: 'center' }}>
        <div style={{ fontSize: 24, marginBottom: 12 }}>⟳</div>
        <div style={{ color: 'var(--text-muted)' }}>加载数据中...</div>
      </div>
    );
  }

  return (
    <div>
      {/* 错误提示 */}
      {error && (
        <div
          className="mb-3"
          style={{
            padding: '10px 16px',
            background: 'rgba(255,107,107,0.1)',
            border: '1px solid rgba(255,107,107,0.3)',
            borderRadius: 8,
            color: 'var(--danger)',
            fontSize: 13,
          }}
        >
          ⚠ {error}
          <button className="btn btn-sm" style={{ marginLeft: 12 }} onClick={fetchData}>重试</button>
        </div>
      )}

      {/* 顶部标题 */}
      <div className="flex-between mb-3">
        <div>
          <h2 style={{ fontSize: 20, fontWeight: 700 }}>
            {shop ? shop.name : '看板概览'}
          </h2>
          <p className="text-muted text-sm">
            {shop ? shop.domain : '请先在「店铺设置」连接你的 Shoplazza 店铺'}
            {' · '}
            更新于 {lastUpdated.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            className="btn btn-sm"
            onClick={fetchData}
            title="刷新数据"
          >
            ↻
          </button>
          <button
            className="btn btn-sm"
            onClick={() => handleSync('products')}
            disabled={syncing}
          >
            {syncing ? '⟳' : '↻'} 同步商品
          </button>
          <button
            className="btn btn-sm"
            onClick={() => handleSync('orders')}
            disabled={syncing}
          >
            {syncing ? '⟳' : '↻'} 同步订单
          </button>
          <button
            className="btn btn-sm btn-primary"
            onClick={() => handleSync('all')}
            disabled={syncing}
          >
            {syncing ? '同步中...' : '一键全同步'}
          </button>
        </div>
      </div>

      {/* 同步结果提示 */}
      {syncResult && (
        <div className="card mb-3" style={{ padding: '10px 16px', fontSize: 13 }}>
          {syncResult}
        </div>
      )}

      {/* 统计卡片 */}
      {overview && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">在售商品</div>
            <div className="stat-value">{overview.productActiveCount}</div>
            <div className="stat-sub">共 {overview.productCount} 个商品</div>
          </div>
          <div className="stat-card success">
            <div className="stat-label">订单总数</div>
            <div className="stat-value">{overview.orderCount}</div>
            <div className="stat-sub">所有渠道</div>
          </div>
          <div className="stat-card info">
            <div className="stat-label">总收入</div>
            <div className="stat-value">
              ${overview.totalRevenue.toFixed(2)}
            </div>
            <div className="stat-sub">已付款 + 已发货</div>
          </div>
          <div className="stat-card warning">
            <div className="stat-label">低库存预警</div>
            <div className="stat-value">{overview.lowInventoryCount}</div>
            <div className="stat-sub">库存 &lt; 10</div>
          </div>
        </div>
      )}

      {/* 订单状态分布 */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">订单状态分布</span>
        </div>
        {orderStatus.length === 0 ? (
          <p className="text-muted text-sm">暂无订单数据</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>状态</th>
                  <th>数量</th>
                  <th>金额</th>
                </tr>
              </thead>
              <tbody>
                {orderStatus.map((s) => (
                  <tr key={s.status}>
                    <td>{STATUS_LABELS[s.status] || s.status}</td>
                    <td>{s.count}</td>
                    <td>${(s.amount || 0).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 近7日收入趋势 */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">近7日收入趋势</span>
        </div>
        <RevenueChart data={dailyRevenue} currency="USD" />
      </div>
    </div>
  );
}
