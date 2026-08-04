/**
 * GET /api/v1/human/social/[alpha_id]/messages
 * Proxy to Gateway /v1/human/social/{alpha_id}/messages
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
    const searchParams = req.nextUrl.searchParams;
    const queryString = searchParams.toString();
    const gatewayPath = `/v1/human/social/${encodeURIComponent(alpha_id)}/messages${queryString ? '?' + queryString : ''}`;

    const res = await proxyToGateway(req, gatewayPath, {
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
