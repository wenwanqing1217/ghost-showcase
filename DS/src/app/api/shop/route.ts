/**
 * GET  /api/shop     — 获取当前店铺信息
 * POST /api/shop     — 创建/更新店铺连接配置
 */

import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { ShoplazzaClient, ShoplazzaError } from '@/lib/shoplazza';
import { z } from 'zod';

export const dynamic = 'force-dynamic';

// ── GET：获取活跃店铺 ──
export async function GET() {
  try {
    const shop = await prisma.shop.findFirst({
      where: { active: true },
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

// ── POST：连接/更新店铺 ──
const ConnectSchema = z.object({
  domain: z.string().min(1, '请输入店铺域名'),
  accessToken: z.string().min(1, '请输入 Access Token'),
  name: z.string().optional(),
});

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { domain, accessToken, name } = ConnectSchema.parse(body);

    // 验证连接 — 调用 Shoplazza API
    const client = new ShoplazzaClient(domain, accessToken);
    const shopInfo = await client.getShopInfo();

    // upsert 店铺记录
    const shop = await prisma.shop.upsert({
      where: { domain },
      update: {
        accessToken,
        name: name || shopInfo.name || domain,
        active: true,
      },
      create: {
        domain,
        accessToken,
        name: name || shopInfo.name || domain,
        platform: 'shoplazza',
      },
    });

    return NextResponse.json({
      ok: true,
      shop: {
        id: shop.id,
        name: shop.name,
        domain: shop.domain,
        shopInfo,
      },
    });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: '参数校验失败', details: error.errors },
        { status: 400 }
      );
    }
    if (error instanceof ShoplazzaError) {
      return NextResponse.json(
        { error: `Shoplazza 连接失败: ${error.message}`, status: error.status },
        { status: 401 }
      );
    }
    return NextResponse.json(
      { error: '服务器错误', detail: error instanceof Error ? error.message : undefined },
      { status: 500 }
    );
  }
}
