import { NextResponse } from 'next/server';
import { getDashboardMetrics } from '@/lib/db/metrics';
import { aiRateLimiter, rateLimitHeaders } from '@/lib/middleware/rate-limit';
import { logger } from '@/lib/observability/logger';

export async function GET(request: Request) {
  const rateLimit = await aiRateLimiter(request);
  if (!rateLimit.success) {
    logger.warn('Metrics rate limited', { remaining: rateLimit.remaining });
    return NextResponse.json(
      { success: false, error: 'Too many requests' },
      { status: 429, headers: rateLimitHeaders(rateLimit) }
    );
  }

  try {
    const metrics = await getDashboardMetrics();
    return NextResponse.json({ success: true, data: metrics }, { headers: rateLimitHeaders(rateLimit) });
  } catch (error) {
    logger.error('Failed to load metrics', { error });
    return NextResponse.json(
      { success: false, error: 'Failed to load metrics' },
      { status: 500 }
    );
  }
}
