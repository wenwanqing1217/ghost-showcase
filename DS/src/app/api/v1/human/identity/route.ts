/**
 * GET /api/v1/human/identity
 * Proxy to Gateway /v1/human/identity
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
  } catch {
    // Fallback: return mock identity for development
    return NextResponse.json({
      ok: true,
      data: {
        did: 'did:aid:demo-local-alpha-id',
        name: 'Demo User',
        env: process.env.NODE_ENV || 'development',
      },
    });
  }
}
