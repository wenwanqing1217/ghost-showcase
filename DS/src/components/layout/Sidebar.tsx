'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import GhostSprite from '@/components/shared/GhostSprite';
import NavIcon from '@/components/shared/NavIcon';
import LogoIcon from '@/components/layout/LogoIcon';

// ── 导航配置 ──
const NAV_GROUPS = [
  {
    label: '平台',
    items: [
      { href: '/', label: '总览', icon: 'overview' as const },
    ],
  },
    {
      label: '操作区',
      items: [
        { href: '/chat', label: '对话', icon: 'chat' as const },
        { href: '/memory', label: '记忆图谱', icon: 'memory' as const },
        { href: '/workflow', label: '工作流', icon: 'workflow' as const },
        { href: '/doubao', label: '豆包记忆桥', icon: 'bridge' as const },
        { href: '/dashboard', label: '运营看板', icon: 'dashboard' as const },
        { href: '/brain', label: '智能大脑', icon: 'brain' as const },
        { href: '/voice', label: '语音', icon: 'voice' as const },
      ],
    },
  {
    label: '生态',
    items: [
      { href: '/ecosystem', label: '生态总览', icon: 'network' as const },
      { href: '/ecosystem/a2a', label: 'A2A 协议', icon: 'a2a' as const },
      { href: '/ecosystem/obsidian', label: '知识图谱', icon: 'obsidian' as const },
      { href: '/ecosystem/strategies', label: '策略供应商', icon: 'dashboard' as const },
      { href: '/ecosystem/tools', label: 'AI 工具', icon: 'tools' as const },
      { href: '/ecosystem/workbench', label: '个人工作台', icon: 'workbench' as const },
      { href: '/social', label: '社交', icon: 'social' as const },
      { href: '/demo', label: '演示', icon: 'overview' as const },
    ],
  },
  {
    label: '管理',
    items: [
      { href: '/products', label: '商品管理', icon: 'products' as const },
      { href: '/orders', label: '订单管理', icon: 'orders' as const },
      { href: '/settings', label: '设置', icon: 'settings' as const },
    ],
  },
];

// ── 接口 ──
interface IdentityStatus {
  connected: boolean;
  did?: string;
  env: string;
}

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [identity, setIdentity] = useState<IdentityStatus>({
    connected: false,
    env: 'development',
  });

  // 检查 Alpha-ID 连接状态
  useEffect(() => {
    const checkIdentity = async () => {
      try {
        const res = await fetch('/api/v1/human/identity', {
          credentials: 'include',
        });
        if (res.ok) {
          const data = await res.json();
          setIdentity({
            connected: true,
            did: data.data?.did || data.did,
            env: process.env.NODE_ENV || 'development',
          });
        }
      } catch {
        // 未连接，保持默认状态
      }
    };

    checkIdentity();
    const interval = setInterval(checkIdentity, 30000); // 30 秒检查一次
    return () => clearInterval(interval);
  }, []);

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/';
    return pathname === href || pathname.startsWith(href + '/');
  };

  const handleNavClick = (e: React.MouseEvent, href: string) => {
    // 对于外部链接或需要特殊处理的导航
    if (href.startsWith('http')) {
      e.preventDefault();
      window.open(href, '_blank');
    }
  };

  return (
    <aside className="sidebar">
      {/* 品牌 */}
      <div className="sidebar-brand">
        <div className="flex items-center gap-2.5">
          <LogoIcon size={32} />
          <div>
            <div className="text-sm font-bold text-white tracking-tight">Ghost Platform</div>
            <div className="text-[10px] text-text-muted font-mono">Web4.0 · v2.0</div>
          </div>
        </div>
      </div>

      {/* 导航分组 */}
      <nav className="flex-1 overflow-y-auto py-3">
        {NAV_GROUPS.map((group) => (
          <div key={group.label} className="mb-1">
            <div className="sidebar-section-label px-4">{group.label}</div>
            {group.items.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={(e) => handleNavClick(e, item.href)}
                className={`flex items-center gap-2.5 px-4 py-2 mx-2 rounded-lg text-sm transition-all duration-150 ${
                  isActive(item.href)
                    ? 'bg-nebula/10 text-nebula-300 border border-nebula/20'
                    : 'text-text-secondary hover:text-white hover:bg-white/5'
                }`}
              >
                <NavIcon type={item.icon} active={isActive(item.href)} />
                <span className="font-medium">{item.label}</span>
              </Link>
            ))}
          </div>
        ))}
      </nav>

      {/* 身份状态 */}
      <div className="p-4 border-t border-ghost-border">
        <div className="glass-card p-3 rounded-lg">
          <div className="flex items-center gap-3 mb-2">
            <GhostSprite size={36} mood="idle" />
            <div className="flex-1">
              <div className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>
                {identity.connected ? 'Alpha-ID 已连接' : 'Alpha-ID 未连接'}
              </div>
              {identity.did && (
                <div className="text-[10px] font-mono mt-0.5" style={{ color: 'var(--nebula-light)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {identity.did.slice(0, 28)}...
                </div>
              )}
              <div className="text-[10px] mt-0.5" style={{ color: 'var(--text-muted)' }}>
                {identity.env}
              </div>
            </div>
          </div>
          {!identity.connected && (
            <Link
              href="/register"
              className="block w-full text-center py-1.5 rounded-lg text-xs font-medium transition-all"
              style={{
                background: 'rgba(139,92,246,0.1)',
                color: 'var(--nebula-light)',
                border: '1px solid rgba(139,92,246,0.15)',
              }}
            >
              获取 Alpha-ID
            </Link>
          )}
        </div>
      </div>
    </aside>
  );
}
