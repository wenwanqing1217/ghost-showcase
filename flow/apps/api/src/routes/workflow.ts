/**
 * Workflow routes — 工作流管理与执行
 *
 * 提供工作流模板查询、执行触发、结果查询能力。
 */
import { FastifyInstance } from 'fastify'
import type {
  Workflow,
  WorkflowTemplate,
  WorkflowExecutionResult,
  ExecuteWorkflowRequest,
} from '@mindflow/shared'

// ── 内存存储（生产环境应替换为数据库） ──
// 最大执行记录数，超过时驱逐最旧记录防止 OOM
const MAX_EXECUTIONS = 1000
const executions = new Map<string, WorkflowExecutionResult>()

/** 带上限的 Map 插入：超过 MAX_EXECUTIONS 时驱逐最旧条目 */
function setWithEviction(key: string, value: WorkflowExecutionResult) {
  if (executions.size >= MAX_EXECUTIONS) {
    // 驱逐最早插入的条目（Map 保持插入顺序）
    const oldestKey = executions.keys().next().value
    if (oldestKey !== undefined) executions.delete(oldestKey)
  }
  executions.set(key, value)
}
const templates: WorkflowTemplate[] = [
  {
    id: 'tpl-greeting',
    name: '问候回复',
    description: '根据用户输入生成友好回复',
    trigger: { type: 'intent', patterns: ['你好', 'hello', 'hi'] },
    workflow: {
      id: 'wf-greeting',
      name: '问候回复',
      description: '简单问候回复工作流',
      nodes: [
        { id: 'n1', type: 'trigger', name: '用户输入' },
        { id: 'n2', type: 'llm', name: '生成回复' },
        { id: 'n3', type: 'output', name: '输出' },
      ],
      edges: [
        { from: 'n1', to: 'n2' },
        { from: 'n2', to: 'n3' },
      ],
    },
  },
  {
    id: 'tpl-search',
    name: '信息搜索',
    description: '搜索并汇总相关信息',
    trigger: { type: 'intent', patterns: ['搜索', '查找', 'search'] },
    workflow: {
      id: 'wf-search',
      name: '信息搜索',
      description: '搜索并汇总信息工作流',
      nodes: [
        { id: 'n1', type: 'trigger', name: '用户查询' },
        { id: 'n2', type: 'search', name: '网络搜索' },
        { id: 'n3', type: 'llm', name: '汇总结果' },
        { id: 'n4', type: 'output', name: '输出' },
      ],
      edges: [
        { from: 'n1', to: 'n2' },
        { from: 'n2', to: 'n3' },
        { from: 'n3', to: 'n4' },
      ],
    },
  },
]

export async function registerWorkflowRoutes(app: FastifyInstance) {
  // 列出所有工作流模板
  app.get('/templates', async () => {
    return { success: true, data: templates }
  })

  // 获取单个模板
  app.get<{ Params: { id: string } }>('/templates/:id', async (request, reply) => {
    const tpl = templates.find((t) => t.id === request.params.id)
    if (!tpl) {
      return reply.status(404).send({ success: false, error: '模板不存在' })
    }
    return { success: true, data: tpl }
  })

  // 执行工作流
  app.post<{ Body: ExecuteWorkflowRequest }>(
    '/execute',
    async (request, reply) => {
      const { message, userId } = request.body || {}
      if (!message) {
        return reply
          .status(400)
          .send({ success: false, error: 'message 不能为空' })
      }

      // 匹配模板
      const matched = templates.find((t) =>
        t.trigger.patterns.some((p) =>
          message.toLowerCase().includes(p.toLowerCase())
        )
      )

      if (!matched) {
        return reply.status(404).send({
          success: false,
          error: '没有匹配的工作流模板',
          available: templates.map((t) => ({ id: t.id, name: t.name })),
        })
      }

      // 模拟执行
      const executionId = `exec-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
      const result: WorkflowExecutionResult = {
        success: true,
        workflowId: matched.workflow.id,
        workflowName: matched.workflow.name,
        result: `已执行工作流 "${matched.workflow.name}"，输入: "${message}"`,
        steps: matched.workflow.nodes.map((node) => ({
          nodeId: node.id,
          nodeName: node.name,
          status: 'success',
          output: `节点 ${node.name} 执行完成`,
          duration: Math.floor(Math.random() * 100) + 10,
        })),
      }

      setWithEviction(executionId, result)

      return {
        success: true,
        data: { executionId, ...result },
      }
    }
  )

  // 查询执行结果
  app.get<{ Params: { id: string } }>(
    '/executions/:id',
    async (request, reply) => {
      const result = executions.get(request.params.id)
      if (!result) {
        return reply
          .status(404)
          .send({ success: false, error: '执行记录不存在' })
      }
      return { success: true, data: result }
    }
  )

  // 列出最近执行记录
  app.get('/executions', async () => {
    const list = Array.from(executions.entries()).map(([id, result]) => ({
      executionId: id,
      ...result,
    }))
    return { success: true, data: list.slice(-20) }
  })
}
