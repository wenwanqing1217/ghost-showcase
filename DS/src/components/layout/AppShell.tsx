'use client';

import { usePathname } from 'next/navigation';
import Sidebar from '@/components/layout/Sidebar';

/**
 * 应用外壳：根据路由决定是否渲染侧边栏。
 * 公共页（品牌首页 / 登录 / demo）不套侧边栏，其余业务页保留侧边栏布局。
 */
const PUBLIC_PATHS = new Set(['/', '/login', '/demo']);

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isPublic = PUBLIC_PATHS.has(pathname);

  if (isPublic) {
    return <>{children}</>;
  }

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-content">{children}</main>
    </div>
  );
}
