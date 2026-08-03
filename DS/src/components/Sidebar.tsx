'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

// 三层架构：展示 → 操作 → 生态
const NAV_GROUPS = [
  {
    label: '平台',
    items: [
      { href: '/', label: '总览', icon: '◫' },
    ],
  },
  {
    label: '操作',
    items: [
      { href: '/dashboard', label: '电商看板', icon: '📊' },
      { href: '/products', label: '商品管理', icon: '⬚' },
      { href: '/orders', label: '订单管理', icon: '☰' },
      { href: '/memory', label: '豆包记忆桥', icon: '💬' },
      { href: '/settings', label: '店铺设置', icon: '⚙' },
    ],
  },
  {
    label: '生态',
    items: [
      { href: '/ecosystem', label: 'Agent 网络', icon: '🕸' },
      { href: '/workbench', label: 'Ghost 工作台', icon: '🔧' },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/';
    return pathname === href || pathname.startsWith(href + '/');
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <h1>Ghost Platform</h1>
        <span>统一平台</span>
      </div>
      <div style={{ padding: '0 16px 12px' }}>
        <a href="http://localhost:8000" target="_blank" rel="noopener noreferrer" style={{ color: '#7dd3fc', fontSize: 12, textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 6 }}>
          🏠 平台首页
        </a>
      </div>
      {NAV_GROUPS.map((group) => (
        <div key={group.label} className="sidebar-section">
          <div className="sidebar-section-label">{group.label}</div>
          <nav className="sidebar-nav">
            {group.items.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`nav-item${isActive(item.href) ? ' active' : ''}`}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            ))}
          </nav>
        </div>
      ))}
      <div style={{ padding: '12px 16px', borderTop: '1px solid var(--border)' }}>
        <span className="text-muted text-sm">
          {process.env.NEXT_PUBLIC_DEMO_MODE === 'true' ? 'Demo 模式' : '已连接'}
        </span>
      </div>
    </aside>
  );
}
