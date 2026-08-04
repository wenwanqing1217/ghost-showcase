import { NextRequest, NextResponse } from 'next/server';
import { proxyToGateway } from '@/lib/api-proxy';

export async function GET(req: NextRequest) {
  const res = await proxyToGateway(req, '/v1/agent/a2a/agents');
  return res;
}
