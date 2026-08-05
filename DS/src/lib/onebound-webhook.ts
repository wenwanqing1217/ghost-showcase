/**
 * OneBound Webhook 辅助函数 — 签名验证 + 事件发布
 *
 * 从路由文件抽离，遵守 Next.js 路由文件只允许导出 HTTP 方法的规定。
 */

import crypto from 'crypto';
import { getEventBusInstance } from '@/lib/eventbus-init';

// Webhook 签名验证密钥（必须配置，否则拒绝所有请求）
const WEBHOOK_SECRET = process.env.ONEBOUND_WEBHOOK_SECRET || '';

/**
 * 验证 OneBound Webhook 签名
 */
export function verifySignature(body: string, signature: string | null): boolean {
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
export async function publishEvent(
  type: string,
  data: Record<string, unknown>,
  tenantId: string,
): Promise<void> {
  try {
    const bus = getEventBusInstance();
    await bus.publish(type as any, data, { tenantId, source: 'onebound-webhook' });
  } catch (e) {
    console.error(`[Webhook] Failed to publish event ${type}:`, e);
  }
}
