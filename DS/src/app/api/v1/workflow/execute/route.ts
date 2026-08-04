/**
 * POST /api/v1/workflow/execute — 执行工作流
 * Proxy to Gateway → Nebula
 */

import { NextRequest, NextResponse } from 'next/server';
import { proxyToGateway } from '@/lib/api-proxy';

export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const res = await proxyToGateway(req, '/v1/human/workflows/execute', {
      method: 'POST',
      timeout: 30_000,
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({ error: 'Invalid response' }));
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ error: 'Workflow service unavailable' }, { status: 503 });
  }
}
