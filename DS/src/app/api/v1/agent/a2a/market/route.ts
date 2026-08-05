import { NextRequest, NextResponse } from 'next/server';
import { proxyToGateway } from '@/lib/api-proxy';

export async function GET(req: NextRequest) {
  const url = new URL(req.url);
  const search = url.search || '';
  const res = await proxyToGateway(req, `/v1/agent/a2a/market${search}`, {
    method: 'GET',
  });
  return res;
}
