import { NextResponse } from 'next/server';
import { generateListing } from '@/lib/agents/content-agent';
import { prisma } from '@/lib/db';
import { evaluateRules } from '@/lib/risk/rules';
import { strictRateLimiter, rateLimitHeaders } from '@/lib/middleware/rate-limit';
import { logger } from '@/lib/observability/logger';

export async function POST(request: Request) {
  const rateLimit = await strictRateLimiter(request);
  if (!rateLimit.success) {
    logger.warn('Content generation rate limited', { remaining: rateLimit.remaining });
    return NextResponse.json(
      { success: false, error: 'Too many requests' },
      { status: 429, headers: rateLimitHeaders(rateLimit) }
    );
  }

  try {
    const body = await request.json();
    const draft = await generateListing(body);

    const evaluation = evaluateRules({ text: draft.description });

    const approval = await prisma.approval.create({
      data: {
        workflowType: 'content_generation',
        status: 'pending',
        payload: JSON.stringify({ input: body, output: draft }),
      },
    });

    await prisma.agentRun.create({
      data: {
        agentType: 'content',
        input: JSON.stringify(body),
        output: JSON.stringify(draft),
        status: 'success',
        approvalId: approval.id,
      },
    });

    return NextResponse.json({
      success: true,
      data: draft,
      approvalId: approval.id,
      riskFlags: evaluation.filter((r) => !r.passed),
    }, { headers: rateLimitHeaders(rateLimit) });
  } catch (error) {
    logger.error('Failed to generate listing', { error });
    return NextResponse.json(
      { success: false, error: 'Failed to generate listing' },
      { status: 500 }
    );
  }
}
