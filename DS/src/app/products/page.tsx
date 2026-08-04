'use client';

import { useEffect, useState, useCallback } from 'react';
import StatusBadge from '@/components/StatusBadge';
import Pagination from '@/components/Pagination';
import ProductAiDialog from '@/components/ProductAiDialog';
import TopBar from '@/components/layout/TopBar';
import AuthGuard from '@/components/layout/AuthGuard';
import { getApiUrl } from '@/lib/gateway-client';

interface Product {
  id: string;
  externalId: string;
  title: string;
  description: string | null;
  price: number;
  comparePrice: number | null;
  currency: string;
  inventory: number;
  images: string; // JSON string
  status: string;
  lastSyncedAt: string;
}

interface PaginationInfo {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [pagination, setPagination] = useState<PaginationInfo>({ page: 1, limit: 20, total: 0, totalPages: 0 });
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [aiAvailable, setAiAvailable] = useState(false);
  const [aiProduct, setAiProduct] = useState<Product | null>(null);
  const [syncMsg, setSyncMsg] = useState<string | null>(null);

  const fetchProducts = useCallback(async (page: number = 1) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: String(page), limit: '20' });
      if (statusFilter) params.set('status', statusFilter);
      if (search) params.set('search', search);

      const res = await fetch(getApiUrl('/api/products', params));
      if (res.ok) {
        const data = await res.json();
        setProducts(data.items);
        setPagination(data.pagination);
      } else {
        console.error('[ProductsPage] fetch failed:', res.status, res.statusText);
      }
    } catch (err) {
      console.error('[ProductsPage] fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, search]);

  useEffect(() => {
    fetchProducts(1);
    // 检查 AI 可用性
    fetch(getApiUrl('/api/ai/status'))
      .then((r) => r.json())
      .then((d) => setAiAvailable(d.available))
      .catch(() => setAiAvailable(false));
  }, [fetchProducts]);

  const parseImages = (images: string): string[] => {
    try { return JSON.parse(images); } catch { return []; }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchProducts(1);
  };

  const handleSync = async () => {
    setSyncing(true);
    setSyncMsg(null);
    try {
      const res = await fetch(getApiUrl('/api/sync'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ entity: 'products' }),
      });
      const data = await res.json();
      if (data.ok) {
        setSyncMsg(`同步完成 · ${data.results?.products?.count || 0} 个商品`);
        fetchProducts(1);
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

  return (
    <AuthGuard>
      <TopBar title="商品管理" subtitle="OneBound 货源商品同步与 AI 文案" />
      <div className="p-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex-between mb-3">
        <div>
          <h2 style={{ fontSize: 20, fontWeight: 700 }}>商品管理</h2>
          <div className="flex gap-2" style={{ marginTop: 4 }}>
            <span className="text-muted text-sm">共 {pagination.total} 个商品</span>
            {aiAvailable && (
              <span style={{
                fontSize: 11,
                padding: '2px 8px',
                borderRadius: 9999,
                background: 'rgba(139,92,246,0.08)',
                color: 'var(--nebula-light)',
                border: '1px solid rgba(139,92,246,0.12)',
              }}>
                AI 就绪
              </span>
            )}
          </div>
        </div>
        <button
          onClick={handleSync}
          disabled={syncing}
          className="btn btn-sm"
          style={{ fontSize: 12 }}
        >
          {syncing ? '⟳ 同步中...' : '⟳ 同步'}
        </button>
      </div>

      {syncMsg && (
        <div style={{
          padding: '8px 12px',
          marginBottom: 12,
          borderRadius: 8,
          background: syncMsg.includes('失败') || syncMsg.includes('失败')
            ? 'rgba(239,68,68,0.08)'
            : 'rgba(16,185,129,0.08)',
          color: syncMsg.includes('失败') ? 'var(--danger)' : 'var(--success)',
          fontSize: 12,
          border: `1px solid ${syncMsg.includes('失败') ? 'rgba(239,68,68,0.12)' : 'rgba(16,185,129,0.12)'}`,
        }}>
          {syncMsg}
        </div>
      )}

      {/* 筛选栏 */}
      <div className="card mb-3" style={{ padding: '12px 16px' }}>
        <form onSubmit={handleSearch} className="flex gap-2" style={{ flexWrap: 'wrap' }}>
          <input
            className="input"
            placeholder="搜索商品名称..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ maxWidth: 240 }}
          />
          <select
            className="input"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{ maxWidth: 140 }}
          >
            <option value="">全部状态</option>
            <option value="active">在售</option>
            <option value="draft">草稿</option>
            <option value="archived">归档</option>
          </select>
          <button type="submit" className="btn btn-sm">搜索</button>
        </form>
      </div>

      {/* 商品列表 */}
      <div className="card">
        {loading ? (
          <p style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>加载中...</p>
        ) : products.length === 0 ? (
          <p style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>暂无商品数据</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th style={{ width: 60 }}>图片</th>
                  <th>商品名称</th>
                  <th>价格</th>
                  <th>库存</th>
                  <th>状态</th>
                  <th>同步时间</th>
                  {aiAvailable && <th style={{ width: 80 }}>操作</th>}
                </tr>
              </thead>
              <tbody>
                {products.map((p) => {
                  const imgs = parseImages(p.images);
                  return (
                    <tr key={p.id}>
                      <td>
                        {imgs[0] ? (
                          <img
                            src={imgs[0]}
                            alt={p.title}
                            style={{ width: 40, height: 40, objectFit: 'cover', borderRadius: 4 }}
                          />
                        ) : (
                          <div style={{ width: 40, height: 40, background: 'var(--bg-hover)', borderRadius: 4 }} />
                        )}
                      </td>
                      <td>
                        <div style={{ fontWeight: 500 }}>{p.title}</div>
                        {p.description && (
                          <div className="text-muted text-sm" style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {p.description}
                          </div>
                        )}
                      </td>
                      <td>
                        <span style={{ fontWeight: 600 }}>${p.price.toFixed(2)}</span>
                        {p.comparePrice && p.comparePrice > p.price && (
                          <span className="text-muted text-sm" style={{ textDecoration: 'line-through', marginLeft: 6 }}>
                            ${p.comparePrice.toFixed(2)}
                          </span>
                        )}
                      </td>
                      <td>
                        <span style={{ color: p.inventory < 10 ? 'var(--danger)' : undefined }}>
                          {p.inventory}
                        </span>
                      </td>
                      <td><StatusBadge status={p.status} /></td>
                      <td className="text-muted text-sm">
                        {new Date(p.lastSyncedAt).toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                      </td>
                      {aiAvailable && (
                        <td>
                          <button
                            className="btn btn-sm"
                            onClick={() => setAiProduct(p)}
                            title="AI 优化文案"
                            style={{ fontSize: 11, padding: '3px 10px' }}
                          >
                            AI
                          </button>
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        <Pagination
          page={pagination.page}
          totalPages={pagination.totalPages}
          onPageChange={(page) => fetchProducts(page)}
        />
      </div>

      {/* AI 文案弹窗 */}
      {aiProduct && (
        <ProductAiDialog
          product={aiProduct}
          onClose={() => setAiProduct(null)}
          onSaved={(title, description) => {
            // 更新列表中对应商品的标题和描述
            setProducts((prev) =>
              prev.map((p) => (p.id === aiProduct.id ? { ...p, title, description } : p))
            );
          }}
        />
      )}
      </div>
    </div>
    </AuthGuard>
  );
}
