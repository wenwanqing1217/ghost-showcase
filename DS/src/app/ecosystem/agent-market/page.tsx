'use client';

import TopBar from '@/components/layout/TopBar';
import AuthGuard from '@/components/layout/AuthGuard';
import { useEffect, useState } from 'react';

// ── Types ──

interface MarketAgent {
  agent_id: string;
  name: string;
  type: string;
  endpoint: string;
  skills: string[];
  is_free: boolean;
  is_online: boolean;
  description: string;
  owner_alpha_id: string;
  status: string;
  price_credits: number;
  category: string;
  rating: number;
  total_calls: number;
  registered_at: number;
  last_heartbeat: number;
  stats?: Record<string, unknown>;
}

interface CallResult {
  success: boolean;
  result?: unknown;
  error?: string;
  billing?: {
    charged: boolean;
    price: number;
    reason: string;
    owner_gain?: number;
    platform_fee?: number;
  };
  execution_time_ms?: number;
}

export default function AgentMarketPage() {
  const [agents, setAgents] = useState<MarketAgent[]>([]);
  const [categories, setCategories] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 过滤
  const [search, setSearch] = useState('');
  const [activeCategory, setActiveCategory] = useState('');

  // 调用面板
  const [callTarget, setCallTarget] = useState<MarketAgent | null>(null);
  const [callSkill, setCallSkill] = useState('');
  const [callParams, setCallParams] = useState('{}');
  const [callerAlphaId, setCallerAlphaId] = useState('');
  const [calling, setCalling] = useState(false);
  const [callResult, setCallResult] = useState<CallResult | null>(null);

  useEffect(() => {
    init();
  }, []);

  const init = async () => {
    setLoading(true);
    setError(null);
    try {
      const idRes = await fetch('/api/v1/human/identity', { credentials: 'include' });
      if (idRes.ok) {
        const idData = await idRes.json();
        const aid = idData.data?.alpha_id || idData.alpha_id || '';
        setCallerAlphaId(aid);
      }
      await Promise.all([fetchAgents(), fetchCategories()]);
    } catch (e) {
      setError(e instanceof Error ? e.message : '初始化失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchAgents = async (q?: string, cat?: string) => {
    try {
      const params = new URLSearchParams();
      if (q ?? search) params.set('q', q ?? search);
      if (cat ?? activeCategory) params.set('category', cat ?? activeCategory);
      const res = await fetch(`/api/v1/agent/a2a/market?${params.toString()}`, {
        credentials: 'include',
      });
      if (res.ok) {
        const data = await res.json();
        setAgents(data.items || []);
      }
    } catch (e) {
      console.warn('fetch agents failed', e);
    }
  };

  const fetchCategories = async () => {
    try {
      const res = await fetch('/api/v1/agent/a2a/categories', { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setCategories(data.categories || {});
      }
    } catch (e) {
      console.warn('fetch categories failed', e);
    }
  };

  const onSearch = (q: string) => {
    setSearch(q);
    fetchAgents(q, activeCategory);
  };

  const onCategory = (cat: string) => {
    const newCat = cat === activeCategory ? '' : cat;
    setActiveCategory(newCat);
    fetchAgents(search, newCat);
  };

  // ── 调用 agent ──
  const onCall = async () => {
    if (!callTarget) return;
    if (!callSkill.trim()) {
      setError('请选择/输入要调用的 skill');
      return;
    }
    let params = {};
    try {
      params = callParams.trim() ? JSON.parse(callParams) : {};
    } catch {
      setError('参数 JSON 格式错误');
      return;
    }
    setCalling(true);
    setError(null);
    setCallResult(null);
    try {
      const res = await fetch('/api/v1/agent/a2a/call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          caller: callerAlphaId || 'anonymous',
          target: callTarget.agent_id,
          skill: callSkill.trim(),
          params,
          caller_alpha_id: callerAlphaId,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setCallResult({ success: false, error: data.detail || data.error || '调用失败' });
      } else {
        setCallResult(data);
      }
    } catch (e) {
      setCallResult({ success: false, error: e instanceof Error ? e.message : '网络错误' });
    } finally {
      setCalling(false);
    }
  };

  // ── 渲染 ──
  if (loading) {
    return (
      <AuthGuard>
        <TopBar title="Agent 市场" subtitle="发现、搜索、调用其他用户上架的 agent" />
        <div className="p-6 text-text-muted">加载中...</div>
      </AuthGuard>
    );
  }

  return (
    <AuthGuard>
      <TopBar title="Agent 市场" subtitle="发现、搜索、调用其他用户上架的 agent" />
      <div className="p-6">
        <div className="max-w-6xl mx-auto">
          {error && (
            <div
              className="mb-4 p-3 rounded-lg text-sm"
              style={{ background: 'rgba(239,68,68,0.1)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.2)' }}
            >
              {error}
              <button
                onClick={() => setError(null)}
                className="float-right text-xs"
                style={{ color: '#ef4444' }}
              >
                关闭
              </button>
            </div>
          )}

          {/* 搜索 + 分类 */}
          <div className="flex flex-col md:flex-row gap-3 mb-6">
            <input
              value={search}
              onChange={(e) => onSearch(e.target.value)}
              placeholder="搜索 agent 名称、描述、技能..."
              className="flex-1 px-4 py-2 rounded-lg text-sm"
              style={{
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid var(--border-color)',
                color: 'var(--text-primary)',
              }}
            />
            <div className="flex gap-2 flex-wrap">
              <CategoryChip
                label="全部"
                count={Object.values(categories).reduce((a, b) => a + b, 0)}
                active={activeCategory === ''}
                onClick={() => onCategory('')}
              />
              {Object.entries(categories).map(([cat, count]) => (
                <CategoryChip
                  key={cat}
                  label={cat}
                  count={count}
                  active={activeCategory === cat}
                  onClick={() => onCategory(cat)}
                />
              ))}
            </div>
          </div>

          {/* Agent 网格 */}
          {agents.length === 0 ? (
            <div className="glass-card p-8 rounded-xl text-center text-text-muted">
              没有找到匹配的 agent，试试调整搜索关键词或分类
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {agents.map((agent) => (
                <AgentCard
                  key={agent.agent_id}
                  agent={agent}
                  onCall={(a) => {
                    setCallTarget(a);
                    setCallSkill(a.skills[0] || '');
                    setCallParams('{}');
                    setCallResult(null);
                  }}
                />
              ))}
            </div>
          )}

          {/* 调用面板（modal） */}
          {callTarget && (
            <div
              className="fixed inset-0 flex items-center justify-center z-50 p-4"
              style={{ background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)' }}
              onClick={() => setCallTarget(null)}
            >
              <div
                className="glass-card rounded-xl p-5 max-w-lg w-full max-h-[90vh] overflow-y-auto"
                onClick={(e) => e.stopPropagation()}
                style={{ background: 'var(--ghost-bg-elevated, #1a1a2e)' }}
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-base font-semibold text-white">{callTarget.name}</h3>
                    <p className="text-xs text-text-muted mt-1">
                      {callTarget.description || '无描述'}
                    </p>
                    <p className="text-[11px] text-text-muted font-mono mt-1">
                      {callTarget.agent_id}
                    </p>
                  </div>
                  <button
                    onClick={() => setCallTarget(null)}
                    className="text-text-muted hover:text-white text-xl"
                  >
                    ×
                  </button>
                </div>

                {/* 价格提示 */}
                <div
                  className="p-2.5 rounded-lg text-xs mb-4"
                  style={{
                    background: callTarget.price_credits > 0 ? 'rgba(251,191,36,0.08)' : 'rgba(16,185,129,0.08)',
                    color: callTarget.price_credits > 0 ? '#fbbf24' : '#10b981',
                  }}
                >
                  {callTarget.price_credits > 0
                    ? `付费 agent：每次调用扣 ${callTarget.price_credits} 积分（好友免费，自己免费）`
                    : '免费 agent：调用不扣积分'}
                </div>

                {/* 调用表单 */}
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs text-text-muted mb-1">技能（skill）</label>
                    <select
                      value={callSkill}
                      onChange={(e) => setCallSkill(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg text-sm"
                      style={{
                        background: 'rgba(255,255,255,0.03)',
                        border: '1px solid var(--border-color)',
                        color: 'var(--text-primary)',
                      }}
                    >
                      {callTarget.skills.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-text-muted mb-1">参数（JSON）</label>
                    <textarea
                      value={callParams}
                      onChange={(e) => setCallParams(e.target.value)}
                      rows={4}
                      className="w-full px-3 py-2 rounded-lg text-sm font-mono"
                      style={{
                        background: 'rgba(255,255,255,0.03)',
                        border: '1px solid var(--border-color)',
                        color: 'var(--text-primary)',
                      }}
                    />
                  </div>
                  {callerAlphaId && (
                    <div className="text-xs text-text-muted">
                      调用方： <span className="font-mono">{callerAlphaId}</span>
                    </div>
                  )}
                  <button
                    onClick={onCall}
                    disabled={calling}
                    className="w-full py-2 rounded-lg text-sm font-medium"
                    style={{
                      background: 'var(--nebula)',
                      color: 'white',
                      opacity: calling ? 0.6 : 1,
                      cursor: calling ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {calling ? '调用中...' : '调用'}
                  </button>
                </div>

                {/* 调用结果 */}
                {callResult && (
                  <div className="mt-4 pt-4 border-t border-ghost-border">
                    <div className="text-xs font-semibold mb-2 flex items-center gap-2">
                      <span
                        className="px-2 py-0.5 rounded-full text-xs"
                        style={{
                          background: callResult.success ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
                          color: callResult.success ? '#10b981' : '#ef4444',
                        }}
                      >
                        {callResult.success ? '成功' : '失败'}
                      </span>
                      {callResult.execution_time_ms && (
                        <span className="text-text-muted">
                          {callResult.execution_time_ms.toFixed(0)} ms
                        </span>
                      )}
                    </div>
                    {callResult.error && (
                      <div className="text-xs text-red-400 mb-2">{callResult.error}</div>
                    )}
                    {callResult.billing && (
                      <div
                        className="text-xs mb-2 p-2 rounded"
                        style={{ background: 'rgba(255,255,255,0.03)' }}
                      >
                        计费：{callResult.billing.reason}
                        {callResult.billing.charged && (
                          <>
                            {' '}· 扣 <b style={{ color: '#fbbf24' }}>{callResult.billing.price}</b> 积分
                            {' '}· 平台抽成 {callResult.billing.platform_fee}
                          </>
                        )}
                      </div>
                    )}
                    {callResult.result !== undefined && (
                      <pre
                        className="text-xs p-2 rounded overflow-x-auto"
                        style={{ background: 'rgba(0,0,0,0.3)', color: 'var(--text-secondary)' }}
                      >
                        {JSON.stringify(callResult.result, null, 2)}
                      </pre>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </AuthGuard>
  );
}

// ── 子组件 ──

function CategoryChip({
  label,
  count,
  active,
  onClick,
}: {
  label: string;
  count: number;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all whitespace-nowrap"
      style={{
        background: active ? 'rgba(139,92,246,0.15)' : 'rgba(255,255,255,0.03)',
        color: active ? 'var(--nebula-light)' : 'var(--text-secondary)',
        border: `1px solid ${active ? 'rgba(139,92,246,0.3)' : 'var(--border-color)'}`,
      }}
    >
      {label} ({count})
    </button>
  );
}

function AgentCard({ agent, onCall }: { agent: MarketAgent; onCall: (a: MarketAgent) => void }) {
  return (
    <div className="glass-card p-4 rounded-xl flex flex-col gap-2">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-white truncate">{agent.name}</h3>
          {agent.category && (
            <span className="text-[10px] text-text-muted">{agent.category}</span>
          )}
        </div>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          {agent.is_online ? (
            <span className="w-1.5 h-1.5 rounded-full" style={{ background: '#10b981' }} />
          ) : (
            <span className="w-1.5 h-1.5 rounded-full" style={{ background: '#64748b' }} />
          )}
          {agent.price_credits > 0 ? (
            <span className="text-xs" style={{ color: '#fbbf24' }}>
              {agent.price_credits} 分
            </span>
          ) : (
            <span className="text-xs text-text-muted">免费</span>
          )}
        </div>
      </div>

      <p className="text-xs text-text-secondary line-clamp-2 min-h-[2.4em]">
        {agent.description || '无描述'}
      </p>

      <div className="flex flex-wrap gap-1 min-h-[1.4em]">
        {agent.skills.slice(0, 4).map((s) => (
          <span
            key={s}
            className="text-[10px] px-1.5 py-0.5 rounded"
            style={{ background: 'rgba(139,92,246,0.1)', color: 'var(--nebula-light)' }}
          >
            {s}
          </span>
        ))}
        {agent.skills.length > 4 && (
          <span className="text-[10px] text-text-muted">+{agent.skills.length - 4}</span>
        )}
      </div>

      <div className="flex items-center justify-between pt-1 text-[11px] text-text-muted">
        <span className="font-mono truncate">
          {agent.owner_alpha_id ? agent.owner_alpha_id.slice(0, 16) : '平台基建'}
        </span>
        <span>
          ⭐ {agent.rating.toFixed(1)} · {agent.total_calls} 次
        </span>
      </div>

      <button
        onClick={() => onCall(agent)}
        disabled={!agent.is_online}
        className="mt-1 py-1.5 rounded-lg text-xs font-medium transition-all"
        style={{
          background: agent.is_online ? 'rgba(139,92,246,0.1)' : 'rgba(255,255,255,0.03)',
          color: agent.is_online ? 'var(--nebula-light)' : 'var(--text-muted)',
          border: `1px solid ${agent.is_online ? 'rgba(139,92,246,0.2)' : 'var(--border-color)'}`,
          cursor: agent.is_online ? 'pointer' : 'not-allowed',
        }}
      >
        {agent.is_online ? '调用' : '离线'}
      </button>
    </div>
  );
}
