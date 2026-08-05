'use client';

import { ReactNode, CSSProperties } from 'react';

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  glow?: boolean;
  onClick?: () => void;
  style?: React.CSSProperties;
}

export default function GlassCard({ children, className = '', glow = false, onClick, style }: GlassCardProps) {
  const baseClasses = 'glass-card rounded-xl p-5';
  const glowClasses = glow ? 'glow-card' : '';
  const clickableClasses = onClick ? 'cursor-pointer' : '';

  return (
    <div
      className={`${baseClasses} ${glowClasses} ${clickableClasses} ${className}`}
      onClick={onClick}
      style={style}
    >
      {children}
    </div>
  );
}
