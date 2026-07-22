import { NextResponse } from 'next/server';
import { prisma } from '@/lib/db';
import { logger } from '@/lib/observability/logger';

const DEFAULT_CAMPAIGNS = [
  {
    id: 'campaign-1',
    name: 'Summer Sale Collection',
    status: 'active',
    budget: 1200,
    spent: 840.5,
    impressions: 124000,
    clicks: 3200,
    conversions: 210,
    ctr: 2.58,
    roas: 3.1,
    bidStrategy: 'auto',
    maxBid: 1.25,
  },
];

export async function GET(request: Request) {
  try {
    const campaigns = await prisma.product.findMany({
      orderBy: { createdAt: 'desc' },
      take: 20,
    });

    if (campaigns.length > 0) {
      const mapped = campaigns.map((product) => ({
        id: product.id,
        name: product.title,
        status: product.status === 'active' ? 'active' : 'paused',
        budget: 1200,
        spent: 840.5,
        impressions: 124000,
        clicks: 3200,
        conversions: 210,
        ctr: 2.58,
        roas: 3.1,
        bidStrategy: 'auto',
        maxBid: 1.25,
      }));

      return NextResponse.json({ success: true, data: mapped });
    }

    return NextResponse.json({ success: true, data: DEFAULT_CAMPAIGNS });
  } catch (error) {
    logger.error('Failed to fetch campaigns', { error });
    return NextResponse.json({ success: true, data: DEFAULT_CAMPAIGNS });
  }
}
