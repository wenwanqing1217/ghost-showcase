/**
 * GET /api/v1/human/identity
 * Proxy to Gateway /v1/human/identity
 *
 * 重要：失败时返回 502/401，不再返回假 ok:true mock。
 * 否则 AuthGuard 会把任何错误都当作"已登录"，造成认证绕过。
 */

import { NextRequest, NextResponse } from 'next/server';
import { proxyToGateway } from '@/lib/api-proxy';

export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  try {
    const res = await proxyToGateway(req, '/v1/human/identity', {
      method: 'GET',
      timeout: 5_000,
    });
    const data = await res.json().catch(() => ({ error: 'Gateway 返回无效响应' }));
    return NextResponse.json(data, { status: res.status });
  } catch (e) {
    // Gateway 连接失败 — 返回 502，让 AuthGuard 正确识别为"未登录"
    return NextResponse.json(
      { ok: false, error: e instanceof Error ? e.message : 'Gateway 连接失败' },
      { status: 502 }
    );
  }
}

