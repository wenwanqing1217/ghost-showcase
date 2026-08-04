import type { Metadata } from 'next';
import './globals.css';
import Sidebar from '@/components/layout/Sidebar';

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
