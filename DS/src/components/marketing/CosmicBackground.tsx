'use client';

// ── 纯 CSS 星空背景 ──
// 零 JS 开销，不影响页面导航性能

export default function CosmicBackground({ opacity = 0.6 }: { opacity?: number }) {
  return (
    <div
      className="fixed inset-0 z-0 pointer-events-none overflow-hidden"
      style={{ opacity }}
    >
      {/* 星云光晕 */}
      <div className="absolute" style={{
        top: '15%', left: '20%', width: 500, height: 500,
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(139,92,246,0.06) 0%, transparent 70%)',
        filter: 'blur(40px)',
      }} />
      <div className="absolute" style={{
        bottom: '20%', right: '15%', width: 400, height: 400,
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(56,189,248,0.04) 0%, transparent 70%)',
        filter: 'blur(40px)',
      }} />

      {/* 星星 — CSS 动画 */}
      {Array.from({ length: 40 }).map((_, i) => {
        const size = Math.random() * 2 + 1;
        const top = Math.random() * 100;
        const left = Math.random() * 100;
        const delay = Math.random() * 5;
        const duration = Math.random() * 3 + 2;
        const isBlue = Math.random() > 0.5;
        return (
          <div
            key={i}
            className="absolute rounded-full"
            style={{
              width: size,
              height: size,
              top: `${top}%`,
              left: `${left}%`,
              background: isBlue ? 'rgba(56,189,248,0.6)' : 'rgba(255,255,255,0.5)',
              boxShadow: `0 0 ${size * 2}px ${isBlue ? 'rgba(56,189,248,0.3)' : 'rgba(255,255,255,0.2)'}`,
              animation: `star-twinkle ${duration}s ease-in-out ${delay}s infinite`,
            }}
          />
        );
      })}
    </div>
  );
}
