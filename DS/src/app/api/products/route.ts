/**
 * GET /api/products — 商品列表（支持分页/搜索）
 * query: ?page=1&limit=20&status=active&search=xxx
 *
 * 认证: 需 Authorization: Bearer <DS_API_KEY>（配置 DS_API_KEY 后生效）
 */

import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { verifyRequest } from '@/lib/auth';

export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  const auth = verifyRequest(req);
  if (!auth.ok) {
    return NextResponse.json({ error: auth.error }, { status: 401 });
  }

  const { searchParams } = new URL(req.url);
  const page = Math.max(1, parseInt(searchParams.get('page') || '1', 10));
  const limit = Math.min(100, Math.max(1, parseInt(searchParams.get('limit') || '20', 10)));
  const status = searchParams.get('status');
  const search = searchParams.get('search')?.trim();

  const where: Record<string, unknown> = {};
  if (status) where.status = status;
  if (search) {
    where.OR = [
      { title: { contains: search, mode: 'insensitive' } },
      { description: { contains: search, mode: 'insensitive' } },
    ];
  }

  const [items, total] = await Promise.all([
    prisma.product.findMany({
      where,
      orderBy: { lastSyncedAt: 'desc' },
      skip: (page - 1) * limit,
      take: limit,
      select: {
        id: true,
        externalId: true,
        title: true,
        description: true,
        price: true,
        comparePrice: true,
        currency: true,
        inventory: true,
        images: true,
        status: true,
        lastSyncedAt: true,
      },
    }),
    prisma.product.count({ where }),
  ]);

  return NextResponse.json({
    items,
    pagination: {
      page,
      limit,
      total,
      totalPages: Math.ceil(total / limit),
    },
  });
}
