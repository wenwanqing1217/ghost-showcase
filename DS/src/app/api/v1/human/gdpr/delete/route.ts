/**
 * DELETE /api/v1/human/gdpr/delete
 * Proxy to Gateway /v1/human/gdpr/delete
 */

import { NextRequest, NextResponse } from 'next/server';
import { proxyToGateway } from '@/lib/api-proxy';

export const dynamic = 'force-dynamic';

export async function DELETE(req: NextRequest) {
  try {
    const body = await req.text().catch(() => '');
    const res = await proxyToGateway(req, '/v1/human/gdpr/delete', {
      method: 'DELETE',
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
