/**
 * POST /api/orders/[id]/fulfill — 标记订单发货
 * body: { trackingNumber?: string, trackingCompany?: string }
 */

import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { createShoplazzaClient } from '@/lib/shoplazza';
import { z } from 'zod';

export const dynamic = 'force-dynamic';

const FulfillSchema = z.object({
  trackingNumber: z.string().optional(),
  trackingCompany: z.string().optional(),
});

export async function POST(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const body = await req.json().catch(() => ({}));
    const { trackingNumber, trackingCompany } = FulfillSchema.parse(body);

    // 查找订单
    const order = await prisma.order.findUnique({
      where: { id: params.id },
      include: { shop: true },
    });

    if (!order) {
      return NextResponse.json({ error: '订单不存在' }, { status: 404 });
    }

    if (order.status === 'fulfilled') {
      return NextResponse.json({ error: '订单已发货' }, { status: 400 });
    }

    if (order.status === 'refunded' || order.status === 'cancelled') {
      return NextResponse.json({ error: '订单已退款/取消，无法发货' }, { status: 400 });
    }

    // 调用 Shoplazza API 发货
    const client = createShoplazzaClient();
    if (client && order.shop.domain === process.env.SHOPLAZZA_SHOP_DOMAIN) {
      try {
        await client.fulfillOrder(order.externalId, trackingNumber, trackingCompany);
      } catch {
        // Shoplazza API 失败也继续更新本地状态（可能是测试订单）
      }
    }

    // 更新本地订单状态
    const updated = await prisma.order.update({
      where: { id: order.id },
      data: {
        status: 'fulfilled',
        fulfilledAt: new Date(),
        trackingNumber: trackingNumber || null,
        trackingCompany: trackingCompany || null,
      },
    });

    return NextResponse.json({
      ok: true,
      order: {
        id: updated.id,
        orderNo: updated.orderNo,
        status: updated.status,
        fulfilledAt: updated.fulfilledAt,
      },
    });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json({ error: '参数校验失败', details: error.errors }, { status: 400 });
    }
    return NextResponse.json(
      { error: '发货失败', detail: error instanceof Error ? error.message : undefined },
      { status: 500 }
    );
  }
}
