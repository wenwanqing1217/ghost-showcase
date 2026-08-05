'use client';

import { useState, useEffect } from 'react';

interface TopBarProps {
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

export default function TopBar({ title, subtitle, actions }: TopBarProps) {
  const [time, setTime] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTime(
        now.toLocaleTimeString('zh-CN', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        })
      );
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="sticky top-0 z-40 h-[60px] flex items-center justify-between px-6 border-b border-ghost-border bg-ghost-bg/80 backdrop-blur-xl">
      {/* 左侧：标题 */}
      <div className="flex items-center gap-4">
        {title && (
          <div>
            <h1 className="text-base font-semibold text-white">{title}</h1>
            {subtitle && (
              <p className="text-xs text-text-muted">{subtitle}</p>
            )}
          </div>
        )}
      </div>

      {/* 右侧：状态 + 操作 */}
      <div className="flex items-center gap-4">
        {/* 系统时间 */}
        <div className="hidden md:flex items-center gap-2 text-xs text-text-muted font-mono">
          <span className="status-dot green" />
          <span>{time}</span>
        </div>

        {/* 自定义操作区 */}
        {actions && <div className="flex items-center gap-2">{actions}</div>}

        {/* 系统状态 */}
        <div className="hidden md:flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs text-text-secondary">
            <span className="status-dot green" />
            <span>Gateway</span>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-text-secondary">
            <span className="status-dot green" />
            <span>Alpha-ID</span>
          </div>
        </div>
      </div>
    </header>
  );
}
