import { NextResponse } from 'next/server';
import { prisma } from '@/lib/db';
import { defaultRateLimiter, rateLimitHeaders } from '@/lib/middleware/rate-limit';
import { logger } from '@/lib/observability/logger';
import { approvalSchema, validateBody } from '@/lib/validation/schemas';

export async function POST(request: Request) {
  const rateLimit = await defaultRateLimiter(request);
  if (!rateLimit.success) {
    logger.warn('Content approval rate limited', { remaining: rateLimit.remaining });
    return NextResponse.json(
      { success: false, error: 'Too many requests' },
      { status: 429, headers: rateLimitHeaders(rateLimit) }
    );
  }

  try {
    const body = await request.json();

    // Validate input
    const validation = validateBody(approvalSchema, body);
    if (!validation.success) {
      return NextResponse.json(
        { success: false, error: 'Validation failed', details: validation.errors },
        { status: 400, headers: rateLimitHeaders(rateLimit) }
      );
    }

    const { approvalId, status } = validation.data;

    // Check existence before update
    const existing = await prisma.approval.findUnique({ where: { id: approvalId } });
    if (!existing) {
      return NextResponse.json(
        { success: false, error: 'Approval not found' },
        { status: 404, headers: rateLimitHeaders(rateLimit) }
      );
    }

    const approval = await prisma.approval.update({
      where: { id: approvalId },
      data: {
        status,
        decidedAt: new Date(),
        result: status === 'approved' ? 'Approved by user' : 'Rejected by user',
      },
    });

    return NextResponse.json({ success: true, approval }, { headers: rateLimitHeaders(rateLimit) });
  } catch (error) {
    logger.error('Failed to update approval', { error });
    return NextResponse.json(
      { success: false, error: 'Failed to update approval' },
      { status: 500 }
    );
  }
}
