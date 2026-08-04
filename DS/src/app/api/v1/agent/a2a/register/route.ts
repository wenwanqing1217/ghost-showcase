import { NextRequest, NextResponse } from 'next/server';
import { proxyToGateway } from '@/lib/api-proxy';

export async function POST(req: NextRequest) {
  const rawBody = await req.text().catch(() => '');
  if (!rawBody.trim()) {
    return NextResponse.json({ error: '请求体不能为空' }, { status: 400 });
  }
  const res = await proxyToGateway(req, '/v1/agent/a2a/register', {
    method: 'POST',
    timeout: 15_000,
    body: rawBody,
  });
  return res;
}
