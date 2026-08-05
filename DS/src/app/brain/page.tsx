'use client';

import { useEffect, useState } from 'react';
import TopBar from '@/components/layout/TopBar';
import AuthGuard from '@/components/layout/AuthGuard';
import { humanApi } from '@/lib/api';

interface BrainStatus {
  ok: boolean;
  data?: {
    alpha_id: string;
    state: string;
    settings: Record<string, unknown>;
  };
}

interface BrainChatResponse {
  success: boolean;
  error?: string;
  detail?: string;
  data?: {
    alpha_id: string;
    reply: string;
    brain_state: string;
  };
}

export default function BrainPage() {
  const [status, setStatus] = useState<BrainStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [awaking, setAwaking] = useState(false);
  const [message, setMessage] = useState('');
  const [reply, setReply] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [error, setError] = useState('');
  const [alphaId, setAlphaId] = useState<string>('');

  // 获取真实身份（替代硬编码 'Alpha-001'，实现用户身份隔离）
  useEffect(() => {
    humanApi
      .getIdentity()
      .then((data: unknown) => {
        const d = (data as { data?: { alpha_id?: string }; alpha_id?: string })?.data || (data as { alpha_id?: string });
        if (d?.alpha_id) setAlphaId(d.alpha_id);
      })
      .catch(() => {
        // AuthGuard 会处理未登录重定向，这里静默
      });
  }, []);

  useEffect(() => {
    loadStatus();
  }, []);

  async function loadStatus() {
    setLoading(true);
    setError('');
    try {
      const res = await fetch('/api/v1/human/brain/status');
      const data = await res.json();
      if (res.ok) {
        setStatus({ ok: true, data: data.data || data });
      } else {
        setStatus({ ok: false });
        setError(data.error || data.detail || '获取大脑状态失败');
      }
    } catch {
      setStatus({ ok: false });
      setError('获取大脑状态失败');
    } finally {
      setLoading(false);
    }
  }

  async function awakeBrain() {
    if (!alphaId) {
      setError('未获取到身份信息，请先登录');
      return;
    }
    setAwaking(true);
    setError('');
    try {
      const res = await fetch('/api/v1/human/brain/awake', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ alpha_id: alphaId }),
      });
      const data = await res.json();
      if (res.ok) {
        setStatus({ ok: true, data: data.data || data });
      } else {
        setError(data.error || data.detail || '唤醒大脑失败');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : '唤醒大脑失败');
    } finally {
      setAwaking(false);
    }
  }

  async function sendBrainChat() {
    if (!message.trim()) return;
    if (!alphaId) {
      setError('未获取到身份信息，请先登录');
      return;
    }
    setChatLoading(true);
    setError('');
    setReply('');
    try {
      const res = await fetch('/api/v1/human/brain/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message.trim(), alpha_id: alphaId }),
      });
      const data: BrainChatResponse = await res.json();
      if (res.ok && data.data) {
        setReply(data.data.reply);
        setStatus({ ok: true, data: { alpha_id: data.data.alpha_id, state: data.data.brain_state, settings: {} } });
      } else {
        setError(data.error || data.detail || '大脑回复失败');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : '大脑回复失败');
    } finally {
      setChatLoading(false);
    }
  }

  const stateColor = status?.data?.state === 'active' ? '#10b981' : status?.data?.state === 'sleep' ? '#f59e0b' : '#6b7280';

  return (
    <AuthGuard>
      <TopBar title="智能大脑" subtitle="GhostBrain — TwinBrain 核心" />
      <div className="p-6">
        <div className="max-w-3xl mx-auto">
          {/* 大脑状态卡片 */}
          <div className="card mb-6" style={{ padding: 24 }}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ background: stateColor, boxShadow: `0 0 12px ${stateColor}` }}
                />
                <div>
                  <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)' }}>
                    {loading ? '加载中...' : status?.ok ? '大脑在线' : '大脑离线'}
                  </h3>
                  {status?.data && (
                    <div className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                      Alpha-ID: {status.data.alpha_id} · 状态: {status.data.state}
                    </div>
                  )}
                </div>
              </div>
              <button
                onClick={awakeBrain}
                disabled={awaking}
                className="px-4 py-2 rounded-xl text-sm font-medium"
                style={{
                  background: 'rgba(139,92,246,0.15)',
                  color: 'var(--nebula-light)',
                  border: '1px solid rgba(139,92,246,0.2)',
                  cursor: awaking ? 'not-allowed' : 'pointer',
                  opacity: awaking ? 0.6 : 1,
                }}
              >
                {awaking ? '唤醒中...' : '唤醒大脑'}
              </button>
            </div>
          </div>

          {/* 大脑对话 */}
          <div className="card" style={{ padding: 24 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 16 }}>
              与大脑对话
            </h3>

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

            {reply && (
              <div
                className="mb-4 p-4 rounded-xl text-sm"
                style={{
                  background: 'rgba(139,92,246,0.08)',
                  color: 'var(--text-primary)',
                  border: '1px solid rgba(139,92,246,0.15)',
                  whiteSpace: 'pre-wrap',
                }}
              >
                {reply}
              </div>
            )}

            <div className="flex gap-2">
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="输入消息与大脑对话..."
                className="flex-1 rounded-xl px-4 py-2.5 text-sm"
                style={{
                  background: 'var(--bg-secondary)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border-color)',
                }}
                onKeyDown={(e) => e.key === 'Enter' && !chatLoading && sendBrainChat()}
              />
              <button
                onClick={sendBrainChat}
                disabled={chatLoading || !message.trim()}
                className="px-4 py-2.5 rounded-xl text-sm font-medium"
                style={{
                  background: 'rgba(139,92,246,0.15)',
                  color: 'var(--nebula-light)',
                  border: '1px solid rgba(139,92,246,0.2)',
                  cursor: (chatLoading || !message.trim()) ? 'not-allowed' : 'pointer',
                  opacity: (chatLoading || !message.trim()) ? 0.6 : 1,
                }}
              >
                {chatLoading ? '思考中...' : '发送'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}
