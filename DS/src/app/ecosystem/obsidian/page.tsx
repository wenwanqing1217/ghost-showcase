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
  updated_at?: string;
  source?: string;
  file_path?: string;
}

interface SyncHistory {
  direction: string;
  status: string;
  synced: number;
  total: number;
  errors: string[];
  timestamp: string;
}

interface VaultStatus {
  exists: boolean;
  path?: string;
  file_count?: number;
  recent_file?: string;
  last_sync?: string;
  total_cards?: number;
}

type Tab = 'browse' | 'write' | 'sync';

export default function ObsidianPage() {
  const [tab, setTab] = useState<Tab>('browse');
  const [status, setStatus] = useState<VaultStatus | null>(null);
  const [cards, setCards] = useState<Card[]>([]);
  const [history, setHistory] = useState<SyncHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filter, setFilter] = useState<'all' | 'strategies' | 'suppliers'>('all');
  const [searching, setSearching] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState('');

  // Write form
  const [writeTitle, setWriteTitle] = useState('');
  const [writeContent, setWriteContent] = useState('');
  const [writeType, setWriteType] = useState('product:insight');
  const [writeTags, setWriteTags] = useState('');
  const [writeLoading, setWriteLoading] = useState(false);

  useEffect(() => {
    loadStatus();
    loadHistory();
  }, []);

  useEffect(() => {
    if (tab === 'browse') loadCards();
    else if (tab === 'sync') loadHistory();
  }, [tab, filter]);

  async function loadStatus() {
    try {
      const res = await fetch('/api/v1/obsidian/status');
      if (res.ok) {
        const data = await res.json();
        setStatus(data.data || data);
      }
    } catch { /* ignore */ }
  }

  async function loadCards() {
    setLoading(true);
    setError('');
    try {
      const base = filter === 'all' ? '?limit=50' : `?type=${filter}&limit=50`;
      const res = await fetch(`/api/v1/obsidian/cards${base}`);
      if (res.ok) {
        const data = await res.json();
        setCards(data.data?.cards || data.data || []);
      } else {
        setError(`加载失败 (${res.status})`);
      }
    } catch {
      setError('加载失败');
    } finally {
      setLoading(false);
    }
  }

  async function loadHistory() {
    try {
      const res = await fetch('/api/v1/obsidian/sync/history?limit=20');
      if (res.ok) {
        const data = await res.json();
        setHistory(data.data?.history || data.data?.history || []);
      }
    } catch { /* ignore */ }
  }

  async function handleSearch() {
    if (!searchQuery.trim()) return;
    setSearching(true);
    setError('');
    try {
      const res = await fetch(`/api/v1/obsidian/cards/search?q=${encodeURIComponent(searchQuery)}&limit=20`);
      if (res.ok) {
        const data = await res.json();
        setCards(data.data?.cards || data.data || []);
      } else {
        setError(`搜索失败 (${res.status})`);
      }
    } catch {
      setError('搜索失败');
    } finally {
      setSearching(false);
    }
  }

  async function writeCard() {
    if (!writeTitle.trim() || !writeContent.trim()) {
      setError('请填写标题和内容');
      return;
    }
    setWriteLoading(true);
    setError('');
    try {
      const res = await fetch('/api/v1/obsidian/cards', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: writeType,
          title: writeTitle.trim(),
          content: writeContent.trim(),
          tags: writeTags.split(',').map(t => t.trim()).filter(Boolean),
        }),
      });
      const data = await res.json();
      if (res.ok && data.id) {
        setWriteTitle('');
        setWriteContent('');
        setWriteTags('');
        setTab('browse');
        loadCards();
        loadStatus();
      } else {
        setError(data.error || data.detail || '写入失败');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : '写入失败');
    } finally {
      setWriteLoading(false);
    }
  }

  async function triggerSync() {
    setSyncing(true);
    setError('');
    try {
      const res = await fetch('/api/v1/obsidian/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ direction: 'both' }),
      });
      const data = await res.json();
      if (res.ok) {
        await loadHistory();
        await loadStatus();
      } else {
        setError(data.error || data.detail || '同步失败');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : '同步失败');
    } finally {
      setSyncing(false);
    }
  }

  return (
    <AuthGuard>
      <TopBar title="知识图谱" subtitle="Obsidian 知识库 · 策略笔记 · 供应商画像 · 双向同步" />
      <div className="p-6">
        <div className="max-w-6xl mx-auto">
          {/* Vault 状态栏 */}
          <div className="card mb-4" style={{ padding: 16 }}>
            <div className="flex-between">
              <div className="flex items-center gap-4">
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 2 }}>
                    Obsidian 知识库
                  </div>
                  <p className="text-muted text-sm">
                    {status?.exists
                      ? `已连接 · ${status?.file_count || 0} 个笔记文件 · ${status?.total_cards || 0} 张卡片`
                      : '未连接 · 请配置 OBSIDIAN_VAULT 环境变量'}
                  </p>
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={triggerSync}
                  disabled={syncing}
                  className="btn btn-sm"
                  title="双向同步"
                >
                  {syncing ? '同步中...' : '↻ 同步'}
                </button>
                <button onClick={loadStatus} className="btn btn-sm" title="刷新状态">
                  ↻
                </button>
                <a
                  className="btn btn-sm btn-primary"
                  href="obsidian://"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  打开 Obsidian
                </a>
              </div>
            </div>
            {status?.path && (
              <div className="text-xs mt-2 font-mono" style={{ color: 'var(--text-muted)' }}>
                路径: {status.path}
              </div>
            )}
          </div>

          {/* Tab 切换 */}
          <div className="flex gap-1 mb-4 p-1 rounded-xl" style={{ background: 'var(--bg-hover)' }}>
            {[
              { key: 'browse' as Tab, label: '📖 浏览卡片' },
              { key: 'write' as Tab, label: '✏️ 写入卡片' },
              { key: 'sync' as Tab, label: '🔄 同步历史' },
            ].map((t) => (
              <button
                key={t.key}
                onClick={() => { setTab(t.key); setError(''); }}
                className="flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all"
                style={{
                  background: tab === t.key ? 'var(--bg-secondary)' : 'transparent',
                  color: tab === t.key ? 'var(--text-primary)' : 'var(--text-muted)',
                  boxShadow: tab === t.key ? '0 1px 3px rgba(0,0,0,0.2)' : 'none',
                }}
              >
                {t.label}
              </button>
            ))}
          </div>

          {error && (
            <div
              className="mb-4 p-3 rounded-lg text-sm"
              style={{
                background: 'rgba(239,68,68,0.1)',
                color: 'var(--danger)',
                border: '1px solid rgba(239,68,68,0.2)',
              }}
            >
              {error}
            </div>
          )}

          {/* 浏览卡片 */}
          {tab === 'browse' && (
            <div>
              {/* 搜索和过滤 */}
              <div className="card mb-4" style={{ padding: 16 }}>
                <div className="flex gap-2 mb-3">
                  <button
                    onClick={() => setFilter('all')}
                    className={`btn btn-sm ${filter === 'all' ? 'btn-primary' : ''}`}
                  >
                    全部
                  </button>
                  <button
                    onClick={() => setFilter('strategies')}
                    className={`btn btn-sm ${filter === 'strategies' ? 'btn-primary' : ''}`}
                  >
                    策略笔记
                  </button>
                  <button
                    onClick={() => setFilter('suppliers')}
                    className={`btn btn-sm ${filter === 'suppliers' ? 'btn-primary' : ''}`}
                  >
                    供应商画像
                  </button>
                </div>
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
                      onClick={() => { setSearchQuery(''); loadCards(); }}
                      className="btn"
                    >
                      清除
                    </button>
                  )}
                </div>
              </div>

              {/* 卡片列表 */}
              <div className="grid md:grid-cols-2 gap-4">
                {loading && (
                  <div className="card col-span-full" style={{ padding: 40, textAlign: 'center' }}>
                    <p className="text-muted">加载知识卡片...</p>
                  </div>
                )}
                {!loading && cards.map((card) => (
                  <div key={card.id} className="card" style={{ padding: 16 }}>
                    <div className="flex-between mb-2">
                      <div className="flex gap-2 items-center">
                        <span className="badge badge-pending">{card.type}</span>
                        {card.source && (
                          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                            {card.source}
                          </span>
                        )}
                      </div>
                      {card.updated_at && (
                        <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                          {new Date(card.updated_at).toLocaleDateString()}
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
                    {card.file_path && (
                      <div className="text-xs mt-2 font-mono" style={{ color: 'var(--text-muted)' }}>
                        {card.file_path}
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
          )}

          {/* 写入卡片 */}
          {tab === 'write' && (
            <div className="card" style={{ padding: 24 }}>
              <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: 'var(--text-primary)' }}>
                写入知识卡片
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs text-muted mb-1.5">卡片类型</label>
                  <select
                    value={writeType}
                    onChange={(e) => setWriteType(e.target.value)}
                    className="w-full rounded-xl px-4 py-2.5 text-sm"
                    style={{
                      background: 'var(--bg-secondary)',
                      color: 'var(--text-primary)',
                      border: '1px solid var(--border-color)',
                    }}
                  >
                    <option value="product:insight">商品洞察</option>
                    <option value="order:analysis">订单分析</option>
                    <option value="strategy">策略笔记</option>
                    <option value="supplier">供应商画像</option>
                    <option value="customer">客户画像</option>
                    <option value="general">通用</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-muted mb-1.5">标题</label>
                  <input
                    type="text"
                    value={writeTitle}
                    onChange={(e) => setWriteTitle(e.target.value)}
                    placeholder="卡片标题"
                    className="w-full rounded-xl px-4 py-2.5 text-sm"
                    style={{
                      background: 'var(--bg-secondary)',
                      color: 'var(--text-primary)',
                      border: '1px solid var(--border-color)',
                    }}
                  />
                </div>
                <div>
                  <label className="block text-xs text-muted mb-1.5">内容 (Markdown)</label>
                  <textarea
                    value={writeContent}
                    onChange={(e) => setWriteContent(e.target.value)}
                    placeholder="卡片内容..."
                    rows={8}
                    className="w-full rounded-xl px-4 py-2.5 text-sm"
                    style={{
                      background: 'var(--bg-secondary)',
                      color: 'var(--text-primary)',
                      border: '1px solid var(--border-color)',
                      fontFamily: "'JetBrains Mono', monospace",
                      fontSize: 13,
                      resize: 'vertical',
                    }}
                  />
                </div>
                <div>
                  <label className="block text-xs text-muted mb-1.5">标签 (逗号分隔)</label>
                  <input
                    type="text"
                    value={writeTags}
                    onChange={(e) => setWriteTags(e.target.value)}
                    placeholder="策略, Q3, 重点"
                    className="w-full rounded-xl px-4 py-2.5 text-sm"
                    style={{
                      background: 'var(--bg-secondary)',
                      color: 'var(--text-primary)',
                      border: '1px solid var(--border-color)',
                    }}
                  />
                </div>
                <button
                  onClick={writeCard}
                  disabled={writeLoading}
                  className="px-6 py-2.5 rounded-xl text-sm font-medium"
                  style={{
                    background: 'rgba(139,92,246,0.15)',
                    color: 'var(--nebula-light)',
                    border: '1px solid rgba(139,92,246,0.2)',
                    cursor: writeLoading ? 'not-allowed' : 'pointer',
                    opacity: writeLoading ? 0.6 : 1,
                  }}
                >
                  {writeLoading ? '写入中...' : '写入卡片'}
                </button>
              </div>
            </div>
          )}

          {/* 同步历史 */}
          {tab === 'sync' && (
            <div className="card" style={{ padding: 24 }}>
              <div className="flex-between mb-4">
                <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)' }}>
                  同步历史
                </h3>
                <button onClick={loadHistory} className="btn btn-sm">刷新</button>
              </div>
              {history.length === 0 ? (
                <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                  暂无同步记录
                </div>
              ) : (
                <div className="space-y-2">
                  {history.map((h, i) => (
                    <div
                      key={i}
                      style={{
                        padding: 12,
                        background: 'var(--bg-hover)',
                        borderRadius: 8,
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <div>
                        <div style={{ fontWeight: 600, fontSize: 13 }}>
                          {h.direction} · {h.synced}/{h.total} 张卡片
                        </div>
                        {h.errors && h.errors.length > 0 && (
                          <div style={{ fontSize: 11, color: 'var(--danger)', marginTop: 2 }}>
                            错误: {h.errors.join(', ')}
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-3">
                        <span
                          className="badge"
                          style={{
                            fontSize: 10,
                            background: h.status === 'completed' ? 'rgba(16,185,129,0.1)' : 'rgba(245,158,11,0.1)',
                            color: h.status === 'completed' ? '#10b981' : '#f59e0b',
                          }}
                        >
                          {h.status === 'completed' ? '完成' : h.status}
                        </span>
                        <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                          {h.timestamp ? new Date(h.timestamp).toLocaleString() : ''}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </AuthGuard>
  );
}
