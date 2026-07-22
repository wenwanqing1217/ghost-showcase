import { NextRequest, NextResponse } from 'next/server';
import { destroySession, verifyCookieValue } from '@/lib/auth/session';

export async function POST(request: NextRequest) {
  const cookie = request.cookies.get('ds_session');
  if (cookie?.value) {
    const token = verifyCookieValue(cookie.value);
    if (token) {
      destroySession(token);
    }
  }

  const response = NextResponse.json({ success: true });
  response.cookies.delete('ds_session');
  return response;
}
