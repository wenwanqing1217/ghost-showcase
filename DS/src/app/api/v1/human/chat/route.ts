/**
 * POST /api/v1/human/chat
 * Proxy to Gateway /v1/human/chat
 */

import { NextRequest, NextResponse } from 'next/server';
import { proxyToGateway } from '@/lib/api-proxy';

export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  // 读取 body 一次，用于验证 + 透传（避免 Body 被重复读取报错）
  const rawBody = await req.text().catch(() => '');
  if (!rawBody.trim()) {
    return NextResponse.json({ error: '请求体不能为空' }, { status: 400 });
  }

  const body = JSON.parse(rawBody) as { message?: string };
  if (!body.message || typeof body.message !== 'string' || !body.message.trim()) {
    return NextResponse.json({ error: 'message 不能为空' }, { status: 400 });
  }

  // 透传到 Gateway，自动转发 X-Tenant-ID / Authorization 等 header
  const res = await proxyToGateway(req, '/v1/human/chat', {
    method: 'POST',
    timeout: 15_000,
    body: rawBody,
  });

  const data = await res.json().catch(() => ({ error: 'Gateway 返回无效响应' }));
  return NextResponse.json(data, { status: res.status });
}
