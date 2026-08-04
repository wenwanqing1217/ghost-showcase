/**
 * PUT /api/v1/human/social/friend-request/[request_id]
 * Proxy to Gateway /v1/human/social/friend-request/{request_id}
 */

import { NextRequest, NextResponse } from 'next/server';
import { proxyToGateway } from '@/lib/api-proxy';

export const dynamic = 'force-dynamic';

export async function PUT(
  req: NextRequest,
  { params }: { params: Promise<{ request_id: string }> }
) {
  try {
    const { request_id } = await params;
    const body = await req.text();
    const res = await proxyToGateway(req, `/v1/human/social/friend-request/${encodeURIComponent(request_id)}`, {
      method: 'PUT',
      timeout: 10_000,
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
