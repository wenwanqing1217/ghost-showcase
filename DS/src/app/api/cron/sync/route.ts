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
import { OneBoundClient, OneBoundError } from '@/lib/onebound';
import { getTenantId, tenantWhere, tenantCreateData } from '@/lib/tenant';
import crypto from 'crypto';

export const dynamic = 'force-dynamic';
export const maxDuration = 120; // 最长运行 2 分钟

const CRON_SECRET = process.env.CRON_SECRET || '';

/**
 * Bearer Token 验证
 *
 * 安全策略：未配置密钥时拒绝所有请求（fail-closed），避免未授权触发同步
 */
function verifyAuth(req: NextRequest): boolean {
  if (!CRON_SECRET) {
    console.error('[Cron] CRON_SECRET 未配置，拒绝请求');
    return false;
  }
  const auth = req.headers.get('authorization');
  // 使用 timingSafeEqual 防止时序攻击
  const expected = `Bearer ${CRON_SECRET}`;
  if (!auth || auth.length !== expected.length) return false;
  return crypto.timingSafeEqual(Buffer.from(auth), Buffer.from(expected));
}

export async function POST(req: NextRequest) {
  if (!verifyAuth(req)) {
    return NextResponse.json({ error: '未授权' }, { status: 401 });
  }

  const startTime = Date.now();
  const results: Record<string, { count: number; error?: string }> = {};

  try {
    // 查找活跃店铺（tenant 隔离）
    const tenantId = getTenantId(req);
    const shop = await prisma.shop.findFirst({
      where: { active: true, ...tenantWhere(tenantId) },
    });
    if (!shop) {
      return NextResponse.json({ ok: false, error: '无活跃货源连接' }, { status: 404 });
    }

    // 创建 OneBound 客户端
    let client: OneBoundClient;
    try {
      client = new OneBoundClient(shop.accessToken);
    } catch (err) {
      return NextResponse.json(
        { ok: false, error: `OneBound API Key 无效: ${err instanceof Error ? err.message : ''}` },
        { status: 500 }
      );
    }

    // 同步商品（从 OneBound 拉取货源商品）
    const productSyncLog = await prisma.syncLog.create({
      data: { shopId: shop.id, entity: 'products', action: 'cron_auto', status: 'running' },
    });
    try {
      const products = await client.listAllProducts();
      let count = 0;
      for (const p of products) {
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
          where: { shopId_externalId: { shopId: shop.id, externalId: String(p.id) } },
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
            shopId: shop.id,
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
        count++;
      }
      await prisma.syncLog.update({
        where: { id: productSyncLog.id },
        data: { status: 'success', count, finishedAt: new Date() },
      });
      results.products = { count };
    } catch (err) {
      const msg = err instanceof OneBoundError ? err.message : String(err);
      await prisma.syncLog.update({
        where: { id: productSyncLog.id },
        data: { status: 'failed', error: msg, finishedAt: new Date() },
      });
      results.products = { count: 0, error: msg };
    }

    // 同步订单（从 OneBound 拉取代发订单）
    const orderSyncLog = await prisma.syncLog.create({
      data: { shopId: shop.id, entity: 'orders', action: 'cron_auto', status: 'running' },
    });
    try {
      const orders = await client.listAllOrders();
      let count = 0;
      for (const o of orders) {
        const status = mapOneBoundStatus(o.status);
        const itemCount = o.items?.reduce((sum, li) => sum + (li.quantity || 0), 0) || 0;

        await prisma.order.upsert({
          where: { shopId_externalId: { shopId: shop.id, externalId: String(o.id) } },
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
            shopId: shop.id,
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
        count++;
      }
      await prisma.syncLog.update({
        where: { id: orderSyncLog.id },
        data: { status: 'success', count, finishedAt: new Date() },
      });
      results.orders = { count };
    } catch (err) {
      const msg = err instanceof OneBoundError ? err.message : String(err);
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
