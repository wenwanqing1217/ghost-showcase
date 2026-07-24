/**
 * GET /api/health
 * 健康检查端点 — Docker / 负载均衡器探活
 */

import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    // 检查数据库连通性
    await prisma.$queryRaw`SELECT 1`;

    return NextResponse.json({
      status: 'ok',
      service: 'ghost-ds',
      timestamp: new Date().toISOString(),
      database: 'connected',
      demo: process.env.DEMO_MODE === 'true',
    });
  } catch (error) {
    return NextResponse.json(
      {
        status: 'error',
        service: 'ghost-ds',
        timestamp: new Date().toISOString(),
        database: 'disconnected',
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 503 }
    );
  }
}
