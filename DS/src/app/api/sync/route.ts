/**
 * POST /api/sync — 手动触发数据同步
 * body: { entity: 'products' | 'orders' | 'all', shopId?: string }
 *
 * 认证: 需 Authorization: Bearer <DS_API_KEY>（配置 DS_API_KEY 后生效）
 */

import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { OneBoundClient, OneBoundError } from '@/lib/onebound';
import { verifyRequest } from '@/lib/auth';
import { getTenantId, tenantWhere, tenantCreateData } from '@/lib/tenant';
import { z } from 'zod';

export const dynamic = 'force-dynamic';

const SyncSchema = z.object({
  entity: z.enum(['products', 'orders', 'all']).default('all'),
  shopId: z.string().optional(),
});

/**
 * 同步商品：从 OneBound 拉取 → upsert（带 tenantId）
 */
async function syncProducts(client: OneBoundClient, shopId: string, tenantId: string): Promise<number> {
  const products = await client.listAllProducts();
  let count = 0;

  for (const p of products) {
    // OneBound 商品字段映射
    const price = p.price
      ? parseFloat(String(p.price))
      : p.variants?.[0]?.price
        ? parseFloat(String(p.variants[0].price))
        : 0;
    const comparePrice = p.compare_price
      ? parseFloat(String(p.compare_price))
      : null;
    const imageSrcs = p.images?.map((i) => i.url) ?? [];
    const status = p.status === 'active' || p.status === 'available' ? 'active' : 'draft';

    await prisma.product.upsert({
      where: { shopId_externalId: { shopId, externalId: String(p.id) } },
      update: {
        title: p.title,
        description: p.description ?? null,
        price,
        comparePrice,
        images: JSON.stringify(imageSrcs),
        status,
        lastSyncedAt: new Date(),
      },
      create: tenantCreateData(tenantId, {
        shopId,
        externalId: String(p.id),
        title: p.title,
        description: p.description ?? null,
        price,
        comparePrice,
        images: JSON.stringify(imageSrcs),
        status,
        currency: 'USD',
      }),
    });
    count += 1;
  }
  return count;
}

/**
 * 同步订单：从 OneBound 拉取代发订单 → upsert（带 tenantId）
 */
async function syncOrders(client: OneBoundClient, shopId: string, tenantId: string): Promise<number> {
  const orders = await client.listAllOrders();
  let count = 0;

  for (const o of orders) {
    const status = mapOneBoundStatus(o.status);
    const itemCount = o.items?.reduce((sum, li) => sum + (li.quantity || 0), 0) || 0;

    await prisma.order.upsert({
      where: { shopId_externalId: { shopId, externalId: String(o.id) } },
      update: {
        orderNo: o.order_number || String(o.id),
        amount: o.total ? parseFloat(String(o.total)) : 0,
        status,
        customerName: o.shipping_address?.name ?? null,
        customerEmail: null,
        itemCount,
        trackingNumber: o.tracking_number || null,
        trackingCompany: o.tracking_company || null,
        rawData: JSON.stringify(o),
      },
      create: tenantCreateData(tenantId, {
        shopId,
        externalId: String(o.id),
        orderNo: o.order_number || String(o.id),
        amount: o.total ? parseFloat(String(o.total)) : 0,
        status,
        currency: o.currency || 'USD',
        customerName: o.shipping_address?.name ?? null,
        itemCount,
        trackingNumber: o.tracking_number || null,
        trackingCompany: o.tracking_company || null,
        rawData: JSON.stringify(o),
      }),
    });
    count += 1;
  }
  return count;
}

/** OneBound 状态 → 内部统一状态 */
function mapOneBoundStatus(oneboundStatus?: string): string {
  if (!oneboundStatus) return 'pending';
  const s = oneboundStatus.toLowerCase();
  if (s.includes('fulfill') || s.includes('ship')) return 'fulfilled';
  if (s.includes('paid') || s.includes('confirm')) return 'paid';
  if (s.includes('cancel') || s.includes('refund')) return 'cancelled';
  if (s.includes('process')) return 'processing';
  return 'pending';
}

// ── 主入口 ──
export async function POST(req: NextRequest) {
  const auth = verifyRequest(req);
  if (!auth.ok) {
    return NextResponse.json({ error: auth.error }, { status: 401 });
  }

  const body = await req.json().catch(() => ({}));
  const { entity, shopId: requestedShopId } = SyncSchema.parse(body);
  const tenantId = getTenantId(req);

  // 查找目标店铺（tenant 隔离）
  const shop = requestedShopId
    ? await prisma.shop.findFirst({
        where: { id: requestedShopId, ...tenantWhere(tenantId) },
      })
    : await prisma.shop.findFirst({
        where: { active: true, ...tenantWhere(tenantId) },
      });

  if (!shop) {
    return NextResponse.json({ error: '未找到货源连接，请先连接 OneBound' }, { status: 404 });
  }

  // 创建 OneBound 客户端
  let client: OneBoundClient;
  try {
    client = new OneBoundClient(shop.accessToken);
  } catch (err) {
    return NextResponse.json(
      { error: `API Key 无效: ${err instanceof Error ? err.message : ''}` },
      { status: 400 }
    );
  }

  const results: Record<string, { count: number; error?: string }> = {};

  // 同步商品（从 OneBound 货源拉取）
  if (entity === 'products' || entity === 'all') {
    const syncLog = await prisma.syncLog.create({
      data: tenantCreateData(tenantId, { shopId: shop.id, entity: 'products', action: 'full', status: 'running' }),
    });
    try {
      const count = await syncProducts(client, shop.id, tenantId);
      await prisma.syncLog.update({
        where: { id: syncLog.id },
        data: { status: 'success', count, finishedAt: new Date() },
      });
      results.products = { count };
    } catch (err) {
      const msg = err instanceof OneBoundError ? err.message : String(err);
      await prisma.syncLog.update({
        where: { id: syncLog.id },
        data: { status: 'failed', error: msg, finishedAt: new Date() },
      });
      results.products = { count: 0, error: msg };
    }
  }

  // 同步订单（从 OneBound 拉取代发订单）
  if (entity === 'orders' || entity === 'all') {
    const syncLog = await prisma.syncLog.create({
      data: tenantCreateData(tenantId, { shopId: shop.id, entity: 'orders', action: 'full', status: 'running' }),
    });
    try {
      const count = await syncOrders(client, shop.id, tenantId);
      await prisma.syncLog.update({
        where: { id: syncLog.id },
        data: { status: 'success', count, finishedAt: new Date() },
      });
      results.orders = { count };
    } catch (err) {
      const msg = err instanceof OneBoundError ? err.message : String(err);
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
