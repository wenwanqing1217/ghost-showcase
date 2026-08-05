'use client';

/**
 * /shop — C 端公开商品展示页（询盘模式 MVP）
 *
 * 零成本电商起步方案：
 * - 公开访问，无需登录
 * - 展示 OneBound 同步的 active 商品
 * - 每个商品卡片有"立即询价"按钮 → 跳转邮件/微信
 * - 不涉及支付，线下成交
 *
 * 联系方式通过环境变量配置：
 * - NEXT_PUBLIC_SHOP_EMAIL: 询盘接收邮箱
 * - NEXT_PUBLIC_SHOP_WECHAT: 微信号（显示二维码或文字）
 * - NEXT_PUBLIC_SHOP_NAME: 店铺名称
 */

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { DEMO_PRODUCTS } from '@/lib/demo-data';

// ── 店铺配置（环境变量）──
const SHOP_NAME = process.env.NEXT_PUBLIC_SHOP_NAME || 'Ghost Store';
const SHOP_TAGLINE = process.env.NEXT_PUBLIC_SHOP_TAGLINE || '精选好物 · 一键询价';
const SHOP_EMAIL = process.env.NEXT_PUBLIC_SHOP_EMAIL || '';
const SHOP_WECHAT = process.env.NEXT_PUBLIC_SHOP_WECHAT || '';

// ── 类型 ──
interface Product {
  id: string;
  externalId: string;
  title: string;
  description: string | null;
  price: number;
  comparePrice: number | null;
  currency: string;
  inventory: number;
  images: string;
  status: string;
}

// ── 工具函数 ──
function parseImages(images: string): string[] {
  try {
    const arr = JSON.parse(images);
    return Array.isArray(arr) ? arr.filter(Boolean) : [];
  } catch {
    return [];
  }
}

function formatPrice(price: number, currency: string): string {
  const symbol = currency === 'USD' ? '$' : currency === 'CNY' ? '¥' : `${currency} `;
  return `${symbol}${price.toFixed(2)}`;
}

function inventoryLabel(inv: number): { text: string; color: string } {
  if (inv <= 0) return { text: '缺货', color: '#6b7280' };
  if (inv < 10) return { text: `仅剩 ${inv} 件`, color: '#f59e0b' };
  return { text: '有货', color: '#10b981' };
}

function inquireUrl(product: Product): string {
  const subject = encodeURIComponent(`询价：${product.title}`);
  const body = encodeURIComponent(
    `你好，我对以下商品感兴趣：\n\n商品：${product.title}\n价格：${formatPrice(product.price, product.currency)}\n\n请问：\n1. 是否有货？\n2. 运费多少？\n3. 预计多久发货？\n\n谢谢！`,
  );
  return `mailto:${SHOP_EMAIL}?subject=${subject}&body=${body}`;
}

export default function ShopPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [isDemo, setIsDemo] = useState(false);
  const [search, setSearch] = useState('');

  const fetchProducts = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ status: 'active', limit: '60' });
      if (search) params.set('search', search);

      const res = await fetch(`/api/products?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        if (data.items && data.items.length > 0) {
          setProducts(data.items);
          setIsDemo(false);
        } else {
          // API 返回空 → 演示数据
          setIsDemo(true);
          setProducts(
            DEMO_PRODUCTS.filter((p) => p.status === 'active').map((p) => ({
              ...p,
              images: JSON.stringify([]),
            })),
          );
        }
      } else {
        setIsDemo(true);
        setProducts(
          DEMO_PRODUCTS.filter((p) => p.status === 'active').map((p) => ({
            ...p,
            images: JSON.stringify([]),
          })),
        );
      }
    } catch {
      setIsDemo(true);
      setProducts(
        DEMO_PRODUCTS.filter((p) => p.status === 'active').map((p) => ({
          ...p,
          images: JSON.stringify([]),
        })),
      );
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      {/* ── 店铺头部 ── */}
      <header
        style={{
          background: 'linear-gradient(135deg, rgba(139,92,246,0.06), rgba(56,189,248,0.04))',
          borderBottom: '1px solid var(--border-color)',
          padding: '24px 0',
        }}
      >
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex items-center justify-between">
            <div>
              <h1
                style={{
                  fontSize: 28,
                  fontWeight: 800,
                  background: 'linear-gradient(135deg, #8b5cf6, #38bdf8)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  letterSpacing: '-0.02em',
                }}
              >
                {SHOP_NAME}
              </h1>
              <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>
                {SHOP_TAGLINE}
              </p>
            </div>
            <Link
              href="/"
              style={{
                fontSize: 12,
                color: 'var(--text-muted)',
                textDecoration: 'none',
                padding: '6px 12px',
                borderRadius: 8,
                border: '1px solid var(--border-color)',
              }}
            >
              ← 返回平台
            </Link>
          </div>
        </div>
      </header>

      {/* ── 演示模式横幅 ── */}
      {isDemo && (
        <div
          style={{
            padding: '10px 16px',
            background: 'rgba(245,158,11,0.06)',
            borderBottom: '1px solid rgba(245,158,11,0.12)',
            color: 'var(--warning)',
            fontSize: 12,
            textAlign: 'center',
          }}
        >
          ⚠ 演示模式 — 未连接 OneBound 货源，显示示例商品。连接后自动切换为真实商品。
        </div>
      )}

      {/* ── 搜索栏 ── */}
      <div className="max-w-6xl mx-auto px-6" style={{ padding: '20px 24px 0' }}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            fetchProducts();
          }}
          className="flex gap-2"
        >
          <div style={{ position: 'relative', flex: 1, maxWidth: 400 }}>
            <span
              style={{
                position: 'absolute',
                left: 12,
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--text-muted)',
                fontSize: 14,
              }}
            >
              🔍
            </span>
            <input
              placeholder="搜索商品..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                paddingLeft: 36,
                width: '100%',
                background: 'var(--bg-secondary)',
                border: '1px solid var(--border-color)',
                borderRadius: 12,
                padding: '10px 12px 10px 36px',
                color: 'var(--text-primary)',
                fontSize: 14,
                outline: 'none',
              }}
            />
          </div>
          <button
            type="submit"
            style={{
              padding: '10px 20px',
              background: 'rgba(139,92,246,0.12)',
              color: 'var(--nebula-light)',
              border: '1px solid rgba(139,92,246,0.2)',
              borderRadius: 12,
              fontSize: 13,
              cursor: 'pointer',
            }}
          >
            搜索
          </button>
        </form>
      </div>

      {/* ── 商品网格 ── */}
      <main className="max-w-6xl mx-auto px-6" style={{ padding: '24px 24px 60px' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: 80 }}>
            <div style={{ fontSize: 32, marginBottom: 12, opacity: 0.4 }}>📦</div>
            <p style={{ color: 'var(--text-muted)' }}>加载商品中...</p>
          </div>
        ) : products.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 80 }}>
            <div style={{ fontSize: 40, marginBottom: 12, opacity: 0.3 }}>📭</div>
            <p style={{ color: 'var(--text-muted)' }}>暂无商品</p>
          </div>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
              gap: 20,
            }}
          >
            {products.map((p) => {
              const imgs = parseImages(p.images);
              const inv = inventoryLabel(p.inventory);
              return (
                <Link
                  key={p.id}
                  href={`/shop/${p.id}`}
                  style={{ textDecoration: 'none', color: 'inherit' }}
                >
                  <div
                    style={{
                      background: 'var(--bg-secondary)',
                      border: '1px solid var(--border-color)',
                      borderRadius: 16,
                      overflow: 'hidden',
                      transition: 'transform 0.2s ease, box-shadow 0.2s ease',
                      cursor: 'pointer',
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.transform = 'translateY(-4px)';
                      e.currentTarget.style.boxShadow = '0 12px 32px rgba(0,0,0,0.2)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.transform = 'translateY(0)';
                      e.currentTarget.style.boxShadow = 'none';
                    }}
                  >
                    {/* 商品图片 */}
                    <div
                      style={{
                        width: '100%',
                        aspectRatio: '1 / 1',
                        background:
                          imgs[0] ?
                            `url(${imgs[0]}) center/cover`
                          : 'linear-gradient(135deg, rgba(139,92,246,0.08), rgba(56,189,248,0.05))',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 48,
                        opacity: imgs[0] ? 1 : 0.3,
                      }}
                    >
                      {!imgs[0] && '📦'}
                    </div>

                    {/* 商品信息 */}
                    <div style={{ padding: 16, flex: 1, display: 'flex', flexDirection: 'column' }}>
                      <h3
                        style={{
                          fontSize: 15,
                          fontWeight: 600,
                          color: 'var(--text-primary)',
                          marginBottom: 6,
                          lineHeight: 1.4,
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden',
                        }}
                      >
                        {p.title}
                      </h3>

                      {p.description && (
                        <p
                          style={{
                            fontSize: 12,
                            color: 'var(--text-muted)',
                            marginBottom: 12,
                            display: '-webkit-box',
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: 'vertical',
                            overflow: 'hidden',
                            flex: 1,
                          }}
                        >
                          {p.description}
                        </p>
                      )}

                      {/* 价格 + 库存 */}
                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'baseline',
                          justifyContent: 'space-between',
                          marginBottom: 12,
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                          <span
                            style={{
                              fontSize: 20,
                              fontWeight: 700,
                              color: 'var(--text-primary)',
                            }}
                          >
                            {formatPrice(p.price, p.currency)}
                          </span>
                          {p.comparePrice && p.comparePrice > p.price && (
                            <span
                              style={{
                                textDecoration: 'line-through',
                                color: 'var(--text-muted)',
                                fontSize: 13,
                              }}
                            >
                              {formatPrice(p.comparePrice, p.currency)}
                            </span>
                          )}
                        </div>
                        <span style={{ fontSize: 11, color: inv.color, fontWeight: 500 }}>
                          {inv.text}
                        </span>
                      </div>

                      {/* 询价按钮 */}
                      <div
                        onClick={(e) => {
                          // 阻止 Link 跳转，直接打开询盘
                          if (!SHOP_EMAIL) {
                            e.preventDefault();
                            return;
                          }
                          e.preventDefault();
                          window.location.href = inquireUrl(p);
                        }}
                        style={{
                          display: 'block',
                          textAlign: 'center',
                          padding: '10px 16px',
                          background: SHOP_EMAIL ?
                            'linear-gradient(135deg, rgba(139,92,246,0.15), rgba(56,189,248,0.1))'
                          : 'var(--bg-primary)',
                          color: SHOP_EMAIL ? 'var(--nebula-light)' : 'var(--text-muted)',
                          border: `1px solid ${SHOP_EMAIL ? 'rgba(139,92,246,0.25)' : 'var(--border-color)'}`,
                          borderRadius: 10,
                          fontSize: 13,
                          fontWeight: 500,
                          cursor: SHOP_EMAIL ? 'pointer' : 'not-allowed',
                        }}
                      >
                        {SHOP_EMAIL ? '💬 立即询价' : '💬 询价未配置'}
                      </div>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </main>

      {/* ── 底部联系区 ── */}
      <footer
        style={{
          borderTop: '1px solid var(--border-color)',
          background: 'var(--bg-secondary)',
          padding: '32px 0',
        }}
      >
        <div className="max-w-6xl mx-auto px-6" style={{ textAlign: 'center' }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, color: 'var(--text-primary)' }}>
            联系我们
          </h3>
          <div
            style={{
              display: 'flex',
              gap: 24,
              justifyContent: 'center',
              flexWrap: 'wrap',
              fontSize: 13,
              color: 'var(--text-muted)',
            }}
          >
            {SHOP_EMAIL && (
              <a
                href={`mailto:${SHOP_EMAIL}`}
                style={{ color: 'var(--nebula-light)', textDecoration: 'none' }}
              >
                ✉ {SHOP_EMAIL}
              </a>
            )}
            {SHOP_WECHAT && <span>💬 微信：{SHOP_WECHAT}</span>}
            {!SHOP_EMAIL && !SHOP_WECHAT && (
              <span style={{ color: 'var(--text-muted)' }}>
                未配置联系方式（设置 NEXT_PUBLIC_SHOP_EMAIL 环境变量启用询盘）
              </span>
            )}
          </div>
          <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 16 }}>
            © {new Date().getFullYear()} {SHOP_NAME} · Powered by Ghost Platform
          </p>
        </div>
      </footer>
    </div>
  );
}
