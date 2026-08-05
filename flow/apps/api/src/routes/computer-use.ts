/**
 * Computer Use routes — 浏览器自动化
 *
 * 提供浏览器截图、页面导航、元素操作能力。
 * 实际执行依赖 Playwright/Puppeteer，此处定义接口。
 */
import { FastifyInstance } from 'fastify'

// ── 任务状态 ──
type TaskStatus = 'pending' | 'running' | 'completed' | 'failed'

interface ComputerUseTask {
  id: string
  type: 'navigate' | 'screenshot' | 'click' | 'type' | 'extract'
  params: Record<string, unknown>
  status: TaskStatus
  result?: unknown
  error?: string
  createdAt: number
  completedAt?: number
}

const tasks = new Map<string, ComputerUseTask>()

export async function registerComputerUseRoutes(app: FastifyInstance) {
  // 浏览器状态
  app.get('/status', async () => {
    return {
      success: true,
      data: {
        available: false, // 需要 Playwright/Puppeteer 环境
        engine: 'playwright',
        message: '浏览器自动化需要安装 Playwright 并配置浏览器路径',
      },
    }
  })

  // 创建任务
  app.post<{
    Body: {
      type: 'navigate' | 'screenshot' | 'click' | 'type' | 'extract'
      params?: Record<string, unknown>
    }
  }>('/tasks', async (request, reply) => {
    const { type, params = {} } = request.body || {}
    const validTypes = ['navigate', 'screenshot', 'click', 'type', 'extract']

    if (!type || !validTypes.includes(type)) {
      return reply.status(400).send({
        success: false,
        error: `type 必须是之一: ${validTypes.join(', ')}`,
      })
    }

    const task: ComputerUseTask = {
      id: `task-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      type,
      params,
      status: 'pending',
      createdAt: Date.now(),
    }
    tasks.set(task.id, task)

    // 模拟任务完成
    task.status = 'completed'
    task.completedAt = Date.now()
    task.result = {
      message: `任务 ${type} 已模拟完成（需要 Playwright 环境才能真正执行）`,
      params,
    }

    return reply.status(201).send({ success: true, data: task })
  })

  // 查询任务
  app.get<{ Params: { id: string } }>(
    '/tasks/:id',
    async (request, reply) => {
      const task = tasks.get(request.params.id)
      if (!task) {
        return reply
          .status(404)
          .send({ success: false, error: '任务不存在' })
      }
      return { success: true, data: task }
    }
  )

  // 列出任务
  app.get('/tasks', async () => {
    return { success: true, data: Array.from(tasks.values()).slice(-20) }
  })

  // 快速截图接口
  app.post<{ Body: { url: string } }>(
    '/screenshot',
    async (request, reply) => {
      const { url } = request.body || {}
      if (!url) {
        return reply
          .status(400)
          .send({ success: false, error: 'url 不能为空' })
      }

      // 模拟截图任务
      const task: ComputerUseTask = {
        id: `ss-${Date.now()}`,
        type: 'screenshot',
        params: { url },
        status: 'completed',
        result: {
          message: `截图已模拟完成（需要 Playwright 环境）`,
          url,
        },
        createdAt: Date.now(),
        completedAt: Date.now(),
      }
      tasks.set(task.id, task)

      return { success: true, data: task }
    }
  )
}
