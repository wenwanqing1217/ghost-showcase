/**
 * GET /api/content/game/status/{task_id} — 查询游戏生成任务状态
 *
 * 透传到 Ghost Gateway：
 *   GET http://localhost:18080/v1/content/game/status/{task_id}
 *
 * 游戏生成是同步的（template-based），状态通常直接返回 completed。
 * 前端轮询此端点以获取实时进度。
 */

import { NextRequest, NextResponse } from 'next/server';
import { proxyToGateway } from '@/lib/api-proxy';

export const dynamic = 'force-dynamic';

export async function GET(
  req: NextRequest,
  { params }: { params: { task_id: string } }
) {
  const { task_id } = params;

  if (!task_id || !task_id.trim()) {
    return NextResponse.json({ error: 'task_id 不能为空' }, { status: 400 });
  }

  // 透传到 Gateway 的游戏状态端点
  const res = await proxyToGateway(req, `/v1/content/game/status/${encodeURIComponent(task_id)}`, {
    method: 'GET',
    timeout: 15_000,
  });

  // Gateway 返回失败状态时透传错误信息
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({
      error: `Gateway 返回错误 (${res.status})`,
    }));
    return NextResponse.json(errorData, { status: res.status });
  }

  // 返回 Gateway 原始响应（包含 status, game_url 等完整数据）
  const data = await res.json().catch(() => ({ error: 'Gateway 返回无效响应' }));
  return NextResponse.json(data);
}
