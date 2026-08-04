/**
 * GET /api/v1/human/memory/graph
 * Proxy to Gateway /v1/human/memory/graph
 */

import { NextRequest, NextResponse } from 'next/server';
import { proxyToGateway } from '@/lib/api-proxy';

export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  try {
    const searchParams = req.nextUrl.searchParams;
    const alphaId = searchParams.get('alpha_id') || 'Alpha-001';

    // 将 alpha_id 作为 query 参数拼到 Gateway 路径上
    const gatewayPath = `/v1/human/memory/graph?alpha_id=${encodeURIComponent(alphaId)}`;

    const res = await proxyToGateway(req, gatewayPath, {
      method: 'GET',
      timeout: 10_000,
    });

    const data = await res.json().catch(() => ({ error: 'Gateway 返回无效响应' }));
    return NextResponse.json(data, { status: res.status });
  } catch {
    // Fallback: return empty graph
    return NextResponse.json({
      nodes: [],
      stats: {
        totalAtoms: 0,
        totalRelations: 0,
        totalMemories: 0,
        layers: 0,
      },
    });
  }
}
