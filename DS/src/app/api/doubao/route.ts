/**
 * POST /api/doubao/chat — 代理到 Gateway /v1/chat
 * GET  /api/doubao/status — Gateway 健康检查
 *
 * 认证: 需 Authorization: Bearer <DS_API_KEY>（配置 DS_API_KEY 后生效）
 */

import { NextRequest, NextResponse } from 'next/server';
import { proxyToGateway } from '@/lib/api-proxy';

export const dynamic = 'force-dynamic';

const GATEWAY_URL = process.env.GATEWAY_URL || 'http://gateway:18080';

/**
 * 检查 Gateway 状态
 */
export async function GET(req: NextRequest) {
  try {
    const res = await proxyToGateway(req, '/health', {
      method: 'GET',
      timeout: 5_000,
    });
    const data = await res.json().catch(() => ({ error: 'Gateway 返回无效响应' }));
    return NextResponse.json({ ok: true, gateway: data });
  } catch {
    return NextResponse.json({ ok: false, error: 'Gateway 不可达' });
  }
}

/**
 * 代理聊天请求到 Gateway
 */
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { alpha_id, message } = body;

    if (!message || typeof message !== 'string') {
      return NextResponse.json({ error: 'message 不能为空' }, { status: 400 });
    }

    // 构建 Gateway 请求 body（透传 alpha_id + message）
    const gatewayBody = JSON.stringify({
      alpha_id: alpha_id || 'Alpha-001',
      message,
    });

    // 直接透传原始请求到 Gateway（保留 alpha_id 等参数）
    const res = await fetch(`${GATEWAY_URL}/v1/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(req.headers.get('authorization') ? { authorization: req.headers.get('authorization')! } : {}),
      },
      body: gatewayBody,
      signal: AbortSignal.timeout(30000),
    });

    const data = await res.json();
    return NextResponse.json(data);
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : '请求失败' },
      { status: 502 }
    );
  }
}
