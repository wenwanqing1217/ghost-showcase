import { NextResponse } from 'next/server';
import { getProducts } from '@/lib/shopify/client';
import { defaultRateLimiter, rateLimitHeaders } from '@/lib/middleware/rate-limit';
import { logger } from '@/lib/observability/logger';

export async function GET(request: Request) {
  const rateLimit = await defaultRateLimiter(request);
  if (!rateLimit.success) {
    logger.warn('Shopify products rate limited', { remaining: rateLimit.remaining });
    return NextResponse.json(
      { success: false, error: 'Too many requests' },
      { status: 429, headers: rateLimitHeaders(rateLimit) }
    );
  }

  try {
    const products = await getProducts();
    return NextResponse.json({ success: true, data: products }, { headers: rateLimitHeaders(rateLimit) });
  } catch (error) {
    logger.error('Failed to fetch products', { error });
    return NextResponse.json(
      { success: false, error: 'Failed to fetch products' },
      { status: 500 }
    );
  }
}
