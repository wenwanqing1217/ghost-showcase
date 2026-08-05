'use client';

import { useState, useCallback } from 'react';

/**
 * LogoIcon — 品牌图标
 *
 * 还原自 Alpha-ID 官网右上角 logo-sprite：
 * 星体核心 + 高光点 + 半弧光带 + 双层旋转光环 + 环绕粒子
 */
export default function LogoIcon({ size = 32 }: { size?: number }) {
  const [hovered, setHovered] = useState(false);

  const handleMouseEnter = useCallback(() => setHovered(true), []);
  const handleMouseLeave = useCallback(() => setHovered(false), []);

  return (
    <span
      className="relative inline-flex cursor-grab active:cursor-grabbing"
      style={{
        width: size,
        height: size,
        flexShrink: 0,
        transform: hovered ? 'scale(1.08)' : 'scale(1)',
        transition: 'transform 0.4s ease',
      }}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {/* 最内层星体核心 */}
      <span
        className="absolute inset-0 rounded-full"
        style={{
          background: 'linear-gradient(135deg, #a78bfa 0%, #8b5cf6 50%, #6366f1 100%)',
          boxShadow: hovered
            ? '0 0 12px rgba(139,92,246,0.5), 0 0 24px rgba(139,92,246,0.2)'
            : '0 0 6px rgba(139,92,246,0.3), 0 0 12px rgba(139,92,246,0.1)',
          transition: 'box-shadow 0.4s ease',
        }}
      >
        {/* 内层高光 */}
        <span
          className="absolute rounded-full"
          style={{
            inset: size * 0.18,
            background: 'linear-gradient(135deg, rgba(255,255,255,0.3) 0%, transparent 60%)',
          }}
        />
        {/* 星点 1 */}
        <span
          className="absolute rounded-full"
          style={{
            top: size * 0.22,
            left: size * 0.22,
            width: size * 0.1,
            height: size * 0.1,
            background: 'rgba(255,255,255,0.75)',
            boxShadow: `0 0 ${size * 0.06}px rgba(255,255,255,0.5)`,
          }}
        />
        {/* 星点 2 */}
        <span
          className="absolute rounded-full"
          style={{
            top: size * 0.42,
            left: size * 0.48,
            width: size * 0.05,
            height: size * 0.05,
            background: 'rgba(255,255,255,0.45)',
          }}
        />
      </span>

      {/* 半弧光带 — 横切效果 */}
      <span
        className="absolute inset-0 rounded-full"
        style={{
          background: 'linear-gradient(to bottom, rgba(245,158,11,0.3) 0%, rgba(251,191,36,0.1) 40%, transparent 70%)',
        }}
      />
      {/* 横切金线 */}
      <span
        className="absolute rounded-full"
        style={{
          top: '50%',
          left: 0,
          right: 0,
          height: size * 0.03,
          background: 'linear-gradient(to right, transparent, rgba(245,158,11,0.5) 50%, transparent)',
          transform: 'translateY(-50%)',
        }}
      />

      {/* 外层双层光环 — 反向旋转 */}
      <span
        className="absolute rounded-full"
        style={{
          inset: `-${size * 0.1}px`,
          borderTop: `${size * 0.035}px solid rgba(245,158,11,0.35)`,
          borderLeft: `${size * 0.035}px solid rgba(245,158,11,0.35)`,
          borderRight: `${size * 0.035}px solid rgba(245,158,11,0.35)`,
          borderBottom: 'none',
        }}
      />
      <span
        className="absolute rounded-full"
        style={{
          inset: `-${size * 0.16}px`,
          borderTop: `${size * 0.025}px solid rgba(245,158,11,0.18)`,
          borderLeft: `${size * 0.025}px solid rgba(245,158,11,0.18)`,
          borderRight: `${size * 0.025}px solid rgba(245,158,11,0.18)`,
          borderBottom: 'none',
        }}
      />

      {/* 金色光晕 */}
      <span
        className="absolute rounded-full"
        style={{
          inset: `-${size * 0.06}px`,
          background: 'linear-gradient(to top, transparent, rgba(245,158,11,0.06) 50%, rgba(251,191,36,0.08))',
        }}
      />

      {/* 环绕粒子 */}
      <span
        className="absolute rounded-full logo-pulse"
        style={{
          top: `-${size * 0.04}px`,
          right: `-${size * 0.02}px`,
          width: size * 0.13,
          height: size * 0.13,
          background: '#fbbf24',
          boxShadow: `0 0 ${size * 0.08}px rgba(251,191,36,0.6)`,
        }}
      />
      <span
        className="absolute rounded-full logo-pulse"
        style={{
          bottom: `-${size * 0.01}px`,
          left: `-${size * 0.01}px`,
          width: size * 0.09,
          height: size * 0.09,
          background: '#a78bfa',
          boxShadow: `0 0 ${size * 0.06}px rgba(167,139,250,0.5)`,
          animationDelay: '0.6s',
        }}
      />
      <span
        className="absolute rounded-full logo-pulse"
        style={{
          top: '50%',
          right: `-${size * 0.07}px`,
          width: size * 0.05,
          height: size * 0.05,
          background: 'rgba(255,255,255,0.75)',
          animationDelay: '1.2s',
        }}
      />
    </span>
  );
}
