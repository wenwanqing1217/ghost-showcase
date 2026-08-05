/**
 * POST /api/content/generate — 触发内容生成（视频 / 游戏）
 *
 * 根据 body.type 路由到 Ghost Gateway 对应的生成端点：
 *   type: "video"  → POST http://localhost:18080/v1/content/video/generate
 *   type: "game"   → POST http://localhost:18080/v1/content/game/generate
 *
 * 前端无需感知 Gateway 地址，由 DS API Route 统一代理。
 */

import { NextRequest, NextResponse } from 'next/server';
import { proxyToGateway } from '@/lib/api-proxy';
import { z } from 'zod';

export const dynamic = 'force-dynamic';

// ── 视频生成参数校验 ──
const VideoGenerateSchema = z.object({
  type: z.literal('video'),
  video_subject: z.string().min(1, 'video_subject 不能为空'),
  video_language: z.string().default('中文'),
  video_aspect: z.enum(['16:9', '9:16', '1:1']).default('16:9'),
  video_concat_mode: z.enum(['random', 'order']).default('random'),
  paragraph_number: z.number().int().positive().max(20).default(3),
  n_threads: z.number().int().positive().max(16).default(2),
  video_source: z.string().optional(),
  video_materials: z.array(z.string()).optional(),
});

// ── 游戏生成参数校验 ──
const GameGenerateSchema = z.object({
  type: z.literal('game'),
  game_type: z.string().min(1, 'game_type 不能为空'),
  theme: z.string().min(1, 'theme 不能为空'),
  description: z.string().optional(),
});

export async function POST(req: NextRequest) {
  // 读取 body 一次，用于验证 + 透传
  const rawBody = await req.text().catch(() => '');
  if (!rawBody.trim()) {
    return NextResponse.json({ error: '请求体不能为空' }, { status: 400 });
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(rawBody);
  } catch {
    return NextResponse.json({ error: '请求体 JSON 格式无效' }, { status: 400 });
  }

  // 根据 type 分发到不同 Gateway 端点
  let gatewayPath: string;
  let validatedBody: unknown;

  if (typeof parsed === 'object' && parsed !== null && 'type' in parsed) {
    const type = (parsed as { type: string }).type;

    if (type === 'video') {
      const result = VideoGenerateSchema.safeParse(parsed);
      if (!result.success) {
        return NextResponse.json(
          { error: '参数校验失败', details: result.error.errors },
          { status: 400 }
        );
      }
      gatewayPath = '/v1/content/video/generate';
      validatedBody = result.data;
    } else if (type === 'game') {
      const result = GameGenerateSchema.safeParse(parsed);
      if (!result.success) {
        return NextResponse.json(
          { error: '参数校验失败', details: result.error.errors },
          { status: 400 }
        );
      }
      gatewayPath = '/v1/content/game/generate';
      validatedBody = result.data;
    } else {
      return NextResponse.json(
        { error: `不支持的生成类型: "${type}"，可选值: video, game` },
        { status: 400 }
      );
    }
  } else {
    return NextResponse.json(
      { error: '请求体缺少 type 字段，请指定 type: "video" 或 type: "game"' },
      { status: 400 }
    );
  }

  // 透传到 Gateway，自动转发 X-Tenant-ID 等关键 header
  const res = await proxyToGateway(req, gatewayPath, {
    method: 'POST',
    timeout: 30_000,
    body: JSON.stringify(validatedBody),
  });

  // Gateway 返回失败状态时透传错误信息
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({
      error: `Gateway 返回错误 (${res.status})`,
    }));
    return NextResponse.json(errorData, { status: res.status });
  }

  // 返回 Gateway 原始响应（包含 task_id, status 等）
  const data = await res.json().catch(() => ({ error: 'Gateway 返回无效响应' }));
  return NextResponse.json(data);
}
