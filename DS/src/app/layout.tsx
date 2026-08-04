import type { Metadata } from 'next';
import './globals.css';
import Sidebar from '@/components/layout/Sidebar';

// TERM: EventBus — Redis Streams 跨服务事件总线
// 在服务器启动时初始化 EventBus，确保事件处理程序注册 + consumer loop 启动
// 之前仅在 health/route.ts import，导致只有访问 /api/health 时才初始化
import '@/lib/eventbus-init';

export const metadata: Metadata = {
  title: {
    default: 'Ghost Platform — Web4.0 人机共生基础设施',
    template: 'G · %s',
  },
  description: '国内合规、以人为核心的 Web4.0 人机共生基础设施。一人一生唯一 Alpha-ID + 双大脑架构 + A2A 智能体协同。',
  icons: {
    icon: '/favicon.svg',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body>
        <div className="app-shell">
          <Sidebar />
          <main className="main-content">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
