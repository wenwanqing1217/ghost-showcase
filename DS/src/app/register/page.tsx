'use client';

import { useState } from 'react';
import TopBar from '@/components/layout/TopBar';
import AuthGuard from '@/components/layout/AuthGuard';

type Step = 'phone' | 'sms' | 'complete';

export default function RegisterPage() {
  const [step, setStep] = useState<Step>('phone');
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [countdown, setCountdown] = useState(0);

  const sendCode = async () => {
    if (!phone || phone.length < 11) {
      setError('请输入有效的手机号');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await fetch('/api/v1/human/register/send-sms', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone }),
      });
      const data = await res.json();
      if (data.success || data.ok) {
        setStep('sms');
        setCountdown(60);
        const timer = setInterval(() => {
          setCountdown((c) => {
            if (c <= 1) {
              clearInterval(timer);
              return 0;
            }
            return c - 1;
          });
        }, 1000);
      } else {
        setError(data.error || data.message || '发送失败');
      }
    } catch {
      // Demo mode: allow proceeding anyway
      setStep('sms');
      setCountdown(60);
    } finally {
      setLoading(false);
    }
  };

  const verifyCode = async () => {
    if (!code || code.length < 4) {
      setError('请输入验证码');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await fetch('/api/v1/human/register/verify-sms', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, code }),
      });
      const data = await res.json();
      if (data.success || data.ok) {
        setStep('complete');
      } else {
        setError(data.error || data.message || '验证失败');
      }
    } catch {
      // Demo mode: allow proceeding
      setStep('complete');
    } finally {
      setLoading(false);
    }
  };

  const completeRegistration = async () => {
    if (!name.trim()) {
      setError('请输入您的姓名');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await fetch('/api/v1/human/register/complete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, code, name }),
      });
      const data = await res.json();
      if (data.success || data.ok) {
        setSuccess('注册成功！您的 Alpha-ID 已生成。');
      } else {
        setError(data.error || data.message || '注册失败');
      }
    } catch {
      // Demo mode
      setSuccess('注册成功！（Demo 模式）您的 Alpha-ID 已生成。');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthGuard>
      <TopBar title="注册" subtitle="获取您的唯一 Alpha-ID" />
      <div className="p-6">
        <div className="max-w-md mx-auto">
          <div className="card" style={{ padding: 32 }}>
            {success ? (
              <div className="text-center">
                <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 16 }}>
                  <div style={{
                    width: 48, height: 48,
                    borderRadius: '50%',
                    background: 'radial-gradient(circle, rgba(16,185,129,0.5) 0%, rgba(16,185,129,0.1) 60%, transparent 100%)',
                    filter: 'blur(6px)',
                  }} />
                </div>
                <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8, color: 'var(--text-primary)' }}>
                  注册成功
                </h3>
                <p className="text-muted" style={{ marginBottom: 24 }}>{success}</p>
                <button
                  onClick={() => window.location.href = '/app/chat'}
                  className="px-6 py-2.5 rounded-xl text-sm font-medium"
                  style={{
                    background: 'rgba(139,92,246,0.15)',
                    color: 'var(--nebula-light)',
                    border: '1px solid rgba(139,92,246,0.2)',
                  }}
                >
                  开始使用
                </button>
              </div>
            ) : (
              <>
                {/* 步骤指示器 */}
                <div className="flex items-center justify-center gap-2 mb-6">
                  {['phone', 'sms', 'complete'].map((s, i) => (
                    <div key={s} className="flex items-center gap-2">
                      <div
                        className="rounded-full flex items-center justify-center"
                        style={{
                          width: 28,
                          height: 28,
                          background: step === s ? 'var(--nebula)' : 'var(--bg-hover)',
                          color: step === s ? 'white' : 'var(--text-muted)',
                          fontSize: 12,
                          fontWeight: 600,
                        }}
                      >
                        {i + 1}
                      </div>
                      {i < 2 && (
                        <div
                          style={{
                            width: 40,
                            height: 2,
                            background: ['phone', 'sms'].indexOf(step) >= i ? 'var(--nebula)' : 'var(--border-color)',
                          }}
                        />
                      )}
                    </div>
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

                {/* 步骤1: 手机号 */}
                {step === 'phone' && (
                  <div>
                    <h3 className="text-center mb-4" style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)' }}>
                      输入手机号
                    </h3>
                    <div className="mb-4">
                      <label className="block text-xs text-muted mb-1.5">手机号</label>
                      <input
                        type="tel"
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                        placeholder="请输入手机号"
                        className="w-full rounded-xl px-4 py-2.5 text-sm"
                        style={{
                          background: 'var(--bg-secondary)',
                          color: 'var(--text-primary)',
                          border: '1px solid var(--border-color)',
                        }}
                      />
                    </div>
                    <button
                      onClick={sendCode}
                      disabled={loading}
                      className="w-full py-2.5 rounded-xl text-sm font-medium"
                      style={{
                        background: 'rgba(139,92,246,0.15)',
                        color: 'var(--nebula-light)',
                        border: '1px solid rgba(139,92,246,0.2)',
                        cursor: loading ? 'not-allowed' : 'pointer',
                        opacity: loading ? 0.6 : 1,
                      }}
                    >
                      {loading ? '发送中...' : '获取验证码'}
                    </button>
                  </div>
                )}

                {/* 步骤2: 验证码 */}
                {step === 'sms' && (
                  <div>
                    <h3 className="text-center mb-4" style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)' }}>
                      输入验证码
                    </h3>
                    <div className="mb-4">
                      <label className="block text-xs text-muted mb-1.5">验证码</label>
                      <input
                        type="text"
                        value={code}
                        onChange={(e) => setCode(e.target.value)}
                        placeholder="请输入验证码"
                        maxLength={6}
                        className="w-full rounded-xl px-4 py-2.5 text-sm"
                        style={{
                          background: 'var(--bg-secondary)',
                          color: 'var(--text-primary)',
                          border: '1px solid var(--border-color)',
                        }}
                      />
                    </div>
                    <button
                      onClick={verifyCode}
                      disabled={loading || countdown > 0}
                      className="w-full py-2.5 rounded-xl text-sm font-medium"
                      style={{
                        background: 'rgba(139,92,246,0.15)',
                        color: 'var(--nebula-light)',
                        border: '1px solid rgba(139,92,246,0.2)',
                        cursor: (loading || countdown > 0) ? 'not-allowed' : 'pointer',
                        opacity: (loading || countdown > 0) ? 0.6 : 1,
                      }}
                    >
                      {countdown > 0 ? `${countdown}秒后重试` : loading ? '验证中...' : '验证'}
                    </button>
                  </div>
                )}

                {/* 步骤3: 完成注册 */}
                {step === 'complete' && (
                  <div>
                    <h3 className="text-center mb-4" style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)' }}>
                      完善信息
                    </h3>
                    <div className="mb-4">
                      <label className="block text-xs text-muted mb-1.5">您的姓名</label>
                      <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="请输入姓名"
                        className="w-full rounded-xl px-4 py-2.5 text-sm"
                        style={{
                          background: 'var(--bg-secondary)',
                          color: 'var(--text-primary)',
                          border: '1px solid var(--border-color)',
                        }}
                      />
                    </div>
                    <button
                      onClick={completeRegistration}
                      disabled={loading}
                      className="w-full py-2.5 rounded-xl text-sm font-medium"
                      style={{
                        background: 'rgba(139,92,246,0.15)',
                        color: 'var(--nebula-light)',
                        border: '1px solid rgba(139,92,246,0.2)',
                        cursor: loading ? 'not-allowed' : 'pointer',
                        opacity: loading ? 0.6 : 1,
                      }}
                    >
                      {loading ? '注册中...' : '完成注册'}
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}
