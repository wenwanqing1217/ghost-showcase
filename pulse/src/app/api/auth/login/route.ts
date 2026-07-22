import { NextRequest, NextResponse } from 'next/server';
import { timingSafeEqual } from 'crypto';
import { createSession, buildCookieValue } from '@/lib/auth/session';

const DASH_USER = process.env.DASH_USER;
const DASH_PASS = process.env.DASH_PASS;

function constantTimeCompare(a: string, b: string): boolean {
  const bufA = Buffer.from(a);
  const bufB = Buffer.from(b);
  if (bufA.length !== bufB.length) return false;
  return timingSafeEqual(bufA, bufB);
}

export async function POST(request: NextRequest) {
  // If no credentials configured, deny login
  if (!DASH_USER || !DASH_PASS) {
    return NextResponse.json(
      { success: false, error: 'Authentication not configured' },
      { status: 503 }
    );
  }

  let body: { username?: string; password?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { success: false, error: 'Invalid request body' },
      { status: 400 }
    );
  }

  const { username, password } = body;

  if (!username || !password) {
    return NextResponse.json(
      { success: false, error: 'Username and password required' },
      { status: 400 }
    );
  }

  // Constant-time comparison to prevent timing attacks
  if (!constantTimeCompare(username, DASH_USER) || !constantTimeCompare(password, DASH_PASS)) {
    return NextResponse.json(
      { success: false, error: 'Invalid credentials' },
      { status: 401 }
    );
  }

  const token = createSession(username);
  const cookieValue = buildCookieValue(token);

  const response = NextResponse.json({ success: true, user: username });
  response.cookies.set('ds_session', cookieValue, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    path: '/',
    maxAge: 60 * 60 * 8, // 8 hours
  });

  return response;
}
