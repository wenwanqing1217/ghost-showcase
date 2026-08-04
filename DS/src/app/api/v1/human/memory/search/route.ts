/**
 * GET /api/v1/human/memory/search
 * Proxy to Gateway /v1/human/memory/search
 */

import { NextRequest, NextResponse } from 'next/server';
import { proxyToGateway } from '@/lib/api-proxy';

export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  try {
    const searchParams = req.nextUrl.searchParams;
    const q = searchParams.get('q') || '';
    const alphaId = searchParams.get('alpha_id') || 'Alpha-001';

    if (!q) {
      return NextResponse.json({ error: 'q 参数不能为空' }, { status: 400 });
    }

    const gatewayPath = `/v1/human/memory/search?q=${encodeURIComponent(q)}&alpha_id=${encodeURIComponent(alphaId)}`;

    const res = await proxyToGateway(req, gatewayPath, {
      method: 'GET',
      timeout: 10_000,
    });

    const data = await res.json().catch(() => ({ results: [], message: 'Gateway 返回无效响应' }));
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ results: [], message: '搜索服务暂不可用' });
  }
}
