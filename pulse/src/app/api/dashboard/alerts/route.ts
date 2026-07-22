import { NextResponse } from 'next/server';
import { prisma } from '@/lib/db';
import { logger } from '@/lib/observability/logger';

export async function GET(request: Request) {
  try {
    const alerts = await prisma.alert.findMany({
      orderBy: { createdAt: 'desc' },
      take: 50,
    });
    if (alerts.length > 0) {
      return NextResponse.json({ success: true, data: alerts });
    }

    const fallbackAlerts = [
      {
        id: 'alert-1',
        severity: 'error',
        category: 'inventory',
        message: 'Inventory Critical',
        metadata: JSON.stringify({ source: 'Warehouse' }),
        resolved: false,
        createdAt: new Date().toISOString(),
      },
      {
        id: 'alert-2',
        severity: 'warning',
        category: 'logistics',
        message: 'Shipping Delay',
        metadata: JSON.stringify({ source: 'Logistics' }),
        resolved: false,
        createdAt: new Date().toISOString(),
      },
    ];

    return NextResponse.json({ success: true, data: fallbackAlerts });
  } catch (error) {
    logger.error('Failed to fetch alerts', { error });
    return NextResponse.json({ success: false, data: [] });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const alert = await prisma.alert.create({
      data: {
        severity: body.severity || 'info',
        category: body.category || 'system',
        message: body.message || '',
        metadata: body.metadata ? JSON.stringify(body.metadata) : null,
      },
    });
    return NextResponse.json({ success: true, data: alert }, { status: 201 });
  } catch (error) {
    logger.error('Failed to create alert', { error });
    return NextResponse.json(
      { success: false, error: 'Failed to create alert' },
      { status: 500 }
    );
  }
}
