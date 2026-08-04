'use client';

import { useEffect, useState, useCallback } from 'react';
import StatusBadge from '@/components/StatusBadge';
import Pagination from '@/components/Pagination';
import ProductAiDialog from '@/components/ProductAiDialog';
import TopBar from '@/components/layout/TopBar';
import AuthGuard from '@/components/layout/AuthGuard';
import { getApiUrl } from '@/lib/gateway-client';
import { DEMO_PRODUCTS } from '@/lib/demo-data';

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
  const [isDemo, setIsDemo] = useState(false);

  const fetchProducts = useCallback(async (page: number = 1) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: String(page), limit: '20' });
      if (statusFilter) params.set('status', statusFilter);
      if (search) params.set('search', search);

      const res = await fetch(getApiUrl('/api/products', params));
      if (res.ok) {
        const data = await res.json();
        if (data.items && data.items.length > 0) {
          setProducts(data.items);
          setPagination(data.pagination);
          setIsDemo(false);
        } else {
          // API 返回空数据 → 使用演示数据
          setIsDemo(true);
          setProducts(DEMO_PRODUCTS.map(p => ({ ...p, images: JSON.stringify([]), lastSyncedAt: new Date().toISOString() })));
          setPagination({ page: 1, limit: 20, total: DEMO_PRODUCTS.length, totalPages: 1 });
        }
      } else {
        console.error('[ProductsPage] fetch failed:', res.status, res.statusText);
        setIsDemo(true);
        setProducts(DEMO_PRODUCTS.map(p => ({ ...p, images: JSON.stringify([]), lastSyncedAt: new Date().toISOString() })));
        setPagination({ page: 1, limit: 20, total: DEMO_PRODUCTS.length, totalPages: 1 });
      }
    } catch (err) {
      console.error('[ProductsPage] fetch error:', err);
      setIsDemo(true);
      setProducts(DEMO_PRODUCTS.map(p => ({ ...p, images: JSON.stringify([]), lastSyncedAt: new Date().toISOString() })));
      setPagination({ page: 1, limit: 20, total: DEMO_PRODUCTS.length, totalPages: 1 });
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
            ⚠ 演示模式 — 未连接到 OneBound 货源，显示示例商品数据
          </div>
        )}
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
      <div className="card mb-4" style={{ padding: '14px 18px' }}>
        <form onSubmit={handleSearch} className="flex gap-2" style={{ flexWrap: 'wrap' }}>
          <div style={{ position: 'relative', flex: '1 1 200px' }}>
            <span style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', fontSize: 14 }}>🔍</span>
            <input
              className="input"
              placeholder="搜索商品名称..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ paddingLeft: 36, maxWidth: 280, width: '100%' }}
            />
          </div>
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
      <div className="card" style={{ overflow: 'hidden', padding: 0 }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: 60 }}>
            <div style={{ fontSize: 24, marginBottom: 12, opacity: 0.4 }}>📦</div>
            <p className="text-muted">加载商品数据...</p>
          </div>
        ) : products.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 60 }}>
            <div style={{ fontSize: 40, marginBottom: 12, opacity: 0.3 }}>📭</div>
            <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>暂无商品数据</p>
            <p className="text-xs text-muted" style={{ marginTop: 4 }}>连接 OneBound 货源后同步商品</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <th style={{ padding: '14px 18px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', width: 60 }}>图片</th>
                  <th style={{ padding: '14px 18px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>商品名称</th>
                  <th style={{ padding: '14px 18px', textAlign: 'right', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>价格</th>
                  <th style={{ padding: '14px 18px', textAlign: 'center', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>库存</th>
                  <th style={{ padding: '14px 18px', textAlign: 'center', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>状态</th>
                  <th style={{ padding: '14px 18px', textAlign: 'right', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>同步时间</th>
                  {aiAvailable && <th style={{ padding: '14px 18px', textAlign: 'center', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', width: 80 }}>操作</th>}
                </tr>
              </thead>
              <tbody>
                {products.map((p) => {
                  const imgs = parseImages(p.images);
                  return (
                    <tr key={p.id} style={{ borderBottom: '1px solid rgba(148,163,184,0.06)', transition: 'background 0.15s ease' }}
                      onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(139,92,246,0.03)'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
                    >
                      <td style={{ padding: '14px 18px' }}>
                        {imgs[0] ? (
                          <img
                            src={imgs[0]}
                            alt={p.title}
                            style={{ width: 44, height: 44, objectFit: 'cover', borderRadius: 8, border: '1px solid var(--border-color)' }}
                          />
                        ) : (
                          <div style={{ width: 44, height: 44, background: 'linear-gradient(135deg, rgba(139,92,246,0.08), rgba(56,189,248,0.05))', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, border: '1px solid var(--border-color)' }}>📦</div>
                        )}
                      </td>
                      <td style={{ padding: '14px 18px' }}>
                        <div style={{ fontWeight: 500, fontSize: 14, color: 'var(--text-primary)', marginBottom: 2 }}>{p.title}</div>
                        {p.description && (
                          <div className="text-muted" style={{ fontSize: 12, maxWidth: 320, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {p.description}
                          </div>
                        )}
                      </td>
                      <td style={{ padding: '14px 18px', textAlign: 'right' }}>
                        <span style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-primary)' }}>${p.price.toFixed(2)}</span>
                        {p.comparePrice && p.comparePrice > p.price && (
                          <span className="text-muted" style={{ textDecoration: 'line-through', marginLeft: 8, fontSize: 12 }}>
                            ${p.comparePrice.toFixed(2)}
                          </span>
                        )}
                      </td>
                      <td style={{ padding: '14px 18px', textAlign: 'center' }}>
                        <span style={{ fontSize: 13, color: p.inventory < 10 ? 'var(--danger)' : 'var(--text-primary)', fontWeight: p.inventory < 10 ? 600 : 400 }}>
                          {p.inventory}
                        </span>
                      </td>
                      <td style={{ padding: '14px 18px', textAlign: 'center' }}><StatusBadge status={p.status} /></td>
                      <td style={{ padding: '14px 18px', textAlign: 'right' }}>
                        <span className="text-muted" style={{ fontSize: 12 }}>{new Date(p.lastSyncedAt).toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</span>
                      </td>
                      {aiAvailable && (
                        <td style={{ padding: '14px 18px', textAlign: 'center' }}>
                          <button
                            className="btn btn-sm"
                            onClick={() => setAiProduct(p)}
                            title="AI 优化文案"
                            style={{ fontSize: 11, padding: '4px 12px' }}
                          >
                            ✦ AI
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
