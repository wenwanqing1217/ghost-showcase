/**
 * GET /api/v1/human/social/[alpha_id]/requests
 * Proxy to Gateway /v1/human/social/{alpha_id}/requests
 */

import { NextRequest, NextResponse } from 'next/server';
import { proxyToGateway } from '@/lib/api-proxy';

export const dynamic = 'force-dynamic';

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ alpha_id: string }> }
) {
  try {
    const { alpha_id } = await params;
    const res = await proxyToGateway(req, `/v1/human/social/${encodeURIComponent(alpha_id)}/requests`, {
      method: 'GET',
      timeout: 10_000,
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
