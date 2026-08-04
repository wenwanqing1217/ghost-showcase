/**
 * POST /api/webhook/onebound — OneBound 事件接收端点
 *
 * 处理 OneBound 推送的实时事件（如配置了 webhook）：
 * - order.created → 新订单入库
 * - order.updated → 更新订单状态
 * - order.fulfilled → 订单发货
 * - product.updated → 商品更新
 *
 * 注：OneBound 为供应链代发平台，主要交互方式为 API 拉取。
 * 如 OneBound 支持 Webhook，可在此配置回调地址。
 * 回调地址：https://your-domain.com/api/webhook/onebound
 */

import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import crypto from 'crypto';
import { getEventBus, initEventBus } from '@/lib/eventbus';
import { Redis } from 'ioredis';

// Lazy EventBus initialization (Next.js doesn't have a server startup hook)
let eventBusInitialized = false;

async function ensureEventBus() {
  if (eventBusInitialized) return;
  try {
    const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';
    const redis = new Redis(redisUrl, {
      retryStrategy: (times) => Math.min(times * 200, 2000),
      maxRetriesPerRequest: 3,
    });
    initEventBus(redis);
    eventBusInitialized = true;
    console.log('[Webhook] EventBus initialized');
  } catch (e) {
    console.error('[Webhook] EventBus init failed:', e);
  }
}

export const dynamic = 'force-dynamic';

// Webhook 签名验证密钥（必须配置，否则拒绝所有请求）
const WEBHOOK_SECRET = process.env.ONEBOUND_WEBHOOK_SECRET || '';

/**
 * 验证 OneBound Webhook 签名
 */
function verifySignature(body: string, signature: string | null): boolean {
  if (!WEBHOOK_SECRET) {
    console.error('[Webhook] ONEBOUND_WEBHOOK_SECRET 未配置，拒绝请求');
    return false;
  }
  if (!signature) return false;

  const expected = crypto
    .createHmac('sha256', WEBHOOK_SECRET)
    .update(body)
    .digest('hex');

  const sigBuf = Buffer.from(signature);
  const expBuf = Buffer.from(expected);
  if (sigBuf.length !== expBuf.length) return false;

  return crypto.timingSafeEqual(sigBuf, expBuf);
}

/**
 * 发布事件到 Event Bus
 */
async function publishEvent(type: string, data: Record<string, unknown>, tenantId: string): Promise<void> {
  try {
    const bus = getEventBus();
    await bus.publish(type as any, data, { tenantId, source: 'onebound-webhook' });
  } catch (e) {
    console.error(`[Webhook] Failed to publish event ${type}:`, e);
  }
}

export async function POST(req: NextRequest) {
  // Ensure EventBus is initialized
  await ensureEventBus();

  const rawBody = await req.text();
  const signature = req.headers.get('x-onebound-signature');

  if (!verifySignature(rawBody, signature)) {
    return NextResponse.json({ error: '签名验证失败' }, { status: 401 });
  }

  let payload: any;
  try {
    payload = JSON.parse(rawBody);
  } catch {
    return NextResponse.json({ error: '无效的 JSON' }, { status: 400 });
  }

  const topic = payload.topic || payload.event || 'unknown';
  const data = payload.data || payload;

  console.log(`[Webhook] 收到事件: ${topic}`, JSON.stringify(data).slice(0, 200));

  try {
    switch (topic) {
      case 'order.created':
      case 'order.updated':
      case 'order.fulfilled':
        await handleOrderEvent(data, topic, reqTenantId(req));
        break;

      case 'product.updated':
        await handleProductEvent(data, reqTenantId(req));
        break;

      default:
        console.log(`[Webhook] 未处理的事件类型: ${topic}`);
    }

    return NextResponse.json({ ok: true, received: topic });
  } catch (error) {
    console.error('[Webhook] 处理失败:', error);
    return NextResponse.json(
      { error: '处理失败', detail: error instanceof Error ? error.message : undefined },
      { status: 500 }
    );
  }
}

/**
 * 处理订单事件 — 保存到 DB + 发布到 Event Bus
 */
async function handleOrderEvent(data: any, topic: string, tenantId?: string) {
  const externalId = data.id?.toString();
  if (!externalId) return;

  // 查找关联店铺（带 tenant 隔离）
  const shop = await prisma.shop.findFirst({
    where: { active: true, ...(tenantId ? { tenantId } : {}) },
  });
  if (!shop) return;

  // 映射状态
  let status = 'pending';
  if (topic === 'order.fulfilled' || data.status?.toLowerCase().includes('fulfill')) status = 'fulfilled';
  if (data.status?.toLowerCase().includes('paid') || data.status?.toLowerCase().includes('confirm')) status = 'paid';
  if (data.status?.toLowerCase().includes('cancel') || data.status?.toLowerCase().includes('refund')) status = 'cancelled';

  const orderData = {
    orderNo: data.order_number || data.name || data.id?.toString(),
    amount: parseFloat(data.total || data.amount || '0'),
    currency: data.currency || 'USD',
    status,
    customerName: data.shipping_address?.name || data.customer?.name || null,
    customerEmail: null,
    itemCount: data.items?.reduce((sum: number, li: any) => sum + (li.quantity || 0), 0) || 0,
    trackingNumber: data.tracking_number || null,
    trackingCompany: data.tracking_company || null,
    rawData: JSON.stringify(data),
  };

  // 获取店铺的 storeMode
  const storeMode = shop.storeMode || 'marketplace';

  await prisma.order.upsert({
    where: { shopId_externalId: { shopId: shop.id, externalId } },
    update: orderData,
    create: {
      shopId: shop.id,
      externalId,
      tenantId: shop.tenantId,
      ...orderData,
    },
  });

  // 发布事件到 Event Bus（触发履约流程）
  const eventType = topic.replace('order.', 'order:');
  await publishEvent(eventType, {
    orderId: externalId,
    shopId: shop.id,
    storeMode,
    items: data.items?.map((li: any) => ({
      productId: li.product_id || li.sku,
      quantity: li.quantity,
      title: li.title,
    })) || [],
    amount: parseFloat(data.total || data.amount || '0'),
  }, shop.tenantId);
}

/**
 * 处理商品事件
 */
async function handleProductEvent(data: any, tenantId?: string) {
  const externalId = data.id?.toString();
  if (!externalId) return;

  const shop = await prisma.shop.findFirst({
    where: { active: true, ...(tenantId ? { tenantId } : {}) },
  });
  if (!shop) return;

  const price = data.price || data.variants?.[0]?.price || 0;

  await prisma.product.upsert({
    where: { shopId_externalId: { shopId: shop.id, externalId } },
    update: {
      title: data.title || 'Untitled',
      description: data.description || null,
      price: parseFloat(String(price)),
      images: JSON.stringify(data.images?.map((i: any) => i.url || i.src) || []),
      status: data.status === 'active' || data.status === 'available' ? 'active' : 'draft',
      lastSyncedAt: new Date(),
    },
    create: {
      shopId: shop.id,
      externalId,
      tenantId: shop.tenantId,
      title: data.title || 'Untitled',
      description: data.description || null,
      price: parseFloat(String(price)),
      images: JSON.stringify(data.images?.map((i: any) => i.url || i.src) || []),
      status: data.status === 'active' || data.status === 'available' ? 'active' : 'draft',
      currency: data.currency || 'USD',
    },
  });

  await publishEvent('supply:product:updated', {
    productId: externalId,
    shopId: shop.id,
    title: data.title,
    price: parseFloat(String(price)),
  }, shop.tenantId);
}

/**
 * 从请求头提取租户 ID（Gateway 注入的 X-Tenant-ID）
 */
function reqTenantId(req: NextRequest): string {
  return req.headers.get('x-tenant-id')?.trim() || 'default';
}

/**
 * GET /api/webhook/onebound — Webhook 健康检查
 */
export async function GET() {
  return NextResponse.json({
    ok: true,
    message: 'OneBound Webhook 端点已就绪',
    supportedEvents: [
      'order.created',
      'order.updated',
      'order.fulfilled',
      'product.updated',
    ],
    configured: !!WEBHOOK_SECRET,
    note: 'OneBound 为供应链 API，主要交互方式为定时拉取同步。Webhook 为可选增强。',
  });
}

