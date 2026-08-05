'use client';

import { ReactNode } from 'react';

interface TagProps {
  children: ReactNode;
  variant?: 'default' | 'subtle';
  className?: string;
}

export default function Tag({ children, variant = 'default', className = '' }: TagProps) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${className}`}
      style={{
        background: variant === 'subtle' ? 'rgba(255,255,255,0.02)' : 'rgba(139,92,246,0.08)',
        color: variant === 'subtle' ? 'var(--text-muted)' : 'var(--nebula-light)',
        border: `1px solid ${variant === 'subtle' ? 'var(--border-color)' : 'rgba(139,92,246,0.12)'}`,
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: 10,
        letterSpacing: '0.02em',
      }}
    >
      {children}
    </span>
  );
}
