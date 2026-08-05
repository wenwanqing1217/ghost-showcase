'use client';

import TopBar from '@/components/layout/TopBar';
import AuthGuard from '@/components/layout/AuthGuard';
import { useEffect, useState } from 'react';

// ── Types ──

interface AgentInfo {
  agent_id: string;
  name: string;
  type: string;
  endpoint: string;
  skills: string[];
  is_free: boolean;
  is_online: boolean;
  description: string;
  owner_alpha_id: string;
  status: 'pending' | 'submitted' | 'approved' | 'delisted';
  price_credits: number;
  category: string;
  rating: number;
  total_calls: number;
  registered_at: number;
  last_heartbeat: number;
  stats?: Record<string, unknown>;
}

interface WalletInfo {
  alpha_id: string;
  balance: number;
  total_earned: number;
  total_spent: number;
  transaction_count: number;
}

interface Transaction {
  tx_id: string;
  alpha_id: string;
  direction: 'credit' | 'debit';
  amount: number;
  reason: string;
  counterparty: string;
  agent_id: string;
  skill: string;
  request_id: string;
  timestamp: number;
}

const STATUS_LABEL: Record<AgentInfo['status'], { label: string; color: string }> = {
  pending: { label: '草稿', color: '#94a3b8' },
  submitted: { label: '待审核', color: '#fbbf24' },
  approved: { label: '已上架', color: '#10b981' },
  delisted: { label: '已下架', color: '#ef4444' },
};

export default function MyAgentsPage() {
  const [alphaId, setAlphaId] = useState<string>('');
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [wallet, setWallet] = useState<WalletInfo | null>(null);
  const [txs, setTxs] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // 注册表单
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    agent_id: '',
    name: '',
    endpoint: '',
    api_key: '',
    skills: '',
    category: '',
    price_credits: '0',
    description: '',
    auto_submit: true,
  });
  const [formLoading, setFormLoading] = useState(false);

  useEffect(() => {
    init();
  }, []);

  const init = async () => {
    setLoading(true);
    setError(null);
    try {
      // 获取当前用户身份
      const idRes = await fetch('/api/v1/human/identity', { credentials: 'include' });
      if (idRes.ok) {
        const idData = await idRes.json();
        const aid = idData.data?.alpha_id || idData.alpha_id || idData.data?.did || '';
        setAlphaId(aid);
        if (aid) {
          await Promise.all([fetchMyAgents(aid), fetchWallet(), fetchTxs()]);
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : '初始化失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchMyAgents = async (aid: string) => {
    try {
      const res = await fetch(`/api/v1/agent/a2a/market?owner=${encodeURIComponent(aid)}`, {
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

  const fetchWallet = async () => {
    try {
      const res = await fetch('/api/v1/credits/wallet', { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setWallet(data.data || data);
      }
    } catch (e) {
      console.warn('fetch wallet failed', e);
    }
  };

  const fetchTxs = async () => {
    try {
      const res = await fetch('/api/v1/credits/transactions?limit=10', {
        credentials: 'include',
      });
      if (res.ok) {
        const data = await res.json();
        setTxs(data.items || []);
      }
    } catch (e) {
      console.warn('fetch txs failed', e);
    }
  };

  // ── 注册 agent ──
  const submitRegister = async () => {
    if (!form.agent_id.trim() || !form.endpoint.trim() || !form.api_key.trim()) {
      setError('agent_id、endpoint、api_key 必填');
      return;
    }
    if (!alphaId) {
      setError('未获取到 alpha_id，无法注册');
      return;
    }
    setFormLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/agent/a2a/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_id: form.agent_id.trim(),
          name: form.name || form.agent_id,
          endpoint: form.endpoint.trim(),
          api_key: form.api_key.trim(),
          skill_list: form.skills.split(',').map((s) => s.trim()).filter(Boolean),
          category: form.category.trim(),
          price_credits: parseInt(form.price_credits || '0', 10) || 0,
          description: form.description.trim(),
          owner_alpha_id: alphaId,
          auto_submit: form.auto_submit,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || data.error || '注册失败');
      setShowForm(false);
      setForm({
        agent_id: '',
        name: '',
        endpoint: '',
        api_key: '',
        skills: '',
        category: '',
        price_credits: '0',
        description: '',
        auto_submit: true,
      });
      await fetchMyAgents(alphaId);
    } catch (e) {
      setError(e instanceof Error ? e.message : '注册失败');
    } finally {
      setFormLoading(false);
    }
  };

  // ── 状态机操作 ──
  const callAction = async (agentId: string, action: 'submit' | 'delist' | 'relist') => {
    setActionLoading(`${agentId}:${action}`);
    setError(null);
    try {
      const res = await fetch(`/api/v1/agent/a2a/agents/${agentId}/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || data.error || `${action} 失败`);
      if (alphaId) await fetchMyAgents(alphaId);
    } catch (e) {
      setError(e instanceof Error ? e.message : `${action} 失败`);
    } finally {
      setActionLoading(null);
    }
  };

  // ── 渲染 ──
  if (loading) {
    return (
      <AuthGuard>
        <TopBar title="我的 Agent" subtitle="注册、管理、上架你接入的 agent" />
        <div className="p-6 text-text-muted">加载中...</div>
      </AuthGuard>
    );
  }

  return (
    <AuthGuard>
      <TopBar title="我的 Agent" subtitle="注册、管理、上架你接入的 agent" />
      <div className="p-6">
        <div className="max-w-6xl mx-auto">
          {error && (
            <div
              className="mb-4 p-3 rounded-lg text-sm"
              style={{ background: 'rgba(239,68,68,0.1)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.2)' }}
            >
              {error}
            </div>
          )}

          {/* 钱包卡片 */}
          {wallet && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <StatCard label="当前余额" value={wallet.balance} accent="var(--nebula)" />
              <StatCard label="累计收入" value={wallet.total_earned} accent="#10b981" />
              <StatCard label="累计支出" value={wallet.total_spent} accent="#fbbf24" />
              <StatCard label="交易笔数" value={wallet.transaction_count} accent="#94a3b8" />
            </div>
          )}

          {/* 顶部操作栏 */}
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-white">
              我的 Agent（{agents.length}）
              {alphaId && <span className="ml-2 text-xs text-text-muted font-mono">{alphaId}</span>}
            </h2>
            <button
              onClick={() => setShowForm(!showForm)}
              className="px-4 py-2 rounded-lg text-sm font-medium transition-all"
              style={{
                background: showForm ? 'rgba(255,255,255,0.05)' : 'rgba(139,92,246,0.1)',
                color: showForm ? 'var(--text-secondary)' : 'var(--nebula-light)',
                border: `1px solid ${showForm ? 'var(--border-color)' : 'rgba(139,92,246,0.2)'}`,
              }}
            >
              {showForm ? '取消' : '+ 注册新 Agent'}
            </button>
          </div>

          {/* 注册表单 */}
          {showForm && (
            <div className="glass-card p-5 rounded-xl mb-6 space-y-3">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <FormInput
                  label="Agent ID *"
                  value={form.agent_id}
                  onChange={(v) => setForm({ ...form, agent_id: v })}
                  placeholder="如：my-translate-bot"
                />
                <FormInput
                  label="显示名"
                  value={form.name}
                  onChange={(v) => setForm({ ...form, name: v })}
                  placeholder="留空则用 Agent ID"
                />
                <FormInput
                  label="Endpoint *"
                  value={form.endpoint}
                  onChange={(v) => setForm({ ...form, endpoint: v })}
                  placeholder="https://your-agent.example.com"
                />
                <FormInput
                  label="API Key *"
                  value={form.api_key}
                  onChange={(v) => setForm({ ...form, api_key: v })}
                  placeholder="你的 agent 调用密钥"
                />
                <FormInput
                  label="技能（逗号分隔）"
                  value={form.skills}
                  onChange={(v) => setForm({ ...form, skills: v })}
                  placeholder="translate, summarize, analyze"
                />
                <FormInput
                  label="分类"
                  value={form.category}
                  onChange={(v) => setForm({ ...form, category: v })}
                  placeholder="翻译 / 文案 / 视频 / 资讯"
                />
                <FormInput
                  label="单次调用价格（积分）"
                  value={form.price_credits}
                  onChange={(v) => setForm({ ...form, price_credits: v })}
                  placeholder="0 表示免费"
                  type="number"
                />
                <div className="flex items-end">
                  <label className="flex items-center gap-2 text-sm text-text-secondary">
                    <input
                      type="checkbox"
                      checked={form.auto_submit}
                      onChange={(e) => setForm({ ...form, auto_submit: e.target.checked })}
                      style={{ accentColor: 'var(--nebula)' }}
                    />
                    自动提交审核
                  </label>
                </div>
              </div>
              <FormInput
                label="描述"
                value={form.description}
                onChange={(v) => setForm({ ...form, description: v })}
                placeholder="一句话介绍你的 agent 能做什么"
              />
              <div className="flex justify-end gap-2 pt-2">
                <button
                  onClick={() => setShowForm(false)}
                  className="px-4 py-2 rounded-lg text-sm"
                  style={{ background: 'rgba(255,255,255,0.03)', color: 'var(--text-secondary)', border: '1px solid var(--border-color)' }}
                >
                  取消
                </button>
                <button
                  onClick={submitRegister}
                  disabled={formLoading}
                  className="px-4 py-2 rounded-lg text-sm font-medium"
                  style={{
                    background: 'var(--nebula)',
                    color: 'white',
                    opacity: formLoading ? 0.6 : 1,
                    cursor: formLoading ? 'not-allowed' : 'pointer',
                  }}
                >
                  {formLoading ? '注册中...' : '注册'}
                </button>
              </div>
              <p className="text-xs text-text-muted">
                状态机：注册后默认 {form.auto_submit ? '「待审核」' : '「草稿」'}。审核通过后才能被市场其他用户发现和调用。
              </p>
            </div>
          )}

          {/* Agent 列表 */}
          {agents.length === 0 ? (
            <div className="glass-card p-8 rounded-xl text-center text-text-muted">
              {alphaId ? '还没有注册任何 agent，点击右上角「+ 注册新 Agent」开始' : '请先登录以查看你的 agent'}
            </div>
          ) : (
            <div className="space-y-3">
              {agents.map((agent) => (
                <AgentCard
                  key={agent.agent_id}
                  agent={agent}
                  actionLoading={actionLoading}
                  onAction={callAction}
                />
              ))}
            </div>
          )}

          {/* 最近交易 */}
          {txs.length > 0 && (
            <div className="mt-8">
              <h3 className="text-sm font-semibold text-white mb-3">最近交易</h3>
              <div className="glass-card rounded-xl overflow-hidden">
                {txs.map((tx, idx) => (
                  <div
                    key={tx.tx_id}
                    className="flex items-center justify-between px-4 py-2.5 text-sm"
                    style={{ borderBottom: idx < txs.length - 1 ? '1px solid var(--border-color)' : 'none' }}
                  >
                    <div className="flex items-center gap-3">
                      <span
                        className="font-mono font-semibold"
                        style={{ color: tx.direction === 'credit' ? '#10b981' : '#fbbf24' }}
                      >
                        {tx.direction === 'credit' ? '+' : '-'}
                        {tx.amount}
                      </span>
                      <span className="text-text-secondary">{tx.reason}</span>
                      {tx.agent_id && (
                        <span className="text-xs text-text-muted font-mono">{tx.agent_id}</span>
                      )}
                    </div>
                    <span className="text-xs text-text-muted">
                      {new Date(tx.timestamp * 1000).toLocaleString('zh-CN')}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </AuthGuard>
  );
}

// ── 子组件 ──

function StatCard({ label, value, accent }: { label: string; value: number; accent: string }) {
  return (
    <div className="glass-card p-4 rounded-xl">
      <div className="text-xs text-text-muted mb-1">{label}</div>
      <div className="text-2xl font-bold" style={{ color: accent }}>
        {value.toLocaleString()}
      </div>
    </div>
  );
}

function FormInput({
  label,
  value,
  onChange,
  placeholder,
  type = 'text',
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
}) {
  return (
    <div>
      <label className="block text-xs text-text-muted mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-3 py-2 rounded-lg text-sm"
        style={{
          background: 'rgba(255,255,255,0.03)',
          border: '1px solid var(--border-color)',
          color: 'var(--text-primary)',
        }}
      />
    </div>
  );
}

function AgentCard({
  agent,
  actionLoading,
  onAction,
}: {
  agent: AgentInfo;
  actionLoading: string | null;
  onAction: (id: string, action: 'submit' | 'delist' | 'relist') => void;
}) {
  const statusInfo = STATUS_LABEL[agent.status] || STATUS_LABEL.pending;
  const isLoading = (a: string) => actionLoading === `${agent.agent_id}:${a}`;

  return (
    <div className="glass-card p-4 rounded-xl">
      <div className="flex items-start justify-between gap-4 mb-2">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-sm font-semibold text-white">{agent.name}</h3>
            <span
              className="text-xs px-2 py-0.5 rounded-full"
              style={{ background: `${statusInfo.color}20`, color: statusInfo.color }}
            >
              {statusInfo.label}
            </span>
            {agent.is_online ? (
              <span className="text-xs text-text-muted">在线</span>
            ) : (
              <span className="text-xs text-text-muted">离线</span>
            )}
            {agent.price_credits > 0 ? (
              <span className="text-xs" style={{ color: '#fbbf24' }}>
                {agent.price_credits} 积分/次
              </span>
            ) : (
              <span className="text-xs text-text-muted">免费</span>
            )}
          </div>
          {agent.description && (
            <p className="text-xs text-text-secondary mb-1.5">{agent.description}</p>
          )}
          <div className="flex flex-wrap gap-1.5 mb-1">
            {agent.skills.map((s) => (
              <span
                key={s}
                className="text-xs px-2 py-0.5 rounded"
                style={{ background: 'rgba(139,92,246,0.1)', color: 'var(--nebula-light)' }}
              >
                {s}
              </span>
            ))}
            {agent.category && (
              <span
                className="text-xs px-2 py-0.5 rounded"
                style={{ background: 'rgba(255,255,255,0.05)', color: 'var(--text-muted)' }}
              >
                {agent.category}
              </span>
            )}
          </div>
          <div className="text-[11px] text-text-muted font-mono">
            {agent.agent_id} · 调用 {agent.total_calls} 次 · 评分 {agent.rating.toFixed(1)}
          </div>
        </div>
        <div className="flex flex-col gap-1.5">
          {(agent.status === 'pending' || agent.status === 'delisted') && (
            <ActionBtn
              label="提交审核"
              loading={isLoading('submit')}
              onClick={() => onAction(agent.agent_id, 'submit')}
              color="#fbbf24"
            />
          )}
          {agent.status === 'approved' && (
            <ActionBtn
              label="下架"
              loading={isLoading('delist')}
              onClick={() => onAction(agent.agent_id, 'delist')}
              color="#ef4444"
            />
          )}
          {agent.status === 'delisted' && (
            <ActionBtn
              label="重新上架"
              loading={isLoading('relist')}
              onClick={() => onAction(agent.agent_id, 'relist')}
              color="#10b981"
            />
          )}
        </div>
      </div>
    </div>
  );
}

function ActionBtn({
  label,
  loading,
  onClick,
  color,
}: {
  label: string;
  loading: boolean;
  onClick: () => void;
  color: string;
}) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className="px-3 py-1 rounded text-xs font-medium transition-all whitespace-nowrap"
      style={{
        background: `${color}15`,
        color,
        border: `1px solid ${color}30`,
        opacity: loading ? 0.5 : 1,
        cursor: loading ? 'not-allowed' : 'pointer',
      }}
    >
      {loading ? '处理中...' : label}
    </button>
  );
}
