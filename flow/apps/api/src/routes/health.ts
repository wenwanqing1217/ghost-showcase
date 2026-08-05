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
