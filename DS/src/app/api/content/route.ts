/**
 * GET /api/content — AI 生成内容列表（视频/游戏）
 * query: ?page=1&limit=20&type=video&status=completed&search=xxx
 *
 * POST /api/content — 创建内容记录（视频生成完成后由后端写入）
 * body: { contentType, title, description?, videoUrl?, ... }
 */

import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { getTenantId, tenantWhere } from '@/lib/tenant';
import { withMetrics } from '@/app/api/metrics/route';

export const dynamic = 'force-dynamic';

async function handler(req: NextRequest): Promise<NextResponse> {
  const tenantId = getTenantId(req);

  if (req.method === 'GET') {
    const { searchParams } = new URL(req.url);
    const page = Math.max(1, parseInt(searchParams.get('page') || '1', 10));
    const limit = Math.min(100, Math.max(1, parseInt(searchParams.get('limit') || '20', 10)));
    const contentType = searchParams.get('type'); // video | game
    const status = searchParams.get('status');
    const search = searchParams.get('search')?.trim();

    const where: Record<string, unknown> = tenantWhere(tenantId);
    if (contentType) where.contentType = contentType;
    if (status) where.status = status;
    if (search) {
      where.OR = [
        { title: { contains: search, mode: 'insensitive' } },
        { description: { contains: search, mode: 'insensitive' } },
      ];
    }

    const [items, total] = await Promise.all([
      prisma.content.findMany({
        where,
        orderBy: { createdAt: 'desc' },
        skip: (page - 1) * limit,
        take: limit,
      }),
      prisma.content.count({ where }),
    ]);

    return NextResponse.json({
      items,
      pagination: { page, limit, total, totalPages: Math.ceil(total / limit) },
    });
  }

  if (req.method === 'POST') {
    const body = await req.json();
    const {
      contentType = 'video',
      title,
      description,
      status = 'completed',
      taskId,
      videoUrl,
      thumbnailUrl,
      duration,
      script,
      aspectRatio,
      gameUrl,
      gameType,
      theme,
      tags = [],
      metadata,
    } = body;

    if (!title) {
      return NextResponse.json({ error: 'title is required' }, { status: 400 });
    }

    const item = await prisma.content.create({
      data: {
        contentType,
        title,
        description,
        status,
        taskId,
        videoUrl,
        thumbnailUrl,
        duration,
        script,
        aspectRatio,
        gameUrl,
        gameType,
        theme,
        tags: Array.isArray(tags) ? JSON.stringify(tags) : tags,
        metadata: metadata ? JSON.stringify(metadata) : null,
        tenantId,
      },
    });

    return NextResponse.json(item, { status: 201 });
  }

  return NextResponse.json({ error: 'Method not allowed' }, { status: 405 });
}

export const GET = withMetrics(handler, 'GET /api/content');
export const POST = withMetrics(handler, 'POST /api/content');
