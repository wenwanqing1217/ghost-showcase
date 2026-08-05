/**
 * GET /api/products/[id] — 商品详情
 *
 * C 端公开访问（无需登录），但仅返回 status=active 的商品。
 * B 端管理可带 ?include=draft 查看非活跃商品（需 DS_API_KEY）。
 *
 * 租户隔离：通过 Gateway 注入的 X-Tenant-ID header 过滤。
 */

import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { getTenantId, tenantWhere } from '@/lib/tenant';
import { withMetrics } from '@/app/api/metrics/route';

export const dynamic = 'force-dynamic';

async function handler(
  req: NextRequest,
  { params }: { params: { id: string } },
): Promise<NextResponse> {
  const tenantId = getTenantId(req);
  const { id } = params;

  if (!id) {
    return NextResponse.json({ error: '商品 ID 必填' }, { status: 400 });
  }

  // C 端默认只看 active；管理端可带 ?include=draft（需 API Key）
  const includeDraft = req.nextUrl.searchParams.get('include') === 'draft';
  const apiKey = process.env.DS_API_KEY;
  const canSeeDraft = includeDraft && apiKey && req.headers.get('x-api-key') === apiKey;
  const statusFilter = canSeeDraft ? {} : { status: 'active' };

  const product = await prisma.product.findFirst({
    where: tenantWhere(tenantId, {
      id,
      ...statusFilter,
    }),
    select: {
      id: true,
      externalId: true,
      title: true,
      description: true,
      price: true,
      comparePrice: true,
      currency: true,
      inventory: true,
      images: true,
      status: true,
      lastSyncedAt: true,
      shop: {
        select: {
          id: true,
          name: true,
          domain: true,
        },
      },
    },
  });

  if (!product) {
    return NextResponse.json({ error: '商品不存在或已下架' }, { status: 404 });
  }

  return NextResponse.json({ item: product });
}

export const GET = withMetrics(handler, 'GET /api/products/[id]');
