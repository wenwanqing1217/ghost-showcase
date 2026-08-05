/**
 * GET /api/growth/stats?alpha_id=XXX — 代理到 Alpha-ID 成长统计
 *
 * 返回精灵形态、经验值、技能分布、进化阶段信息
 */

import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const ALPHA_ID_URL = process.env.ALPHA_ID_URL || 'http://localhost:8000';

export async function GET(req: NextRequest) {
  const alphaId = req.nextUrl.searchParams.get('alpha_id');
  if (!alphaId) {
    return NextResponse.json(
      { error: 'alpha_id 必填' },
      { status: 400 },
    );
  }

  try {
    const resp = await fetch(
      `${ALPHA_ID_URL}/growth/stats?alpha_id=${encodeURIComponent(alphaId)}`,
      { headers: { 'Content-Type': 'application/json' } },
    );
    const data = await resp.json();
    if (!resp.ok) {
      return NextResponse.json(
        { error: data.error || `Alpha-ID 返回 ${resp.status}` },
        { status: resp.status },
      );
    }
    return NextResponse.json(data);
  } catch (err) {
    console.error('[growth/stats] 代理失败:', err);
    // 返回 Demo 数据，保证页面可渲染
    return NextResponse.json({
      success: true,
      alpha_id: alphaId,
      demo: true,
      stats: {
        total_exp: 0,
        total_tasks: 0,
        tool_counts: {},
        stage_index: 0,
        stage_name: '种子',
        stage_emoji: '🌱',
        last_task_time: 0,
        last_task_tool: '',
        last_task_desc: '',
      },
      stage_info: {
        current: { name: '种子', min_exp: 0, emoji: '🌱' },
        next: { name: '幼生体', min_exp: 10, emoji: '🥚' },
        exp_to_next: 10,
        progress: 0,
      },
      stages: [
        { name: '种子', min_exp: 0, emoji: '🌱' },
        { name: '幼生体', min_exp: 10, emoji: '🥚' },
        { name: '成长期', min_exp: 50, emoji: '🌿' },
        { name: '成熟体', min_exp: 100, emoji: '🌳' },
        { name: '完全体', min_exp: 200, emoji: '✨' },
        { name: '超越体', min_exp: 500, emoji: '🔮' },
      ],
    });
  }
}
