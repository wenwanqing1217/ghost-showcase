/**
 * MindFlow Map → DS Webhook 接收端点
 *
 * 接收来自 mindflow-map 的事件通知（审批完成、内容预审结果等），
 * 可选落库到 alerts 表。
 *
 * 认证：X-Service-Key 头（服务间调用）
 */

import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/db';
import { validateServiceKey } from '@/lib/middleware/service-auth';
import { logger } from '@/lib/observability/logger';

// 动态导出（避免构建时连接数据库）
export const dynamic = 'force-dynamic';

interface WebhookPayload {
  event: string;
  payload: Record<string, unknown>;
}

/**
 * POST /api/webhooks/mindflow-map
 * 接收 mindflow-map 事件
 */
export async function POST(request: NextRequest) {
  // 服务间认证
  const auth = validateServiceKey(request);
  if (!auth.valid) {
    logger.warn('Webhook auth failed', { error: auth.error });
    return NextResponse.json(
      { success: false, error: auth.error },
      { status: 401 },
    );
  }

  let body: WebhookPayload;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { success: false, error: 'Invalid JSON body' },
      { status: 400 },
    );
  }

  const { event, payload } = body;

  if (!event || typeof event !== 'string') {
    return NextResponse.json(
      { success: false, error: 'Missing or invalid event type' },
      { status: 400 },
    );
  }

  logger.info('Received webhook from mindflow-map', { event, payload });

  // 根据事件类型处理
  try {
    switch (event) {
      case 'approval.completed':
      case 'approval.rejected':
        // 审批结果 → 创建告警记录
        await prisma.alert.create({
          data: {
            severity: event === 'approval.rejected' ? 'high' : 'info',
            category: 'approval',
            message: String(payload.message || `Approval ${event}`),
            metadata: JSON.stringify(payload),
            resolved: false,
          },
        });
        break;

      case 'precheck.completed':
        // 内容预审完成
        await prisma.alert.create({
          data: {
            severity: payload.status === 'rejected' ? 'warning' : 'info',
            category: 'precheck',
            message: String(payload.title || 'Content precheck completed'),
            metadata: JSON.stringify(payload),
            resolved: true,
          },
        });
        break;

      case 'workflow.completed':
        // 工作流完成 → 仅记录日志
        logger.info('Workflow completed', { payload });
        break;

      default:
        // 未知事件 → 记录但不报错
        logger.warn('Unknown webhook event', { event, payload });
    }

    return NextResponse.json({ success: true, received: event });
  } catch (error) {
    logger.error('Webhook processing failed', { event, error });
    return NextResponse.json(
      { success: false, error: 'Processing failed' },
      { status: 500 },
    );
  }
}

/**
 * GET /api/webhooks/mindflow-map
 * 健康检查端点（验证 webhook 路径可达）
 */
export async function GET(request: NextRequest) {
  const auth = validateServiceKey(request);
  if (!auth.valid) {
    return NextResponse.json(
      { success: false, error: auth.error },
      { status: 401 },
    );
  }

  return NextResponse.json({
    service: 'ds-webhook',
    status: 'active',
    accepts: [
      'approval.completed',
      'approval.rejected',
      'precheck.completed',
      'workflow.completed',
    ],
  });
}
