/**
 * GET /api/content/generate/status/{task_id} — 查询内容生成任务状态
 *
 * 透传到 Ghost Gateway：
 *   GET http://localhost:18080/v1/content/video/status/{task_id}
 *
 * 返回完整的 Gateway 响应，包含：
 *   - state: 任务状态（0=待处理, 1=处理中, 2=已完成, 3=失败, 4=卡住需恢复）
 *   - progress: 完成百分比
 *   - videos: 生成视频 URL 列表
 *   - script: 视频脚本文本
 *   - recovery 数据（state=4 且 progress>=75% 时的恢复信息）
 *
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

  // 透传到 Gateway，自动转发 X-Tenant-ID 等关键 header
  const res = await proxyToGateway(req, `/v1/content/video/status/${encodeURIComponent(task_id)}`, {
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

  // 返回 Gateway 原始响应（包含 state, progress, videos, script, recovery 等完整数据）
  const data = await res.json().catch(() => ({ error: 'Gateway 返回无效响应' }));
  return NextResponse.json(data);
}
