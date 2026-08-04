'use client';

import { useEffect, useState } from 'react';
import TopBar from '@/components/layout/TopBar';
import AuthGuard from '@/components/layout/AuthGuard';

interface VoiceStatus {
  ok: boolean;
  data?: {
    available: boolean;
    has_stt: boolean;
    has_tts: boolean;
    model?: {
      whisper: string;
      tts: string;
    };
    error?: string;
  };
}

export default function VoicePage() {
  const [status, setStatus] = useState<VoiceStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [text, setText] = useState('');
  const [speaking, setSpeaking] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadStatus();
  }, []);

  async function loadStatus() {
    setLoading(true);
    setError('');
    try {
      const res = await fetch('/api/v1/human/voice/status');
      const data = await res.json();
      if (res.ok) {
        setStatus({ ok: true, data: data.data || data });
      } else {
        setStatus({ ok: false, data });
        setError(data.error || data.detail || '获取语音状态失败');
      }
    } catch {
      setStatus({ ok: false });
      setError('获取语音状态失败');
    } finally {
      setLoading(false);
    }
  }

  async function speakText() {
    if (!text.trim() || speaking) return;
    setSpeaking(true);
    setError('');
    try {
      const res = await fetch('/api/v1/human/voice/speak', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text.trim() }),
      });
      const data = await res.json();
      if (res.ok && data.ok) {
        setText('');
      } else {
        setError(data.error || data.message || '语音合成失败');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : '语音合成失败');
    } finally {
      setSpeaking(false);
    }
  }

  const available = status?.data?.available;
  const hasStt = status?.data?.has_stt;
  const hasTts = status?.data?.has_tts;

  return (
    <AuthGuard>
      <TopBar title="语音" subtitle="GhostVoice — Whisper STT + Coqui TTS" />
      <div className="p-6">
        <div className="max-w-3xl mx-auto">
          {/* 语音状态卡片 */}
          <div className="card mb-6" style={{ padding: 24 }}>
            <div className="flex items-center gap-4">
              <div
                className="w-3 h-3 rounded-full"
                style={{
                  background: available ? '#10b981' : '#6b7280',
                  boxShadow: available ? '0 0 12px #10b981' : 'none',
                }}
              />
              <div>
                <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)' }}>
                  {loading ? '加载中...' : available ? '语音引擎就绪' : '语音引擎不可用'}
                </h3>
                <div className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                  STT (Whisper): {hasStt ? '✅ 可用' : '❌ 不可用'}
                  {' · '}
                  TTS (Coqui): {hasTts ? '✅ 可用' : '❌ 不可用'}
                  {status?.data?.model && (
                    <> · 模型: {status.data.model.whisper} / {status.data.model.tts}</>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* 语音合成 */}
          <div className="card" style={{ padding: 24 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 16 }}>
              语音合成（TTS）
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

            {!available && (
              <div
                className="mb-4 p-3 rounded-lg text-sm"
                style={{
                  background: 'rgba(245,158,11,0.1)',
                  color: '#f59e0b',
                  border: '1px solid rgba(245,158,11,0.2)',
                }}
              >
                语音引擎不可用。请安装 faster-whisper 和 Coqui TTS。
              </div>
            )}

            <div className="flex gap-2">
              <input
                type="text"
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="输入要合成的文本..."
                className="flex-1 rounded-xl px-4 py-2.5 text-sm"
                style={{
                  background: 'var(--bg-secondary)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border-color)',
                }}
                onKeyDown={(e) => e.key === 'Enter' && !speaking && speakText()}
              />
              <button
                onClick={speakText}
                disabled={speaking || !text.trim() || !available}
                className="px-4 py-2.5 rounded-xl text-sm font-medium"
                style={{
                  background: 'rgba(139,92,246,0.15)',
                  color: 'var(--nebula-light)',
                  border: '1px solid rgba(139,92,246,0.2)',
                  cursor: (speaking || !text.trim() || !available) ? 'not-allowed' : 'pointer',
                  opacity: (speaking || !text.trim() || !available) ? 0.6 : 1,
                }}
              >
                {speaking ? '合成中...' : '合成语音'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}
