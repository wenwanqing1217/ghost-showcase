import { NextResponse } from 'next/server';
import { prisma } from '@/lib/db';
import { defaultRateLimiter, rateLimitHeaders } from '@/lib/middleware/rate-limit';
import { logger } from '@/lib/observability/logger';

export async function GET(request: Request) {
  const rateLimit = await defaultRateLimiter(request);
  if (!rateLimit.success) {
    logger.warn('Health check rate limited', { remaining: rateLimit.remaining });
    return NextResponse.json(
      { success: false, error: 'Too many requests' },
      { status: 429, headers: rateLimitHeaders(rateLimit) }
    );
  }

  const checks: {
    timestamp: string;
    status: 'healthy' | 'degraded';
    database: 'connected' | 'disconnected';
    demo: boolean;
    missing: string[];
  } = {
    timestamp: new Date().toISOString(),
    status: 'healthy',
    database: 'connected',
    demo: process.env.DEMO_MODE === 'true',
    missing: [],
  };

  // Check database connectivity
  try {
    await prisma.$queryRaw`SELECT 1`;
  } catch {
    checks.database = 'disconnected';
    checks.status = 'degraded';
  }

  // Check optional config (don't fail health check for missing optional keys)
  if (!process.env.OPENAI_API_KEY) checks.missing.push('OPENAI_API_KEY');
  if (!process.env.SHOPIFY_SHOP_DOMAIN) checks.missing.push('SHOPIFY_SHOP_DOMAIN');

  // In demo mode, missing keys are expected
  if (checks.demo && checks.database === 'connected') {
    checks.status = 'healthy';
  }

  const statusCode = checks.status === 'healthy' ? 200 : 503;
  return NextResponse.json(checks, { status: statusCode, headers: rateLimitHeaders(rateLimit) });
}
