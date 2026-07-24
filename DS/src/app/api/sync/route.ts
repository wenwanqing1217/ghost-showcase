/**
 * POST /api/sync — 手动触发数据同步
 * body: { entity: 'products' | 'orders' | 'all', shopId?: string }
 */

import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { ShoplazzaClient, ShoplazzaError } from '@/lib/shoplazza';
import { z } from 'zod';

export const dynamic = 'force-dynamic';

const SyncSchema = z.object({
  entity: z.enum(['products', 'orders', 'all']).default('all'),
  shopId: z.string().optional(),
});

/**
 * 同步商品：拉取 → upsert
 */
async function syncProducts(client: ShoplazzaClient, shopId: string): Promise<number> {
  const products = await client.listAllProducts();
  let count = 0;

  for (const p of products) {
    // Shoplazza 价格字段：price_min/price_max 或 variants[0].price
    const price = p.price_min
      ? parseFloat(String(p.price_min))
      : p.variants?.[0]?.price
        ? parseFloat(String(p.variants[0].price))
        : 0;
    const comparePrice = p.origin_price_max
      ? parseFloat(String(p.origin_price_max))
      : null;
    const imageSrcs = p.images?.map((i) => i.src) ?? [];

    await prisma.product.upsert({
      where: { shopId_externalId: { shopId, externalId: p.id } },
      update: {
        title: p.title,
        description: p.description ?? null,
        price,
        comparePrice,
        images: JSON.stringify(imageSrcs),
        status: p.published ? 'active' : 'draft',
        lastSyncedAt: new Date(),
      },
      create: {
        shopId,
        externalId: p.id,
        title: p.title,
        description: p.description ?? null,
        price,
        comparePrice,
        images: JSON.stringify(imageSrcs),
        status: p.published ? 'active' : 'draft',
        currency: 'USD',
      },
    });
    count += 1;
  }
  return count;
}

/**
 * 同步订单：拉取 → upsert
 */
async function syncOrders(client: ShoplazzaClient, shopId: string): Promise<number> {
  const orders = await client.listAllOrders();
  let count = 0;

  for (const o of orders) {
    await prisma.order.upsert({
      where: { shopId_externalId: { shopId, externalId: o.id } },
      update: {
        orderNo: o.order_number || o.name || o.id,
        amount: o.total_price ? parseFloat(String(o.total_price)) : 0,
        status: mapOrderStatus(o.financial_status, o.fulfillment_status),
        customerName: o.customer?.name ?? null,
        customerEmail: o.customer?.email ?? null,
        itemCount: o.line_items?.reduce((sum, li) => sum + li.quantity, 0) ?? 0,
        paidAt: o.financial_status === 'paid' ? new Date(o.created_at || Date.now()) : null,
        fulfilledAt: o.fulfillment_status === 'fulfilled' ? new Date(o.updated_at || Date.now()) : null,
        rawData: JSON.stringify(o),
      },
      create: {
        shopId,
        externalId: o.id,
        orderNo: o.order_number || o.name || o.id,
        amount: o.total_price ? parseFloat(String(o.total_price)) : 0,
        status: mapOrderStatus(o.financial_status, o.fulfillment_status),
        customerName: o.customer?.name ?? null,
        customerEmail: o.customer?.email ?? null,
        itemCount: o.line_items?.reduce((sum, li) => sum + li.quantity, 0) ?? 0,
        currency: 'USD',
        paidAt: o.financial_status === 'paid' ? new Date(o.created_at || Date.now()) : null,
        fulfilledAt: o.fulfillment_status === 'fulfilled' ? new Date(o.updated_at || Date.now()) : null,
        rawData: JSON.stringify(o),
      },
    });
    count += 1;
  }
  return count;
}

/** Shoplazza 状态 → 内部统一状态 */
function mapOrderStatus(
  financial?: string,
  fulfillment?: string
): string {
  if (financial === 'refunded' || financial === 'voided') return 'refunded';
  if (fulfillment === 'fulfilled') return 'fulfilled';
  if (financial === 'paid') return 'paid';
  if (financial === 'pending' || financial === 'authorized') return 'pending';
  return 'pending';
}

// ── 主入口 ──
export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => ({}));
  const { entity, shopId } = SyncSchema.parse(body);

  // 查找目标店铺
  const shop = shopId
    ? await prisma.shop.findUnique({ where: { id: shopId } })
    : await prisma.shop.findFirst({ where: { active: true } });

  if (!shop) {
    return NextResponse.json({ error: '未找到店铺，请先连接' }, { status: 404 });
  }

  // 创建客户端
  let client: ShoplazzaClient;
  try {
    client = new ShoplazzaClient(shop.domain, shop.accessToken);
  } catch (err) {
    return NextResponse.json(
      { error: `店铺配置无效: ${err instanceof Error ? err.message : ''}` },
      { status: 400 }
    );
  }

  const results: Record<string, { count: number; error?: string }> = {};

  // 同步商品
  if (entity === 'products' || entity === 'all') {
    const syncLog = await prisma.syncLog.create({
      data: { shopId: shop.id, entity: 'products', action: 'full', status: 'running' },
    });
    try {
      const count = await syncProducts(client, shop.id);
      await prisma.syncLog.update({
        where: { id: syncLog.id },
        data: { status: 'success', count, finishedAt: new Date() },
      });
      results.products = { count };
    } catch (err) {
      const msg = err instanceof ShoplazzaError ? err.message : String(err);
      await prisma.syncLog.update({
        where: { id: syncLog.id },
        data: { status: 'failed', error: msg, finishedAt: new Date() },
      });
      results.products = { count: 0, error: msg };
    }
  }

  // 同步订单
  if (entity === 'orders' || entity === 'all') {
    const syncLog = await prisma.syncLog.create({
      data: { shopId: shop.id, entity: 'orders', action: 'full', status: 'running' },
    });
    try {
      const count = await syncOrders(client, shop.id);
      await prisma.syncLog.update({
        where: { id: syncLog.id },
        data: { status: 'success', count, finishedAt: new Date() },
      });
      results.orders = { count };
    } catch (err) {
      const msg = err instanceof ShoplazzaError ? err.message : String(err);
      await prisma.syncLog.update({
        where: { id: syncLog.id },
        data: { status: 'failed', error: msg, finishedAt: new Date() },
      });
      results.orders = { count: 0, error: msg };
    }
  }

  const hasError = Object.values(results).some((r) => r.error);

  return NextResponse.json({
    ok: !hasError,
    results,
    shopId: shop.id,
    shopName: shop.name,
    syncedAt: new Date().toISOString(),
  });
}
