/**
 * POST /api/v1/human/register/complete
 * Proxy to Gateway /v1/human/register/complete
 */

import { NextRequest, NextResponse } from 'next/server';
import { proxyToGateway } from '@/lib/api-proxy';

export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  try {
    const res = await proxyToGateway(req, '/v1/human/register/complete', {
      method: 'POST',
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
