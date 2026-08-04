/**
 * GET /api/v1/workflow/templates — 获取工作流模板列表
 * Proxy to Gateway → Nebula
 */

import { NextRequest, NextResponse } from 'next/server';
import { proxyToGateway } from '@/lib/api-proxy';

export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  try {
    const res = await proxyToGateway(req, '/v1/human/workflows', { method: 'GET', timeout: 10_000 });
    const data = await res.json().catch(() => ({ error: 'Invalid response' }));
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ error: 'Workflow service unavailable' }, { status: 503 });
  }
}
