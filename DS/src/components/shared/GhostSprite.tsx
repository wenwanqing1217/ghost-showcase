'use client';

import { useState, useCallback } from 'react';

/**
 * GhostSprite — 白色幽灵小精灵
 *
 * 还原自 Alpha-ID 官网 ghost.html 设计。
 * 默认使用纯 CSS 渲染白色幽灵（半透明身体、大眼睛、腮红、光环、浮动节点）。
 * 传入 `src` 后自动切换为自定义图片。
 *
 * @example
 *   <GhostSprite size={48} />                        // 默认 idle
 *   <GhostSprite size={48} mood="happy" />            // 开心旋转
 *   <GhostSprite size={48} mood="sleeping" />         // 闭眼睡觉
 *   <GhostSprite size={48} src="/custom.png" />       // 自定义图片
 */
interface GhostSpriteProps {
  size?: number;
  className?: string;
  src?: string;
  alt?: string;
  mood?: 'idle' | 'happy' | 'sleeping';
}

const MOOD_CLASS: Record<string, string> = {
  idle: '',
  happy: 'ghost-mood-happy',
  sleeping: 'ghost-mood-sleeping',
};

export default function GhostSprite({ size = 48, className = '', src, alt = 'Ghost', mood = 'idle' }: GhostSpriteProps) {
  const [hovered, setHovered] = useState(false);

  const handleMouseEnter = useCallback(() => setHovered(true), []);
  const handleMouseLeave = useCallback(() => setHovered(false), []);

  // ── 自定义图片模式 ──
  if (src) {
    return (
      <span
        className={`inline-flex items-center justify-center ${className}`}
        style={{
          width: size, height: size,
          flexShrink: 0,
          position: 'relative',
          transition: 'transform 0.4s ease',
          transform: hovered ? 'scale(1.1)' : 'scale(1)',
        }}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        {/* 柔光背景 */}
        <span
          className="absolute rounded-full"
          style={{
            width: size * 1.3, height: size * 1.3,
            background: 'radial-gradient(circle, rgba(139,92,246,0.25) 0%, rgba(56,189,248,0.08) 50%, transparent 70%)',
            filter: 'blur(4px)',
            transition: 'transform 0.6s ease, opacity 0.6s ease',
            transform: hovered ? 'scale(1.25)' : 'scale(1)',
            opacity: hovered ? 1 : 0.7,
          }}
        />
        <img
          src={src}
          alt={alt}
          width={size}
          height={size}
          style={{
            width: size, height: size,
            objectFit: 'contain',
            position: 'relative',
            zIndex: 1,
            filter: 'brightness(1.1) drop-shadow(0 0 6px rgba(139,92,246,0.35))',
            transition: 'transform 0.4s ease, filter 0.4s ease',
            ...(hovered ? { filter: 'brightness(1.2) drop-shadow(0 0 12px rgba(139,92,246,0.5))' } : {}),
          }}
        />
      </span>
    );
  }

  // ── 纯 CSS 白色幽灵小精灵 ──
  const bodyInset = size * 0.09;
  const moodClass = MOOD_CLASS[mood] || '';

  return (
    <span
      className={`ghost-sprite ${moodClass} ${className}`}
      style={{
        '--s': `${size}px`,
        width: size, height: size,
        flexShrink: 0,
        position: 'relative',
        display: 'inline-block',
        transition: 'transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)',
        transform: hovered ? 'translateY(-4px) scale(1.08)' : 'translateY(0) scale(1)',
      } as React.CSSProperties}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {/* 外层光晕 */}
      <span className="ghost-aura" />

      {/* 身体 */}
      <span className="ghost-body" />

      {/* 顶部光环 — 白色天使圈 */}
      <span className="ghost-halo" />

      {/* 悬浮小幽灵 */}
      <span className="ghost-float-ghost" />

      {/* 脸部 */}
      <span className="ghost-face">
        {/* 左眼 */}
        <span className="ghost-eye ghost-eye-left">
          <span className="ghost-eye-pupil" />
        </span>
        {/* 右眼 */}
        <span className="ghost-eye ghost-eye-right">
          <span className="ghost-eye-pupil" />
        </span>
        {/* 左腮红 */}
        <span className="ghost-cheek ghost-cheek-left" />
        {/* 右腮红 */}
        <span className="ghost-cheek ghost-cheek-right" />
        {/* 嘴巴 */}
        <span className="ghost-mouth" />
      </span>

      {/* 浮动节点 */}
      <span className="ghost-node n1" />
      <span className="ghost-node n2" />
      <span className="ghost-node n3" />
      <span className="ghost-node n4" />
      <span className="ghost-node n5" />
      <span className="ghost-node n6" />

      {/* 底部 Alpha-ID */}
      <span className="ghost-aid">Alpha-ID</span>
    </span>
  );
}
