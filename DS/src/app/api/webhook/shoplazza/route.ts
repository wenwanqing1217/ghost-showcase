/**
 * POST /api/webhook/shoplazza — Shoplazza Webhook 接收端点
 *
 * 处理 Shoplazza 推送的实时事件：
 * - orders/create → 新订单入库
 * - orders/updated → 更新订单状态
 * - orders/paid → 订单付款
 * - orders/fulfilled → 订单发货
 * - products/create → 新商品入库
 * - products/updated → 商品更新
 *
 * 配置方式：在 Shoplazza 后台 → 设置 → Webhook → 添加回调地址
 * 回调地址：https://your-domain.com/api/webhook/shoplazza
 */

import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import crypto from 'crypto';

export const dynamic = 'force-dynamic';

// Webhook 签名验证密钥（可选，从环境变量读取）
const WEBHOOK_SECRET = process.env.SHOPLAZZA_WEBHOOK_SECRET || '';

/**
 * 验证 Shoplazza Webhook 签名
 * Shoplazza 使用 HMAC-SHA256 签名，放在 X-Shoplazza-Signature 头
 */
function verifySignature(body: string, signature: string | null): boolean {
  if (!WEBHOOK_SECRET || !signature) return true; // 未配置密钥则跳过验证

  const expected = crypto
    .createHmac('sha256', WEBHOOK_SECRET)
    .update(body)
    .digest('hex');

  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  );
}

export async function POST(req: NextRequest) {
  const rawBody = await req.text();
  const signature = req.headers.get('x-shoplazza-signature');

  // 验证签名
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
      case 'orders/create':
      case 'orders/updated':
      case 'orders/paid':
      case 'orders/fulfilled':
        await handleOrderEvent(data, topic);
        break;

      case 'products/create':
      case 'products/updated':
        await handleProductEvent(data);
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
 * 处理订单事件
 */
async function handleOrderEvent(data: any, topic: string) {
  const externalId = data.id?.toString();
  if (!externalId) return;

  // 查找关联店铺
  const shop = await prisma.shop.findFirst({ where: { active: true } });
  if (!shop) return;

  // 映射状态
  let status = 'pending';
  if (topic === 'orders/paid' || data.financial_status === 'paid') status = 'paid';
  if (topic === 'orders/fulfilled' || data.fulfillment_status === 'fulfilled') status = 'fulfilled';
  if (data.financial_status === 'refunded') status = 'refunded';

  const orderData = {
    orderNo: data.order_number || data.name || data.id?.toString(),
    amount: parseFloat(data.total_price || '0'),
    currency: data.currency || 'USD',
    status,
    customerName: data.customer?.name || data.billing_address?.name || null,
    customerEmail: data.customer?.email || data.billing_address?.email || null,
    itemCount: data.line_items?.reduce((sum: number, li: any) => sum + (li.quantity || 0), 0) || 0,
    paidAt: data.financial_status === 'paid' ? new Date() : null,
    fulfilledAt: data.fulfillment_status === 'fulfilled' ? new Date() : null,
    rawData: JSON.stringify(data),
  };

  await prisma.order.upsert({
    where: { shopId_externalId: { shopId: shop.id, externalId } },
    update: orderData,
    create: {
      shopId: shop.id,
      externalId,
      ...orderData,
    },
  });
}

/**
 * 处理商品事件
 */
async function handleProductEvent(data: any) {
  const externalId = data.id?.toString();
  if (!externalId) return;

  const shop = await prisma.shop.findFirst({ where: { active: true } });
  if (!shop) return;

  const price = data.price_min || data.variants?.[0]?.price || 0;

  await prisma.product.upsert({
    where: { shopId_externalId: { shopId: shop.id, externalId } },
    update: {
      title: data.title || 'Untitled',
      description: data.description || null,
      price: parseFloat(price),
      images: JSON.stringify(data.images?.map((i: any) => i.src) || []),
      status: data.published ? 'active' : 'draft',
      lastSyncedAt: new Date(),
    },
    create: {
      shopId: shop.id,
      externalId,
      title: data.title || 'Untitled',
      description: data.description || null,
      price: parseFloat(price),
      images: JSON.stringify(data.images?.map((i: any) => i.src) || []),
      status: data.published ? 'active' : 'draft',
      currency: data.currency || 'USD',
    },
  });
}

/**
 * GET /api/webhook/shoplazza — Webhook 健康检查/验证用
 * 某些平台会用 GET 请求验证 webhook URL 是否有效
 */
export async function GET() {
  return NextResponse.json({
    ok: true,
    message: 'Shoplazza Webhook 端点已就绪',
    supportedEvents: [
      'orders/create',
      'orders/updated',
      'orders/paid',
      'orders/fulfilled',
      'products/create',
      'products/updated',
    ],
    configured: !!WEBHOOK_SECRET,
  });
}
