/**
 * POST /api/v1/human/chat
 * Proxy to Gateway /v1/human/chat
 */

import { NextRequest, NextResponse } from 'next/server';
import { proxyToGateway } from '@/lib/api-proxy';

export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  // 验证请求体
  const body = await req.json().catch(() => null);
  if (!body || typeof body.message !== 'string' || !body.message.trim()) {
    return NextResponse.json({ error: 'message 不能为空' }, { status: 400 });
  }

  // 透传到 Gateway，自动转发 X-Tenant-ID / Authorization 等 header
  const res = await proxyToGateway(req, '/v1/human/chat', {
    method: 'POST',
    timeout: 15_000,
  });

  const data = await res.json().catch(() => ({ error: 'Gateway 返回无效响应' }));
  return NextResponse.json(data, { status: res.status });
}
