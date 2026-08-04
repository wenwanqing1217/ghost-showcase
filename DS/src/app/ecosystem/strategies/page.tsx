'use client';

import TopBar from '@/components/layout/TopBar';
import AuthGuard from '@/components/layout/AuthGuard';
import { useEffect, useState } from 'react';

interface Strategy {
  id: string;
  title: string;
  content: string;
  tags?: string[];
  created_at?: string;
}

export default function StrategiesPage() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [suppliers, setSuppliers] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [stratRes, suppRes] = await Promise.all([
          fetch('/api/v1/obsidian/cards/strategies'),
          fetch('/api/v1/obsidian/cards/suppliers'),
        ]);
        if (stratRes.ok) {
          const data = await stratRes.json();
          setStrategies(data.data?.cards || data.data || []);
        }
        if (suppRes.ok) {
          const data = await suppRes.json();
          setSuppliers(data.data?.cards || data.data || []);
        }
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <AuthGuard>
      <TopBar title="策略与供应商" subtitle="运营策略 · 供应商画像 · 知识卡片" />
      <div className="p-6">
        <div className="max-w-5xl mx-auto">
          {/* 策略笔记 */}
          <div className="mb-8">
            <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>策略笔记</h2>
            <div className="grid md:grid-cols-2 gap-4">
              {loading && (
                <div className="card col-span-full" style={{ padding: 40, textAlign: 'center' }}>
                  <p className="text-muted">加载策略笔记...</p>
                </div>
              )}
              {!loading && strategies.map((s, i) => (
                <div key={s.id || i} className="card" style={{ padding: 16 }}>
                  <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 6 }}>{s.title}</div>
                  <p className="text-muted text-sm" style={{ display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {s.content}
                  </p>
                  {s.tags && s.tags.length > 0 && (
                    <div className="flex gap-1.5 mt-2 flex-wrap">
                      {s.tags.map((tag, j) => (
                        <span key={j} className="badge badge-pending" style={{ fontSize: 10 }}>#{tag}</span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {!loading && strategies.length === 0 && (
                <div className="card col-span-full" style={{ padding: 40, textAlign: 'center' }}>
                  <p className="text-muted">暂无策略笔记</p>
                </div>
              )}
            </div>
          </div>

          {/* 供应商画像 */}
          <div>
            <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>供应商画像</h2>
            <div className="grid md:grid-cols-2 gap-4">
              {loading && (
                <div className="card col-span-full" style={{ padding: 40, textAlign: 'center' }}>
                  <p className="text-muted">加载供应商画像...</p>
                </div>
              )}
              {!loading && suppliers.map((s, i) => (
                <div key={s.id || i} className="card" style={{ padding: 16 }}>
                  <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 6 }}>{s.title}</div>
                  <p className="text-muted text-sm" style={{ display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {s.content}
                  </p>
                  {s.tags && s.tags.length > 0 && (
                    <div className="flex gap-1.5 mt-2 flex-wrap">
                      {s.tags.map((tag, j) => (
                        <span key={j} className="badge badge-active" style={{ fontSize: 10 }}>#{tag}</span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {!loading && suppliers.length === 0 && (
                <div className="card col-span-full" style={{ padding: 40, textAlign: 'center' }}>
                  <p className="text-muted">暂无供应商画像</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}
