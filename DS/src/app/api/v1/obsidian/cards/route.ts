import { NextRequest, NextResponse } from 'next/server';
import { proxyToGateway } from '@/lib/api-proxy';

export async function GET(req: NextRequest) {
  const url = new URL(req.url);
  const query = url.searchParams.toString();
  const path = query ? `/v1/obsidian/cards?${query}` : '/v1/obsidian/cards';
  const res = await proxyToGateway(req, path);
  return res;
}

export async function POST(req: NextRequest) {
  const rawBody = await req.text().catch(() => '');
  if (!rawBody.trim()) {
    return NextResponse.json({ error: '请求体不能为空' }, { status: 400 });
  }
  const res = await proxyToGateway(req, '/v1/obsidian/cards', {
    method: 'POST',
    timeout: 15_000,
    body: rawBody,
  });
  return res;
}
