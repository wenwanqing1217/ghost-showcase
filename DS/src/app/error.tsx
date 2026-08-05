'use client';

/**
 * 全局错误边界（Next.js App Router error.tsx 约定）
 * 兜住页面级运行时错误，避免整页白屏；提供"重试"入口。
 */
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 16,
      padding: 32,
      background: 'var(--bg, #0a0a14)',
      color: 'var(--text, #eee)',
      textAlign: 'center',
      fontFamily: 'var(--font-sans, system-ui, sans-serif)',
    }}>
      <div style={{ fontSize: 48 }}>💥</div>
      <h1 style={{ margin: 0, fontSize: 20 }}>页面出了点问题</h1>
      <p style={{ opacity: 0.7, fontSize: 14, maxWidth: 420, wordBreak: 'break-all' }}>
        {error.message || '发生未知错误'}
      </p>
      <button
        onClick={reset}
        style={{
          padding: '10px 24px',
          borderRadius: 8,
          border: '1px solid rgba(255,255,255,0.2)',
          background: 'rgba(255,255,255,0.08)',
          color: 'inherit',
          cursor: 'pointer',
          fontSize: 14,
        }}
      >
        重试
      </button>
    </div>
  );
}
