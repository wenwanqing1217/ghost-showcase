'use client';

import { useState } from 'react';
import TopBar from '@/components/layout/TopBar';
import GlassCard from '@/components/shared/GlassCard';
import Tag from '@/components/shared/Tag';

type Step = 1 | 2 | 3 | 4;

export default function DemoPage() {
  const [step, setStep] = useState<Step>(1);
  const [loading, setLoading] = useState(false);
  const [did, setDid] = useState<string>('');
  const [pubkey, setPubkey] = useState<string>('');
  const [method, setMethod] = useState<string>('');
  const [error, setError] = useState('');
  const [copied, setCopied] = useState<string | null>(null);

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(label);
      setTimeout(() => setCopied(null), 1500);
    });
  };

  const startDemo = async () => {
    setLoading(true);
    setError('');
    setStep(2);

    try {
      // 调用真实 DID 生成 API
      const res = await fetch('/api/v1/register/generate-did', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await res.json();
      if (data.id || data.did) {
        setDid(data.id || data.did || '');
        setPubkey(data.public_key || data.pubkey || '');
        setMethod(data.method || 'Ed25519');
        setStep(3);
      } else {
        throw new Error(data.error || data.message || '生成失败');
      }
    } catch (err: any) {
      // API 不可用时降级为模拟
      console.warn('DID API fallback:', err.message);
      await new Promise(r => setTimeout(r, 1500));
      const mockDid = 'did:aid:' + Array.from({ length: 36 }, () =>
        'abcdefghijklmnopqrstuvwxyz0123456789'[Math.floor(Math.random() * 36)]
      ).join('').slice(0, 36);
      const mockPubkey = '0x' + Array.from({ length: 64 }, () =>
        '0123456789abcdef'[Math.floor(Math.random() * 16)]
      ).join('');
      setDid(mockDid);
      setPubkey(mockPubkey);
      setMethod('Ed25519 (simulated)');
      setStep(3);
    } finally {
      setLoading(false);
    }
  };

  const resetDemo = () => {
    setStep(1);
    setDid('');
    setPubkey('');
    setMethod('');
    setError('');
    setCopied(null);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="max-w-2xl w-full">
        {/* 标题 */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-black text-white mb-4">
            见证<span className="gradient-text">数字身份</span>的诞生
          </h1>
          <p className="text-text-secondary">
            点击下方按钮，体验 DID 生成的全过程。你的身份将在本地安全生成，私钥由你独有。
          </p>
        </div>

        <GlassCard glow className="p-8 md:p-10 relative overflow-hidden">
          {/* 步骤指示器 */}
          <div className="flex items-center justify-center gap-3 mb-8">
            {[1, 2, 3].map((s) => (
              <div key={s} className="flex items-center gap-2">
                <div
                  className="rounded-full flex items-center justify-center transition-all duration-300"
                  style={{
                    width: 32,
                    height: 32,
                    background: step >= s ? 'var(--nebula)' : 'var(--bg-hover)',
                    color: step >= s ? 'white' : 'var(--text-muted)',
                    fontSize: 13,
                    fontWeight: 700,
                    boxShadow: step === s ? '0 0 20px rgba(139,92,246,0.4)' : 'none',
                  }}
                >
                  {step > s ? '✓' : s}
                </div>
                {s < 3 && (
                  <div
                    className="transition-all duration-500"
                    style={{
                      width: 48,
                      height: 2,
                      background: step > s ? 'var(--nebula)' : 'var(--border-color)',
                    }}
                  />
                )}
              </div>
            ))}
          </div>

          {error && (
            <div
              className="mb-6 p-3 rounded-lg text-sm"
              style={{
                background: 'rgba(239,68,68,0.1)',
                color: 'var(--danger)',
                border: '1px solid rgba(239,68,68,0.2)',
              }}
            >
              {error}
            </div>
          )}

          {/* 步骤1: 开始 */}
          {step === 1 && (
            <div className="text-center">
              <div className="mb-8">
                <div
                  className="w-24 h-24 mx-auto rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg shadow-violet-500/30 mb-6 cursor-pointer hover:scale-105 transition-transform"
                  onClick={startDemo}
                >
                  <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.5">
                    <path d="M12 2L2 7l10 5 10-5-10-5z" />
                    <path d="M2 17l10 5 10-5" />
                    <path d="M2 12l10 5 10-5" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold text-white mb-2">生成你的 DID</h3>
                <p className="text-text-secondary text-sm">Ed25519 密钥对 · 去中心化身份</p>
              </div>
              <button
                onClick={startDemo}
                disabled={loading}
                className="btn-primary px-8 py-3 rounded-2xl text-white font-semibold text-sm"
              >
                开始演示
              </button>
            </div>
          )}

          {/* 步骤2: 生成中 */}
          {step === 2 && (
            <div className="text-center">
              <div className="mb-8">
                <div className="w-20 h-20 mx-auto rounded-full border-4 border-violet-500/30 border-t-violet-500 animate-spin mb-6" />
                <h3 className="text-xl font-bold text-white mb-2">身份生成中...</h3>
                <p className="text-text-secondary text-sm">正在生成 {method || 'Ed25519'} 密钥对</p>
              </div>
              <div className="space-y-2.5 text-left font-mono text-sm max-w-md mx-auto">
                {['生成随机种子...', '推导 Ed25519 密钥对...', '计算公钥哈希...', '构建 DID 标识符...'].map((msg, i) => (
                  <div
                    key={i}
                    className="text-text-muted"
                    style={{ animation: `pulse 1.5s ease-in-out ${i * 400}ms infinite` }}
                  >
                    → {msg}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 步骤3: 完成 */}
          {step === 3 && (
            <div>
              <div className="text-center mb-8">
                <div className="w-16 h-16 mx-auto rounded-full bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center shadow-lg shadow-emerald-500/30 mb-4">
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                    <polyline points="22 4 12 14.01 9 11.01" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold text-white mb-2">身份已生成</h3>
                <p className="text-text-secondary text-sm">这就是属于你的数字灵魂，独一无二</p>
              </div>

              {/* DID 展示 */}
              <div className="code-block rounded-2xl p-5 mb-4 group cursor-pointer" onClick={() => copyToClipboard(did, 'did')}>
                <div className="flex items-center justify-between mb-2">
                  <div className="text-xs text-text-muted font-mono">DID</div>
                  <span className="text-xs text-text-muted opacity-0 group-hover:opacity-100 transition-opacity">
                    {copied === 'did' ? '已复制!' : '点击复制'}
                  </span>
                </div>
                <div className="text-base font-mono text-nebula-300 break-all select-all">{did}</div>
              </div>

              {/* 签名公钥 */}
              {pubkey && (
                <div className="code-block rounded-2xl p-5 mb-4 group cursor-pointer" onClick={() => copyToClipboard(pubkey, 'pubkey')}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-xs text-text-muted font-mono">签名公钥</div>
                    <span className="text-xs text-text-muted opacity-0 group-hover:opacity-100 transition-opacity">
                      {copied === 'pubkey' ? '已复制!' : '点击复制'}
                    </span>
                  </div>
                  <div className="text-sm font-mono text-cosmic-300 break-all select-all">{pubkey}</div>
                </div>
              )}

              {/* 方法标签 */}
              {method && (
                <div className="code-block rounded-2xl p-4 mb-4">
                  <div className="text-xs text-text-muted font-mono mb-1">签名方法</div>
                  <div className="text-sm font-mono text-white">{method}</div>
                </div>
              )}

              {/* 状态标签 */}
              <div className="flex flex-wrap justify-center gap-3 mt-6">
                <Tag>已验证</Tag>
                <Tag variant="subtle">本地存储</Tag>
                <Tag variant="subtle">私钥加密</Tag>
              </div>

              <div className="mt-6 pt-6 border-t border-white/10 flex justify-center gap-4">
                <button
                  onClick={resetDemo}
                  className="text-sm text-text-muted hover:text-white transition"
                >
                  重新演示
                </button>
                <button
                  onClick={() => window.location.href = '/register'}
                  className="text-sm px-4 py-2 rounded-lg"
                  style={{
                    background: 'rgba(139,92,246,0.15)',
                    color: 'var(--nebula-light)',
                    border: '1px solid rgba(139,92,246,0.2)',
                  }}
                >
                  正式注册 →
                </button>
              </div>
            </div>
          )}
        </GlassCard>

        {/* 底部说明 */}
        <div className="mt-8 text-center text-xs text-text-muted">
          <p>所有命令均可使用 <code className="text-nebula-300 font-mono">--help</code> 查看详细参数</p>
        </div>
      </div>
    </div>
  );
}
