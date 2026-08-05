/**
 * AI Assistant routes — AI 助手对话
 *
 * 提供对话会话管理和流式对话能力。
 * 实际 LLM 调用通过 Gateway 代理到 Alpha-ID。
 */
import { FastifyInstance } from 'fastify'
import type {
  AssistantSession,
  AssistantMessage,
  AssistantCapability,
} from '@mindflow/shared'

// ── 内存会话存储 ──
// 最大会话数，超过时驱逐最旧会话防止 OOM
const MAX_SESSIONS = 500
const sessions = new Map<string, AssistantSession>()

/** 带上限的 Map 插入：超过 MAX_SESSIONS 时驱逐最旧条目 */
function setSessionWithEviction(key: string, value: AssistantSession) {
  if (sessions.size >= MAX_SESSIONS) {
    const oldestKey = sessions.keys().next().value
    if (oldestKey !== undefined) sessions.delete(oldestKey)
  }
  sessions.set(key, value)
}

const capabilities: AssistantCapability[] = [
  { id: 'chat', name: '智能对话', description: '自然语言多轮对话', enabled: true, icon: '💬' },
  { id: 'workflow', name: '工作流', description: '执行预设工作流', enabled: true, icon: '⚙️' },
  { id: 'map', name: '地图导航', description: 'POI 搜索与路线规划', enabled: true, icon: '🗺️' },
  { id: 'computer', name: '浏览器控制', description: '自动化浏览器操作', enabled: false, icon: '🌐' },
]

export async function registerAidRoutes(app: FastifyInstance) {
  // 列出助手能力
  app.get('/capabilities', async () => {
    return { success: true, data: capabilities }
  })

  // 创建会话
  app.post('/sessions', async (request, reply) => {
    const userId = (request.body as { userId?: string })?.userId
    const session: AssistantSession = {
      id: `sess-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      userId,
      messages: [],
      context: {},
      createdAt: Date.now(),
      updatedAt: Date.now(),
    }
    setSessionWithEviction(session.id, session)
    return reply.status(201).send({ success: true, data: session })
  })

  // 获取会话
  app.get<{ Params: { id: string } }>(
    '/sessions/:id',
    async (request, reply) => {
      const session = sessions.get(request.params.id)
      if (!session) {
        return reply
          .status(404)
          .send({ success: false, error: '会话不存在' })
      }
      return { success: true, data: session }
    }
  )

  // 发送消息（非流式，返回完整回复）
  app.post<{ Params: { id: string }; Body: { message: string } }>(
    '/sessions/:id/messages',
    async (request, reply) => {
      const session = sessions.get(request.params.id)
      if (!session) {
        return reply
          .status(404)
          .send({ success: false, error: '会话不存在' })
      }

      const { message } = request.body || {}
      if (!message) {
        return reply
          .status(400)
          .send({ success: false, error: 'message 不能为空' })
      }

      // 用户消息
      const userMsg: AssistantMessage = {
        id: `msg-${Date.now()}-u`,
        role: 'user',
        content: message,
        timestamp: Date.now(),
      }
      session.messages.push(userMsg)

      // 模拟 AI 回复（实际应调用 LLM）
      const assistantMsg: AssistantMessage = {
        id: `msg-${Date.now()}-a`,
        role: 'assistant',
        content: `收到: "${message}"。这是一个模拟回复，实际部署时对接 LLM。`,
        timestamp: Date.now(),
      }
      session.messages.push(assistantMsg)
      session.updatedAt = Date.now()

      return { success: true, data: { user: userMsg, assistant: assistantMsg } }
    }
  )

  // 删除会话
  app.delete<{ Params: { id: string } }>(
    '/sessions/:id',
    async (request, reply) => {
      if (!sessions.has(request.params.id)) {
        return reply
          .status(404)
          .send({ success: false, error: '会话不存在' })
      }
      sessions.delete(request.params.id)
      return { success: true, data: { deleted: true } }
    }
  )
}
