/**
 * POST /api/ai/copy — 为商品生成 AI 文案
 * 有 API Key → 调外部 LLM（Groq/DeepSeek）
 * 无 API Key → Demo 模式（本地模板生成）
 *
 * body: { productId?, title, description?, tone?, lang?, save? }
 */

import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { generateProductCopy, getAiMode, ProductCopyInput } from '@/lib/ai';
import { z } from 'zod';

export const dynamic = 'force-dynamic';

const CopySchema = z.object({
  productId: z.string().optional(),
  title: z.string().min(1, '请输入商品标题'),
  description: z.string().optional(),
  keywords: z.array(z.string()).optional(),
  tone: z.enum(['professional', 'casual', 'luxury', 'fun']).default('professional'),
  lang: z.enum(['zh', 'en']).default('zh'),
  save: z.boolean().default(false),
});

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const input: ProductCopyInput = CopySchema.parse(body);

    const result = await generateProductCopy(input);

    // 保存到商品记录
    if (body.productId && body.save) {
      await prisma.product.update({
        where: { id: body.productId },
        data: {
          title: result.title,
          description: result.description,
        },
      });
    }

    return NextResponse.json({
      ok: true,
      mode: result.mode,
      result,
      saved: !!(body.productId && body.save),
    });
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
