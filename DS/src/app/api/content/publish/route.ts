/**
 * POST /api/content/publish — 视频跨平台发布
 *
 * 代理到 Gateway POST /v1/content/video/publish
 * 将已生成的视频发布到 TikTok / Instagram / YouTube
 */

import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const GATEWAY_URL = process.env.GATEWAY_URL || process.env.NEXT_PUBLIC_GATEWAY_URL || 'http://localhost:18080';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { task_id, title, platforms, youtube_description, youtube_tags, youtube_privacy_status } = body;

    if (!task_id || !title) {
      return NextResponse.json(
        { error: 'task_id 和 title 必填' },
        { status: 400 },
      );
    }

    const resp = await fetch(`${GATEWAY_URL}/v1/content/video/publish`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        task_id,
        title,
        platforms: platforms || ['tiktok'],
        youtube_description,
        youtube_tags,
        youtube_privacy_status: youtube_privacy_status || 'public',
      }),
    });

    const data = await resp.json();

    if (!resp.ok) {
      return NextResponse.json(
        { error: data.error || data.detail || `Gateway 返回 ${resp.status}` },
        { status: resp.status },
      );
    }

    return NextResponse.json(data);
  } catch (err) {
    console.error('[content/publish] 代理失败:', err);
    return NextResponse.json(
      { error: err instanceof Error ? err.message : '发布请求失败' },
      { status: 500 },
    );
  }
}
