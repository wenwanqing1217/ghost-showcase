/**
 * POST /api/cron/sync — 定时自动同步端点
 *
 * 供外部 cron 服务调用（如系统 crontab、GitHub Actions、Vercel Cron）
 * 建议频率：每 15 分钟执行一次
 *
 * 使用方式：
 * 1. 系统 crontab: 每15分钟 curl -X POST https://your-domain.com/api/cron/sync
 * 2. GitHub Actions: 配置 schedule cron 触发
 * 3. 配合 Authorization 头保护端点
 *
 * 请求头：Authorization: Bearer ${CRON_SECRET}
 */

import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { createShoplazzaClient, ShoplazzaError } from '@/lib/shoplazza';

export const dynamic = 'force-dynamic';
export const maxDuration = 120; // 最长运行 2 分钟

const CRON_SECRET = process.env.CRON_SECRET || '';

/**
 * 简单的 Bearer Token 验证
 */
function verifyAuth(req: NextRequest): boolean {
  if (!CRON_SECRET) return true; // 未配置则跳过验证
  const auth = req.headers.get('authorization');
  return auth === `Bearer ${CRON_SECRET}`;
}

export async function POST(req: NextRequest) {
  if (!verifyAuth(req)) {
    return NextResponse.json({ error: '未授权' }, { status: 401 });
  }

  const startTime = Date.now();
  const results: Record<string, { count: number; error?: string }> = {};

  try {
    // 查找活跃店铺
    const shop = await prisma.shop.findFirst({ where: { active: true } });
    if (!shop) {
      return NextResponse.json({ ok: false, error: '无活跃店铺' }, { status: 404 });
    }

    const client = createShoplazzaClient();
    if (!client) {
      return NextResponse.json({ ok: false, error: 'Shoplazza 客户端创建失败' }, { status: 500 });
    }

    // 同步商品
    const productSyncLog = await prisma.syncLog.create({
      data: { shopId: shop.id, entity: 'products', action: 'cron_auto', status: 'running' },
    });
    try {
      const products = await client.listAllProducts();
      let count = 0;
      for (const p of products) {
        const price = p.price_min
          ? parseFloat(String(p.price_min))
          : p.variants?.[0]?.price
            ? parseFloat(String(p.variants[0].price))
            : 0;
        const imageSrcs = p.images?.map((i) => i.src) ?? [];

        await prisma.product.upsert({
          where: { shopId_externalId: { shopId: shop.id, externalId: p.id } },
          update: {
            title: p.title,
            description: p.description ?? null,
            price,
            images: JSON.stringify(imageSrcs),
            status: p.published ? 'active' : 'draft',
            lastSyncedAt: new Date(),
          },
          create: {
            shopId: shop.id,
            externalId: p.id,
            title: p.title,
            description: p.description ?? null,
            price,
            images: JSON.stringify(imageSrcs),
            status: p.published ? 'active' : 'draft',
            currency: 'USD',
          },
        });
        count++;
      }
      await prisma.syncLog.update({
        where: { id: productSyncLog.id },
        data: { status: 'success', count, finishedAt: new Date() },
      });
      results.products = { count };
    } catch (err) {
      const msg = err instanceof ShoplazzaError ? err.message : String(err);
      await prisma.syncLog.update({
        where: { id: productSyncLog.id },
        data: { status: 'failed', error: msg, finishedAt: new Date() },
      });
      results.products = { count: 0, error: msg };
    }

    // 同步订单
    const orderSyncLog = await prisma.syncLog.create({
      data: { shopId: shop.id, entity: 'orders', action: 'cron_auto', status: 'running' },
    });
    try {
      const orders = await client.listAllOrders();
      let count = 0;
      for (const o of orders) {
        const status = mapOrderStatus(o.financial_status, o.fulfillment_status);
        await prisma.order.upsert({
          where: { shopId_externalId: { shopId: shop.id, externalId: o.id } },
          update: {
            orderNo: o.order_number || o.name || o.id,
            amount: o.total_price ? parseFloat(String(o.total_price)) : 0,
            status,
            customerName: o.customer?.name ?? null,
            customerEmail: o.customer?.email ?? null,
            itemCount: o.line_items?.reduce((sum: number, li: any) => sum + li.quantity, 0) ?? 0,
            rawData: JSON.stringify(o),
          },
          create: {
            shopId: shop.id,
            externalId: o.id,
            orderNo: o.order_number || o.name || o.id,
            amount: o.total_price ? parseFloat(String(o.total_price)) : 0,
            status,
            customerName: o.customer?.name ?? null,
            customerEmail: o.customer?.email ?? null,
            itemCount: o.line_items?.reduce((sum: number, li: any) => sum + li.quantity, 0) ?? 0,
            currency: 'USD',
            rawData: JSON.stringify(o),
          },
        });
        count++;
      }
      await prisma.syncLog.update({
        where: { id: orderSyncLog.id },
        data: { status: 'success', count, finishedAt: new Date() },
      });
      results.orders = { count };
    } catch (err) {
      const msg = err instanceof ShoplazzaError ? err.message : String(err);
      await prisma.syncLog.update({
        where: { id: orderSyncLog.id },
        data: { status: 'failed', error: msg, finishedAt: new Date() },
      });
      results.orders = { count: 0, error: msg };
    }

    const duration = Date.now() - startTime;
    const hasError = Object.values(results).some((r) => r.error);

    return NextResponse.json({
      ok: !hasError,
      results,
      shopId: shop.id,
      shopName: shop.name,
      duration: `${(duration / 1000).toFixed(1)}s`,
      syncedAt: new Date().toISOString(),
    });
  } catch (error) {
    return NextResponse.json(
      { ok: false, error: '同步失败', detail: error instanceof Error ? error.message : undefined },
      { status: 500 }
    );
  }
}

/** Shoplazza 状态 → 内部统一状态 */
function mapOrderStatus(financial?: string, fulfillment?: string): string {
  if (financial === 'refunded' || financial === 'voided') return 'refunded';
  if (fulfillment === 'fulfilled') return 'fulfilled';
  if (financial === 'paid') return 'paid';
  if (financial === 'pending' || financial === 'authorized') return 'pending';
  return 'pending';
}

/**
 * GET /api/cron/sync — 查看最近同步日志
 */
export async function GET() {
  const logs = await prisma.syncLog.findMany({
    where: { action: 'cron_auto' },
    orderBy: { startedAt: 'desc' },
    take: 10,
    select: {
      id: true,
      entity: true,
      status: true,
      count: true,
      error: true,
      startedAt: true,
      finishedAt: true,
    },
  });

  return NextResponse.json({
    ok: true,
    recentSyncs: logs,
    tip: '用 POST 触发自动同步，建议每 15 分钟执行一次',
  });
}
