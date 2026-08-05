'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import GhostSprite from '@/components/shared/GhostSprite';
import LogoIcon from '@/components/layout/LogoIcon';

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [checking, setChecking] = useState(true);
  const router = useRouter();

  // If already authenticated, redirect to chat
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const res = await fetch('/api/v1/human/identity', {
          credentials: 'include',
        });
        if (res.ok) {
          router.push('/chat');
        }
      } catch {
        // Not authenticated, stay on login page
      } finally {
        setChecking(false);
      }
    };

    checkAuth();
  }, [router]);

  const handleLogin = async () => {
    setLoading(true);
    setError('');

    try {
      const res = await fetch('/api/v1/human/register/quick-register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
        credentials: 'include',
      });

      const data = await res.json();

      if (data.success || data.ok) {
        // Quick-register succeeded, redirect to chat
        router.push('/chat');
      } else {
        setError(data.error || data.message || '登录失败，请重试');
      }
    } catch (e) {
      // 不再认证绕过 — 显示错误让用户知道后端不可用
      setError(
        '无法连接登录服务（Gateway 或 Alpha-ID 未运行）。' +
          (e instanceof Error ? ` 详情: ${e.message}` : '')
      );
    } finally {
      setLoading(false);
    }
  };

  // Loading state while checking auth
  if (checking) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-text-secondary text-sm">加载中...</div>
      </div>
    );
  }

  return (
    <div className="relative min-h-screen flex items-center justify-center">
      {/* 背景 */}
      <div
        className="fixed inset-0"
        style={{
          background: 'radial-gradient(ellipse at 50% 30%, rgba(139,92,246,0.08) 0%, transparent 60%)',
        }}
      />

      <div className="relative z-10 w-full max-w-sm px-6">
        {/* 品牌 */}
        <div className="text-center mb-8">
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 16 }}>
            <LogoIcon size={48} />
          </div>
          <div
            className="mb-2"
            style={{
              fontSize: 'clamp(1.5rem, 4vw, 2rem)',
              fontWeight: 800,
              color: 'var(--text-primary)',
              letterSpacing: '-0.02em',
            }}
          >
            Ghost Platform
          </div>
          <p style={{ fontSize: 14, color: 'var(--text-muted)' }}>
            登录以获取您的 Alpha-ID
          </p>
        </div>

        {/* 登录卡片 */}
        <div
          className="card"
          style={{
            padding: 32,
          }}
        >
          {/* 错误提示 */}
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

          {/* 幽灵图标 */}
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 20 }}>
            <GhostSprite size={64} mood="idle" />
          </div>

          <h3
            className="text-center mb-2"
            style={{
              fontSize: 18,
              fontWeight: 600,
              color: 'var(--text-primary)',
            }}
          >
            登录
          </h3>

          <p
            className="text-center mb-6"
            style={{
              fontSize: 13,
              color: 'var(--text-muted)',
              lineHeight: 1.5,
            }}
          >
            点击下方按钮，系统将自动为您创建 Alpha-ID 并登录
          </p>

          <button
            onClick={handleLogin}
            disabled={loading}
            className="w-full py-2.5 rounded-xl text-sm font-medium transition-all"
            style={{
              background: 'rgba(139,92,246,0.15)',
              color: 'var(--nebula-light)',
              border: '1px solid rgba(139,92,246,0.2)',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.6 : 1,
            }}
          >
            {loading ? '登录中...' : '登录'}
          </button>

          <p
            className="text-center mt-4"
            style={{
              fontSize: 11,
              color: 'var(--text-muted)',
            }}
          >
            登录即表示您同意我们的服务条款和隐私政策
          </p>
        </div>
      </div>
    </div>
  );
}
