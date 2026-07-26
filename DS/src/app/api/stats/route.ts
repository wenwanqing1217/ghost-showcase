/**
 * GET /api/stats — 看板统计数据
 * 返回：商品总数、订单总数、收入总额、各状态分布、近7日趋势
 */

import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

export const dynamic = 'force-dynamic';

export async function GET() {
  const now = new Date();
  const sevenDaysAgo = new Date(now.getTime() - 7 * 86400000);

  const [
    productCount,
    productActiveCount,
    orderCount,
    orderTotalAmount,
    statusDistribution,
    recentOrders,
    lowInventoryCount,
  ] = await Promise.all([
    // 商品总数
    prisma.product.count(),
    // 在售商品数
    prisma.product.count({ where: { status: 'active' } }),
    // 订单总数
    prisma.order.count(),
    // 订单总金额（已支付）
    prisma.order.aggregate({
      _sum: { amount: true },
      where: { status: { in: ['paid', 'fulfilled'] } },
    }),
    // 订单状态分布
    prisma.order.groupBy({
      by: ['status'],
      _count: { status: true },
      _sum: { amount: true },
    }),
    // 最近 7 日订单
    prisma.order.findMany({
      where: { createdAt: { gte: sevenDaysAgo } },
      select: {
        amount: true,
        status: true,
        createdAt: true,
      },
      orderBy: { createdAt: 'asc' },
    }),
    // 低库存商品（< 10）
    prisma.product.count({
      where: { inventory: { lt: 10 }, status: 'active' },
    }),
  ]);

  // 按日聚合近7日收入（补全无订单的日期为 0）
  const dailyMap: Record<string, number> = {};
  for (let i = 6; i >= 0; i--) {
    const d = new Date(now.getTime() - i * 86400000);
    dailyMap[d.toISOString().slice(0, 10)] = 0;
  }
  for (const o of recentOrders) {
    if (o.status === 'paid' || o.status === 'fulfilled') {
      const day = o.createdAt.toISOString().slice(0, 10);
      if (day in dailyMap) {
        dailyMap[day] = (dailyMap[day] || 0) + o.amount;
      }
    }
  }
  const dailyRevenue = Object.entries(dailyMap)
    .map(([date, amount]) => ({ date, amount }))
    .sort((a, b) => a.date.localeCompare(b.date));

  return NextResponse.json({
    overview: {
      productCount,
      productActiveCount,
      orderCount,
      totalRevenue: orderTotalAmount._sum.amount ?? 0,
      lowInventoryCount,
    },
    orderStatus: statusDistribution.map((s) => ({
      status: s.status,
      count: s._count.status,
      amount: s._sum.amount ?? 0,
    })),
    dailyRevenue,
    currency: 'USD',
    generatedAt: now.toISOString(),
  });
}
