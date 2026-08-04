'use client';

import TopBar from '@/components/layout/TopBar';
import AuthGuard from '@/components/layout/AuthGuard';
import { useEffect, useState } from 'react';

interface Card {
  id: string;
  type: string;
  title: string;
  content: string;
  tags?: string[];
  created_at?: string;
}

export default function ObsidianPage() {
  const [status, setStatus] = useState<any>(null);
  const [cards, setCards] = useState<Card[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch('/api/v1/obsidian/status');
        if (res.ok) {
          const data = await res.json();
          setStatus(data.data || data);
        }
      } catch {
        // ignore
      }
    };
    fetchStatus();
  }, []);

  useEffect(() => {
    const fetchCards = async () => {
      setLoading(true);
      try {
        const res = await fetch('/api/v1/obsidian/cards?limit=50');
        if (res.ok) {
          const data = await res.json();
          setCards(data.data?.cards || data.data || []);
        }
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    };
    fetchCards();
  }, []);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const res = await fetch(`/api/v1/obsidian/cards/search?q=${encodeURIComponent(searchQuery)}`);
      if (res.ok) {
        const data = await res.json();
        setCards(data.data?.cards || data.data || []);
      }
    } catch {
      // ignore
    } finally {
      setSearching(false);
    }
  };

  return (
    <AuthGuard>
      <TopBar title="知识图谱" subtitle="Obsidian 知识库 · 策略笔记 · 供应商画像" />
      <div className="p-6">
        <div className="max-w-5xl mx-auto">
          {/* Vault 状态 */}
          <div className="card mb-6" style={{ padding: 20 }}>
            <div className="flex-between">
              <div>
                <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>Obsidian 知识库</div>
                <p className="text-muted text-sm">
                  {status?.exists
                    ? `已连接 · ${status?.file_count || 0} 个笔记文件 · 最近: ${status?.recent_file || '无'}`
                    : '未连接 · 请配置 OBSIDIAN_VAULT 环境变量'}
                </p>
              </div>
              <span className={`badge ${status?.exists ? 'badge-active' : 'badge-pending'}`}>
                {status?.exists ? '已连接' : '未连接'}
              </span>
            </div>
            {status?.path && (
              <div className="text-xs mt-2 font-mono" style={{ color: 'var(--text-muted)' }}>
                路径: {status.path}
              </div>
            )}
          </div>

          {/* 搜索栏 */}
          <div className="card mb-6" style={{ padding: 16 }}>
            <div className="flex gap-2">
              <input
                className="input flex-1"
                type="text"
                placeholder="搜索知识卡片..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              />
              <button
                onClick={handleSearch}
                disabled={searching || !searchQuery.trim()}
                className="btn btn-primary"
              >
                {searching ? '搜索中...' : '搜索'}
              </button>
              {searchQuery && (
                <button
                  onClick={() => {
                    setSearchQuery('');
                    window.location.reload();
                  }}
                  className="btn"
                >
                  清除
                </button>
              )}
            </div>
          </div>

          {/* 知识卡片列表 */}
          <div className="grid md:grid-cols-2 gap-4">
            {loading && (
              <div className="card col-span-full" style={{ padding: 40, textAlign: 'center' }}>
                <p className="text-muted">加载知识卡片...</p>
              </div>
            )}
            {!loading && cards.map((card, i) => (
              <div key={card.id || i} className="card" style={{ padding: 16 }}>
                <div className="flex-between mb-2">
                  <span className="badge badge-pending">{card.type}</span>
                  {card.created_at && (
                    <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                      {new Date(card.created_at).toLocaleDateString()}
                    </span>
                  )}
                </div>
                <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 6 }}>{card.title}</div>
                <p className="text-muted text-sm" style={{ display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                  {card.content}
                </p>
                {card.tags && card.tags.length > 0 && (
                  <div className="flex gap-1.5 mt-2 flex-wrap">
                    {card.tags.map((tag, j) => (
                      <span key={j} className="badge badge-pending" style={{ fontSize: 10 }}>#{tag}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {!loading && cards.length === 0 && (
              <div className="card col-span-full" style={{ padding: 40, textAlign: 'center' }}>
                <p className="text-muted">
                  {searchQuery ? '未找到匹配的知识卡片' : '暂无知识卡片'}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}
