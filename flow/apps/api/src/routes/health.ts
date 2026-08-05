/**
 * Health check endpoint
 */
import { FastifyInstance } from 'fastify'

export async function registerHealthRoutes(app: FastifyInstance) {
  app.get('/', async () => {
    return {
      success: true,
      data: {
        service: 'mindflow-api',
        version: '0.1.0',
        status: 'ok',
        timestamp: Date.now(),
      },
    }
  })

  // 详细健康检查（含依赖状态）
  app.get('/detailed', async () => {
    return {
      success: true,
      data: {
        service: 'mindflow-api',
        version: '0.1.0',
        status: 'ok',
        timestamp: Date.now(),
        uptime: process.uptime(),
        memory: process.memoryUsage(),
      },
    }
  })
}

/**
 * Prometheus 指标端点（/metrics，纯文本格式）
 * 供 gateway 聚合 /v1/internal/monitoring/metrics 与 Prometheus 抓取。
 */
export async function registerMetricsRoutes(app: FastifyInstance) {
  app.get('/metrics', async (_req, reply) => {
    const mem = process.memoryUsage()
    const body = [
      '# HELP flow_up MindFlow API up',
      '# TYPE flow_up gauge',
      'flow_up 1.0',
      '# HELP flow_uptime_seconds MindFlow API uptime',
      '# TYPE flow_uptime_seconds gauge',
      `flow_uptime_seconds ${process.uptime()}`,
      '# HELP process_resident_memory_bytes Resident memory bytes',
      '# TYPE process_resident_memory_bytes gauge',
      `process_resident_memory_bytes ${mem.rss}`,
    ].join('\n')
    reply.header('content-type', 'text/plain').send(body)
  })
}
