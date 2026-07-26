/**
 * GET /api/ai/status — 检查 AI 服务状态
 * 始终返回可用（Demo 模式兜底）
 */

import { NextResponse } from 'next/server';
import { getAiMode } from '@/lib/ai';

export const dynamic = 'force-dynamic';

export async function GET() {
  const mode = getAiMode();

  return NextResponse.json({
    available: true,
    mode, // 'demo' | 'api'
    provider: mode === 'api'
      ? (process.env.AI_BASE_URL?.includes('groq') ? 'Groq' :
         process.env.AI_BASE_URL?.includes('deepseek') ? 'DeepSeek' : 'OpenAI-compatible')
      : 'Demo (本地模板)',
    model: process.env.AI_MODEL || 'llama-3.3-70b-versatile',
    baseUrl: process.env.AI_BASE_URL || 'https://api.groq.com/openai/v1',
    hint: mode === 'demo'
      ? '当前为 Demo 模式（无需 API Key）。设置 AI_API_KEY 可启用 Groq 免费额度或 DeepSeek。'
      : 'API 模式已启用',
  });
}
