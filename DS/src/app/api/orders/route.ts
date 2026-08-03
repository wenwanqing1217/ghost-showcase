/**
 * GET /api/orders — 订单列表（支持分页/状态筛选）
 * query: ?page=1&limit=20&status=paid&search=xxx
 *
 * 认证: 需 Authorization: Bearer <DS_API_KEY>（配置 DS_API_KEY 后生效）
 */

import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { verifyRequest } from '@/lib/auth';

export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  // 认证检查
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
      { orderNo: { contains: search, mode: 'insensitive' } },
      { customerName: { contains: search, mode: 'insensitive' } },
      { customerEmail: { contains: search, mode: 'insensitive' } },
    ];
  }

  const [items, total, statusStats] = await Promise.all([
    prisma.order.findMany({
      where,
      orderBy: { createdAt: 'desc' },
      skip: (page - 1) * limit,
      take: limit,
      select: {
        id: true,
        externalId: true,
        orderNo: true,
        amount: true,
        currency: true,
        status: true,
        customerName: true,
        customerEmail: true,
        itemCount: true,
        paidAt: true,
        fulfilledAt: true,
        createdAt: true,
      },
    }),
    prisma.order.count({ where }),
    // 各状态订单数（用于筛选标签）
    prisma.order.groupBy({
      by: ['status'],
      _count: { status: true },
    }),
  ]);

  return NextResponse.json({
    items,
    pagination: { page, limit, total, totalPages: Math.ceil(total / limit) },
    statusCounts: statusStats.reduce((acc: Record<string, number>, s: { status: string; _count: { status: number } }) => {
      acc[s.status] = s._count.status;
      return acc;
    }, {} as Record<string, number>),
  });
}
