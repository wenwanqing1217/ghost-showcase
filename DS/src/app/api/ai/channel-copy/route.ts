/**
 * POST /api/ai/channel-copy — 生成闲鱼/小红书渠道文案
 *
 * 低成本出海/变现：用户输入商品信息，生成两个渠道的原生文案 + 发布清单。
 * 复用 lib/ai.ts：有 AI_API_KEY 走 LLM，无 Key 走本地模板（零成本）。
 *
 * body: { platform: 'xianyu' | 'xiaohongshu', product, description?, price?, condition?, tone? }
 */

import { NextRequest, NextResponse } from 'next/server';
import { generateChannelCopy, ChannelCopyInput } from '@/lib/ai';
import { z } from 'zod';

export const dynamic = 'force-dynamic';

const Schema = z.object({
  platform: z.enum(['xianyu', 'xiaohongshu', 'douyin']),
  product: z.string().min(1, '请输入商品名/主题'),
  description: z.string().optional(),
  price: z.string().optional(),
  condition: z.string().optional(),
  tone: z.enum(['professional', 'casual', 'luxury', 'fun']).default('casual'),
});

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const input: ChannelCopyInput = Schema.parse(body);
    const result = await generateChannelCopy(input);
    return NextResponse.json({ ok: true, result });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: '参数校验失败', details: error.errors },
        { status: 400 }
      );
    }
    return NextResponse.json(
      { error: error instanceof Error ? error.message : '生成失败' },
      { status: 500 }
    );
  }
}
