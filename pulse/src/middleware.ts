import { NextRequest, NextResponse } from 'next/server';
import { logger } from '@/lib/observability/logger';
import { validateSession, verifyCookieValue } from '@/lib/auth/session';

const API_KEY = process.env.DS_API_KEY;
const DASH_USER = process.env.DASH_USER;
const DASH_PASS = process.env.DASH_PASS;

function isApiRoute(path: string): boolean {
  return path.startsWith('/api/');
}

function isAuthRoute(path: string): boolean {
  return path.startsWith('/api/auth/');
}

function unauthorized(reason: string) {
  logger.warn(reason);
  return NextResponse.json(
    { success: false, error: 'Unauthorized' },
    { status: 401 }
  );
}

export function middleware(request: NextRequest) {
  const path = request.nextUrl.pathname;

  // ── Auth routes: always allow (login/logout must be public) ──
  if (isAuthRoute(path)) {
    return NextResponse.next();
  }

  // ── API routes: require x-api-key header ──
  if (isApiRoute(path)) {
    if (!API_KEY) {
      // 任何环境下未配置 API Key 都拒绝 — 绝不开放未认证访问
      return NextResponse.json(
        { success: false, error: 'API key not configured' },
        { status: 500 }
      );
    }

    const providedKey = request.headers.get('x-api-key');
    if (providedKey !== API_KEY) {
      return unauthorized('Invalid API key');
    }
    return NextResponse.next();
  }

  // ── Dashboard routes: require session cookie if credentials configured ──
  if (DASH_USER && DASH_PASS) {
    const cookie = request.cookies.get('ds_session');
    if (!cookie?.value) {
      const loginUrl = new URL('/login', request.url);
      return NextResponse.redirect(loginUrl);
    }

    const token = verifyCookieValue(cookie.value);
    if (!token || !validateSession(token)) {
      const loginUrl = new URL('/login', request.url);
      const response = NextResponse.redirect(loginUrl);
      response.cookies.delete('ds_session');
      return response;
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/:path*'],
};
