'use client';

/**
 * /shop/[id] — C 端商品详情页（询盘模式）
 *
 * 展示商品大图、详细描述、价格、库存
 * "立即询价"按钮 → 打开邮件预填询盘内容
 */

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { DEMO_PRODUCTS } from '@/lib/demo-data';

const SHOP_NAME = process.env.NEXT_PUBLIC_SHOP_NAME || 'Ghost Store';
const SHOP_EMAIL = process.env.NEXT_PUBLIC_SHOP_EMAIL || '';
const SHOP_WECHAT = process.env.NEXT_PUBLIC_SHOP_WECHAT || '';

interface Product {
  id: string;
  title: string;
  description: string | null;
  price: number;
  comparePrice: number | null;
  currency: string;
  inventory: number;
  images: string;
  status: string;
  shop?: { id: string; name: string; domain: string | null };
}

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

export default function ProductDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [activeImg, setActiveImg] = useState(0);

  useEffect(() => {
    async function fetchProduct() {
      setLoading(true);
      try {
        const res = await fetch(`/api/products/${id}`);
        if (res.ok) {
          const data = await res.json();
          setProduct(data.item);
        } else if (res.status === 404) {
          // 尝试演示数据
          const demo = DEMO_PRODUCTS.find((p) => p.id === id);
          if (demo) {
            setProduct({ ...demo, images: JSON.stringify([]) });
          } else {
            setNotFound(true);
          }
        } else {
          const demo = DEMO_PRODUCTS.find((p) => p.id === id);
          setProduct(demo ? { ...demo, images: JSON.stringify([]) } : null);
        }
      } catch {
        const demo = DEMO_PRODUCTS.find((p) => p.id === id);
        setProduct(demo ? { ...demo, images: JSON.stringify([]) } : null);
      } finally {
        setLoading(false);
      }
    }
    if (id) fetchProduct();
  }, [id]);

  function inquireUrl(): string {
    if (!product || !SHOP_EMAIL) return '#';
    const subject = encodeURIComponent(`询价：${product.title}`);
    const body = encodeURIComponent(
      `你好，我对以下商品感兴趣：\n\n商品：${product.title}\n价格：${formatPrice(product.price, product.currency)}\n商品ID：${product.id}\n\n请问：\n1. 是否有货？\n2. 运费多少？\n3. 预计多久发货？\n4. 是否支持批量优惠？\n\n谢谢！`,
    );
    return `mailto:${SHOP_EMAIL}?subject=${subject}&body=${body}`;
  }

  if (loading) {
    return (
      <div className="min-h-screen" style={{ background: 'var(--bg-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 32, marginBottom: 12, opacity: 0.4 }}>📦</div>
          <p style={{ color: 'var(--text-muted)' }}>加载商品详情...</p>
        </div>
      </div>
    );
  }

  if (notFound || !product) {
    return (
      <div className="min-h-screen" style={{ background: 'var(--bg-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 48, marginBottom: 16, opacity: 0.3 }}>🔍</div>
          <h2 style={{ fontSize: 18, color: 'var(--text-primary)', marginBottom: 8 }}>商品不存在</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 20 }}>
            该商品可能已下架或链接有误
          </p>
          <button
            onClick={() => router.push('/shop')}
            style={{
              padding: '10px 20px',
              background: 'rgba(139,92,246,0.12)',
              color: 'var(--nebula-light)',
              border: '1px solid rgba(139,92,246,0.2)',
              borderRadius: 10,
              fontSize: 13,
              cursor: 'pointer',
            }}
          >
            ← 返回店铺
          </button>
        </div>
      </div>
    );
  }

  const images = parseImages(product.images);
  const discount =
    product.comparePrice && product.comparePrice > product.price ?
      Math.round((1 - product.price / product.comparePrice) * 100)
    : 0;

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      {/* 简洁头部 */}
      <header
        style={{
          background: 'linear-gradient(135deg, rgba(139,92,246,0.06), rgba(56,189,248,0.04))',
          borderBottom: '1px solid var(--border-color)',
          padding: '16px 0',
        }}
      >
        <div className="max-w-5xl mx-auto px-6 flex items-center justify-between">
          <Link
            href="/shop"
            style={{
              fontSize: 18,
              fontWeight: 800,
              background: 'linear-gradient(135deg, #8b5cf6, #38bdf8)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              textDecoration: 'none',
            }}
          >
            {SHOP_NAME}
          </Link>
          <Link
            href="/shop"
            style={{
              fontSize: 12,
              color: 'var(--text-muted)',
              textDecoration: 'none',
              padding: '6px 12px',
              borderRadius: 8,
              border: '1px solid var(--border-color)',
            }}
          >
            ← 返回店铺
          </Link>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6" style={{ padding: '32px 24px 60px' }}>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: 40,
          }}
        >
          {/* ── 左：图片区 ── */}
          <div>
            <div
              style={{
                width: '100%',
                aspectRatio: '1 / 1',
                borderRadius: 16,
                overflow: 'hidden',
                background: images[activeImg] ?
                  `url(${images[activeImg]}) center/cover`
                : 'linear-gradient(135deg, rgba(139,92,246,0.08), rgba(56,189,248,0.05))',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 64,
                opacity: images[activeImg] ? 1 : 0.3,
                border: '1px solid var(--border-color)',
              }}
            >
              {!images[activeImg] && '📦'}
            </div>
            {images.length > 1 && (
              <div
                style={{
                  display: 'flex',
                  gap: 8,
                  marginTop: 12,
                  overflowX: 'auto',
                }}
              >
                {images.map((img, i) => (
                  <div
                    key={i}
                    onClick={() => setActiveImg(i)}
                    style={{
                      width: 56,
                      height: 56,
                      borderRadius: 8,
                      background: `url(${img}) center/cover`,
                      border:
                        i === activeImg ?
                          '2px solid var(--nebula-light)'
                        : '1px solid var(--border-color)',
                      cursor: 'pointer',
                      flexShrink: 0,
                    }}
                  />
                ))}
              </div>
            )}
          </div>

          {/* ── 右：信息区 ── */}
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <h1
              style={{
                fontSize: 24,
                fontWeight: 700,
                color: 'var(--text-primary)',
                marginBottom: 12,
                lineHeight: 1.3,
              }}
            >
              {product.title}
            </h1>

            {/* 价格 */}
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 16 }}>
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 800,
                  color: 'var(--nebula-light)',
                }}
              >
                {formatPrice(product.price, product.currency)}
              </span>
              {product.comparePrice && product.comparePrice > product.price && (
                <>
                  <span
                    style={{
                      textDecoration: 'line-through',
                      color: 'var(--text-muted)',
                      fontSize: 18,
                    }}
                  >
                    {formatPrice(product.comparePrice, product.currency)}
                  </span>
                  <span
                    style={{
                      padding: '2px 8px',
                      background: 'rgba(239,68,68,0.1)',
                      color: 'var(--danger)',
                      borderRadius: 6,
                      fontSize: 12,
                      fontWeight: 600,
                    }}
                  >
                    -{discount}%
                  </span>
                </>
              )}
            </div>

            {/* 库存状态 */}
            <div style={{ marginBottom: 24 }}>
              {product.inventory > 0 ? (
                <span
                  style={{
                    fontSize: 13,
                    color: product.inventory < 10 ? '#f59e0b' : '#10b981',
                    fontWeight: 500,
                  }}
                >
                  ● {product.inventory < 10 ? `仅剩 ${product.inventory} 件` : '现货充足'}
                </span>
              ) : (
                <span style={{ fontSize: 13, color: '#6b7280' }}>● 暂时缺货</span>
              )}
            </div>

            {/* 描述 */}
            {product.description && (
              <div style={{ marginBottom: 32 }}>
                <h3
                  style={{
                    fontSize: 13,
                    fontWeight: 600,
                    color: 'var(--text-muted)',
                    marginBottom: 8,
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                  }}
                >
                  商品详情
                </h3>
                <p
                  style={{
                    fontSize: 14,
                    color: 'var(--text-primary)',
                    lineHeight: 1.7,
                    whiteSpace: 'pre-wrap',
                  }}
                >
                  {product.description}
                </p>
              </div>
            )}

            {/* 询价按钮 */}
            <div style={{ marginTop: 'auto' }}>
              {SHOP_EMAIL ? (
                <a
                  href={inquireUrl()}
                  style={{
                    display: 'block',
                    textAlign: 'center',
                    padding: '16px 24px',
                    background: 'linear-gradient(135deg, #8b5cf6, #38bdf8)',
                    color: '#fff',
                    borderRadius: 12,
                    fontSize: 15,
                    fontWeight: 600,
                    textDecoration: 'none',
                    marginBottom: 12,
                  }}
                >
                  💬 立即询价
                </a>
              ) : (
                <div
                  style={{
                    display: 'block',
                    textAlign: 'center',
                    padding: '16px 24px',
                    background: 'var(--bg-secondary)',
                    color: 'var(--text-muted)',
                    borderRadius: 12,
                    fontSize: 15,
                    fontWeight: 500,
                    marginBottom: 12,
                    border: '1px solid var(--border-color)',
                  }}
                >
                  询价未配置
                </div>
              )}

              {/* 联系方式 */}
              <div
                style={{
                  fontSize: 12,
                  color: 'var(--text-muted)',
                  textAlign: 'center',
                  lineHeight: 1.8,
                }}
              >
                {SHOP_EMAIL && (
                  <div>
                    ✉ <a href={`mailto:${SHOP_EMAIL}`} style={{ color: 'var(--nebula-light)' }}>{SHOP_EMAIL}</a>
                  </div>
                )}
                {SHOP_WECHAT && <div>💬 微信：{SHOP_WECHAT}</div>}
                {!SHOP_EMAIL && !SHOP_WECHAT && (
                  <div>设置 NEXT_PUBLIC_SHOP_EMAIL 环境变量启用询盘</div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
