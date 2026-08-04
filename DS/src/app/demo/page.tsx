'use client';

import { useState } from 'react';
import GlassCard from '@/components/shared/GlassCard';
import Tag from '@/components/shared/Tag';

export default function DemoPage() {
  const [step, setStep] = useState(1);
  const [generating, setGenerating] = useState(false);
  const [did, setDid] = useState<string>('');
  const [pubkey, setPubkey] = useState<string>('');

  const startDemo = () => {
    setGenerating(true);
    setStep(2);

    // 模拟 DID 生成过程
    setTimeout(() => {
      const mockDid = 'did:aid:' + Array.from({ length: 36 }, () =>
        'abcdefghijklmnopqrstuvwxyz0123456789'[Math.floor(Math.random() * 36)]
      ).join('').slice(0, 36);
      const mockPubkey = '0x' + Array.from({ length: 64 }, () =>
        '0123456789abcdef'[Math.floor(Math.random() * 16)]
      ).join('');

      setDid(mockDid);
      setPubkey(mockPubkey);
      setGenerating(false);
      setStep(3);
    }, 2000);
  };

  const resetDemo = () => {
    setStep(1);
    setDid('');
    setPubkey('');
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
            点击下方按钮，体验 DID 生成的全过程。这只是一个演示，你的真实身份将在本地安全生成。
          </p>
        </div>

        <GlassCard glow className="p-8 md:p-10 relative overflow-hidden">
          {/* 初始状态 */}
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
                className="btn-primary px-8 py-3 rounded-2xl text-white font-semibold text-sm"
              >
                开始演示
              </button>
            </div>
          )}

          {/* 生成中状态 */}
          {step === 2 && (
            <div className="text-center">
              <div className="mb-8">
                <div className="w-20 h-20 mx-auto rounded-full border-4 border-violet-500/30 border-t-violet-500 animate-spin mb-6" />
                <h3 className="text-xl font-bold text-white mb-2">身份生成中...</h3>
                <p className="text-text-secondary text-sm">正在生成 Ed25519 密钥对</p>
              </div>
              <div className="space-y-2 text-left font-mono text-sm max-w-md mx-auto">
                <div className="text-text-muted">→ 生成随机种子...</div>
                <div className="text-text-muted">→ 推导 Ed25519 密钥对...</div>
                <div className="text-text-muted">→ 计算公钥哈希...</div>
              </div>
            </div>
          )}

          {/* 生成完成状态 */}
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
              <div className="code-block rounded-2xl p-5 mb-4">
                <div className="text-xs text-text-muted font-mono mb-2">DID</div>
                <div className="text-lg font-mono text-nebula-300 break-all">{did}</div>
              </div>

              {/* 签名公钥 */}
              <div className="code-block rounded-2xl p-5 mb-4">
                <div className="text-xs text-text-muted font-mono mb-2">签名公钥</div>
                <div className="text-sm font-mono text-cosmic-300 break-all">{pubkey}</div>
              </div>

              {/* 状态标签 */}
              <div className="flex flex-wrap justify-center gap-3 mt-6">
                <Tag>已验证</Tag>
                <Tag variant="subtle">本地存储</Tag>
                <Tag variant="subtle">私钥加密</Tag>
              </div>

              <div className="mt-6 pt-6 border-t border-white/10 text-center">
                <button
                  onClick={resetDemo}
                  className="text-sm text-text-muted hover:text-white transition"
                >
                  重新演示
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
