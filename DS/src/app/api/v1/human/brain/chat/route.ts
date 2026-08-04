/**
 * POST /api/v1/human/brain/chat
 * Proxy to Gateway /v1/human/brain/chat
 */

import { NextRequest, NextResponse } from 'next/server';
import { proxyToGateway } from '@/lib/api-proxy';

export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  try {
    const body = await req.text();
    const res = await proxyToGateway(req, '/v1/human/brain/chat', {
      method: 'POST',
      timeout: 30_000,
      body,
    });
    const data = await res.json().catch(() => ({ error: 'Gateway 返回无效响应' }));
    return NextResponse.json(data, { status: res.status });
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : '请求失败' },
      { status: 502 }
    );
  }
}
