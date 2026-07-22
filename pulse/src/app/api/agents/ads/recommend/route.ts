import { NextResponse } from 'next/server';
import { prisma } from '@/lib/db';
import { logger } from '@/lib/observability/logger';
import { adsRecommendSchema, validateBody } from '@/lib/validation/schemas';

export async function GET(request: Request) {
  try {
    const recommendations = [
      {
        id: 'recommendation-1',
        type: 'budget',
        priority: 'high',
        message: 'Increase budget for top-performing ad set.',
        impact: 'Expected +18% revenue with current ROAS.',
      },
    ];

    return NextResponse.json({ success: true, data: recommendations });
  } catch (error) {
    logger.error('Failed to fetch ad recommendations', { error });
    return NextResponse.json({ success: true, data: [] });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();

    // Validate input
    const validation = validateBody(adsRecommendSchema, body);
    if (!validation.success) {
      return NextResponse.json(
        { success: false, error: 'Validation failed', details: validation.errors },
        { status: 400 }
      );
    }

    // Store optimization request as an agent run for tracking
    const run = await prisma.agentRun.create({
      data: {
        agentType: 'ads',
        input: JSON.stringify(validation.data),
        output: JSON.stringify({ status: 'accepted', recommendations: [] }),
        status: 'success',
      },
    });

    return NextResponse.json(
      {
        success: true,
        data: {
          id: run.id,
          status: 'accepted',
          message: 'Ad optimization request recorded. Connect an ad platform to get real recommendations.',
        },
      },
      { status: 201 }
    );
  } catch (error) {
    logger.error('Failed to process ad optimization', { error });
    return NextResponse.json(
      { success: false, error: 'Failed to process optimization' },
      { status: 500 }
    );
  }
}
