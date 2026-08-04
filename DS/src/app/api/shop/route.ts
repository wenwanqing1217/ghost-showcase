/**
 * GET  /api/shop     — 获取当前店铺信息
 * POST /api/shop     — 创建/更新店铺连接配置
 */

import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { OneBoundClient, OneBoundError } from '@/lib/onebound';
import { getTenantId, tenantWhere } from '@/lib/tenant';
import { z } from 'zod';

export const dynamic = 'force-dynamic';

// ── GET：获取当前租户的活跃店铺 ──
export async function GET(req: NextRequest) {
  try {
    const tenantId = getTenantId(req);
    const shop = await prisma.shop.findFirst({
      where: { active: true, ...tenantWhere(tenantId) },
      select: {
        id: true,
        name: true,
        domain: true,
        platform: true,
        active: true,
        createdAt: true,
        accessToken: false, // 不返回 token
        _count: { select: { products: true, orders: true } },
      },
    });

    if (!shop) {
      return NextResponse.json({ shop: null, demo: true });
    }

    return NextResponse.json({ shop, demo: false });
  } catch (error) {
    return NextResponse.json(
      { error: '查询失败', detail: error instanceof Error ? error.message : undefined },
      { status: 500 }
    );
  }
}

// ── POST：连接 OneBound 货源 ──
const ConnectSchema = z.object({
  apiKey: z.string().min(10, 'API Key 至少 10 个字符'),
  name: z.string().optional(),
  storeMode: z.enum(['marketplace', 'independent', 'both']).optional(),
});

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { apiKey, name, storeMode } = ConnectSchema.parse(body);
    const tenantId = getTenantId(req);

    // 验证 API Key — 调用 OneBound API
    const client = new OneBoundClient(apiKey);
    const sourceInfo = await client.getProduct('1').catch(() => ({} as any));
    const isValid = !(sourceInfo instanceof OneBoundError);

    if (!isValid) {
      return NextResponse.json(
        { error: 'OneBound API Key 无效，请检查' },
        { status: 401 }
      );
    }

    // 使用 API Key 的指纹作为 domain（全局唯一标识）
    const domainHash = apiKey.slice(-8);
    const shopName = name || `OneBound 货源 #${domainHash}`;

    // upsert 店铺记录（tenant 隔离）
    const shop = await prisma.shop.upsert({
      where: { domain: `onebound-${domainHash}` },
      update: {
        accessToken: apiKey,
        name: shopName,
        active: true,
        platform: 'onebound',
        tenantId,
        storeMode: storeMode || 'marketplace',
      },
      create: {
        domain: `onebound-${domainHash}`,
        accessToken: apiKey,
        name: shopName,
        platform: 'onebound',
        tenantId,
        storeMode: storeMode || 'marketplace',
      },
    });

    return NextResponse.json({
      ok: true,
      shop: {
        id: shop.id,
        name: shop.name,
        domain: shop.domain,
        platform: shop.platform,
        storeMode: shop.storeMode,
      },
    });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: '参数校验失败', details: error.errors },
        { status: 400 }
      );
    }
    if (error instanceof OneBoundError) {
      return NextResponse.json(
        { error: `OneBound 连接失败: ${error.message}`, status: error.status },
        { status: 401 }
      );
    }
    return NextResponse.json(
      { error: '服务器错误', detail: error instanceof Error ? error.message : undefined },
      { status: 500 }
    );
  }
}

// ── PATCH：更新店铺模式（集市/独立站切换）──
const UpdateModeSchema = z.object({
  storeMode: z.enum(['marketplace', 'independent', 'both']),
});

export async function PATCH(req: NextRequest) {
  try {
    const body = await req.json();
    const { storeMode } = UpdateModeSchema.parse(body);
    const tenantId = getTenantId(req);

    const shop = await prisma.shop.findFirst({
      where: { active: true, ...tenantWhere(tenantId) },
    });

    if (!shop) {
      return NextResponse.json({ error: '未找到店铺' }, { status: 404 });
    }

    const updated = await prisma.shop.update({
      where: { id: shop.id },
      data: { storeMode },
      select: {
        id: true,
        name: true,
        domain: true,
        storeMode: true,
        platform: true,
        active: true,
      },
    });

    return NextResponse.json({ ok: true, shop: updated });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: '参数校验失败', details: error.errors },
        { status: 400 }
      );
    }
    return NextResponse.json(
      { error: '更新失败', detail: error instanceof Error ? error.message : undefined },
      { status: 500 }
    );
  }
}

// ── DELETE：断开店铺连接 ──
export async function DELETE(req: NextRequest) {
  try {
    const tenantId = getTenantId(req);

    const shop = await prisma.shop.findFirst({
      where: { active: true, ...tenantWhere(tenantId) },
    });

    if (!shop) {
      return NextResponse.json({ error: '未找到活跃店铺' }, { status: 404 });
    }

    await prisma.shop.update({
      where: { id: shop.id },
      data: { active: false },
    });

    return NextResponse.json({ ok: true, message: '店铺已断开' });
  } catch (error) {
    return NextResponse.json(
      { error: '断开失败', detail: error instanceof Error ? error.message : undefined },
      { status: 500 }
    );
  }
}
