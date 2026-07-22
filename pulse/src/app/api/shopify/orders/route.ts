import { NextResponse } from 'next/server';
import { getOrders } from '@/lib/shopify/client';
import { defaultRateLimiter, rateLimitHeaders } from '@/lib/middleware/rate-limit';
import { logger } from '@/lib/observability/logger';

export async function GET(request: Request) {
  const rateLimit = await defaultRateLimiter(request);
  if (!rateLimit.success) {
    logger.warn('Shopify orders rate limited', { remaining: rateLimit.remaining });
    return NextResponse.json(
      { success: false, error: 'Too many requests' },
      { status: 429, headers: rateLimitHeaders(rateLimit) }
    );
  }

  try {
    const orders = await getOrders();
    return NextResponse.json({ success: true, data: orders }, { headers: rateLimitHeaders(rateLimit) });
  } catch (error) {
    logger.error('Failed to fetch orders', { error });
    return NextResponse.json(
      { success: false, error: 'Failed to fetch orders' },
      { status: 500 }
    );
  }
}
