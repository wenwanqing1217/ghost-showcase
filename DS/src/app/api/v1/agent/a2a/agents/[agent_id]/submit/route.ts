import { NextRequest, NextResponse } from 'next/server';
import { proxyToGateway } from '@/lib/api-proxy';

export async function POST(req: NextRequest, { params }: { params: { agent_id: string } }) {
  const res = await proxyToGateway(req, `/v1/agent/a2a/agents/${params.agent_id}/submit`, {
    method: 'POST',
  });
  return res;
}
