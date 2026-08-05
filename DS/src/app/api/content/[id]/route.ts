/**
 * GET /api/content/[id] — 获取单个内容详情
 * DELETE /api/content/[id] — 删除内容
 * PATCH /api/content/[id] — 更新内容
 */

import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { getTenantId, tenantWhere } from '@/lib/tenant';
import { withMetrics } from '@/app/api/metrics/route';

export const dynamic = 'force-dynamic';

async function handler(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const tenantId = getTenantId(req);
  const { id } = await params;

  if (req.method === 'GET') {
    const item = await prisma.content.findFirst({
      where: { ...tenantWhere(tenantId), id },
    });

    if (!item) {
      return NextResponse.json({ error: 'Content not found' }, { status: 404 });
    }

    return NextResponse.json(item);
  }

  if (req.method === 'DELETE') {
    const item = await prisma.content.findFirst({
      where: { ...tenantWhere(tenantId), id },
    });

    if (!item) {
      return NextResponse.json({ error: 'Content not found' }, { status: 404 });
    }

    await prisma.content.delete({ where: { id } });
    return NextResponse.json({ success: true });
  }

  if (req.method === 'PATCH') {
    const body = await req.json();
    const item = await prisma.content.update({
      where: { id },
      data: {
        title: body.title,
        description: body.description,
        status: body.status,
        tags: Array.isArray(body.tags) ? JSON.stringify(body.tags) : undefined,
        metadata: body.metadata ? JSON.stringify(body.metadata) : undefined,
      },
    });

    return NextResponse.json(item);
  }

  return NextResponse.json({ error: 'Method not allowed' }, { status: 405 });
}

export const GET = withMetrics(handler, 'GET /api/content/[id]');
export const DELETE = withMetrics(handler, 'DELETE /api/content/[id]');
export const PATCH = withMetrics(handler, 'PATCH /api/content/[id]');
