'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

interface AuthGuardProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

/**
 * 鉴权守卫组件
 * 检查用户是否已登录（通过 Alpha-ID identity API）
 * 未登录则重定向到首页
 */
export default function AuthGuard({ children, fallback }: AuthGuardProps) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const router = useRouter();

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const res = await fetch('/api/v1/human/identity', {
          credentials: 'include',
        });
        if (res.ok) {
          // 200 时还需校验响应含有效身份字段，防止异常 200 空数据被当作"已登录"
          const data = await res.json().catch(() => null);
          const payload = data?.data || data || {};
          setIsAuthenticated(!!(payload.alpha_id || payload.did || payload.id));
        } else {
          setIsAuthenticated(false);
        }
      } catch {
        setIsAuthenticated(false);
      }
    };

    checkAuth();
  }, [router]);

  // 未认证时重定向到登录页（在 effect 中执行，避免 render phase 中调用 router.push 导致崩溃）
  useEffect(() => {
    if (isAuthenticated === false) {
      router.push('/login');
    }
  }, [isAuthenticated, router]);

  // 加载中
  if (isAuthenticated === null) {
    return fallback || (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-text-secondary text-sm">加载中...</div>
      </div>
    );
  }

  // 未认证
  if (!isAuthenticated) {
    return fallback || null;
  }

  // 已认证，渲染子组件
  return <>{children}</>;
}
