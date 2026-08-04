/**
 * GET /api/internal/monitoring/metrics
 * 代理到 Gateway 的 /v1/internal/monitoring/metrics 端点
 * 汇总所有后端服务的 Prometheus 指标
 */

import { NextRequest, NextResponse } from 'next/server';
import { proxyToGateway } from '@/lib/api-proxy';

export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  try {
    const res = await proxyToGateway(req, '/v1/internal/monitoring/metrics', {
      method: 'GET',
      timeout: 10_000,
    });

    const data = await res.json().catch(() => ({ error: 'Gateway 返回无效响应' }));
    return NextResponse.json(data, { status: res.status });
  } catch (error) {
    return NextResponse.json(
      {
        error: 'Failed to fetch monitoring metrics',
        message: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 502 }
    );
  }
}
