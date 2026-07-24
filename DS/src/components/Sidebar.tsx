'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const NAV_ITEMS = [
  { href: '/', label: '看板概览', icon: '◫' },
  { href: '/products', label: '商品管理', icon: '⬚' },
  { href: '/orders', label: '订单管理', icon: '☰' },
  { href: '/settings', label: '店铺设置', icon: '⚙' },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <h1>Ghost DS</h1>
        <span>电商运营看板</span>
      </div>
      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href ||
            (item.href !== '/' && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`nav-item${active ? ' active' : ''}`}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
      <div style={{ padding: '12px 16px', borderTop: '1px solid var(--border)' }}>
        <span className="text-muted text-sm">
          {process.env.NEXT_PUBLIC_DEMO_MODE === 'true' ? 'Demo 模式' : '已连接'}
        </span>
      </div>
    </aside>
  );
}
