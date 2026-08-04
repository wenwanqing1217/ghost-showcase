import { NextRequest, NextResponse } from 'next/server';
import { proxyToGateway } from '@/lib/api-proxy';

export async function GET(req: NextRequest) {
  const url = new URL(req.url);
  const query = url.searchParams.toString();
  const path = query ? `/v1/obsidian/cards/search?${query}` : '/v1/obsidian/cards/search';
  const res = await proxyToGateway(req, path);
  return res;
}
