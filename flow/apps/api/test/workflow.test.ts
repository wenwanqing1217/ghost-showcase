import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import Fastify from 'fastify'
import cors from '@fastify/cors'
import { registerWorkflowRoutes } from '../src/routes/workflow'

describe('Workflow Routes', () => {
  const app = Fastify()
  beforeAll(async () => {
    await app.register(cors, { origin: ['http://localhost:3000'] })
    await app.register(registerWorkflowRoutes, { prefix: '/workflow' })
    await app.ready()
  })
  afterAll(async () => {
    await app.close()
  })

  it('GET /workflow/templates returns template list', async () => {
    const res = await app.inject({ method: 'GET', url: '/workflow/templates' })
    expect(res.statusCode).toBe(200)
    const body = res.json()
    expect(body.success).toBe(true)
    expect(body.data).toBeInstanceOf(Array)
    expect(body.data.length).toBeGreaterThan(0)
    expect(body.data[0].id).toBeDefined()
    expect(body.data[0].name).toBeDefined()
  })

  it('GET /workflow/templates/:id returns single template', async () => {
    const res = await app.inject({ method: 'GET', url: '/workflow/templates/tpl-greeting' })
    expect(res.statusCode).toBe(200)
    const body = res.json()
    expect(body.success).toBe(true)
    expect(body.data.id).toBe('tpl-greeting')
  })

  it('GET /workflow/templates/:id returns 404 for unknown', async () => {
    const res = await app.inject({ method: 'GET', url: '/workflow/templates/nonexistent' })
    expect(res.statusCode).toBe(404)
  })

  it('POST /workflow/execute matches template and runs', async () => {
    const res = await app.inject({
      method: 'POST',
      url: '/workflow/execute',
      payload: { message: 'hello' },
    })
    expect(res.statusCode).toBe(200)
    const body = res.json()
    expect(body.success).toBe(true)
    expect(body.data.workflowId).toBe('wf-greeting')
    expect(body.data.steps).toBeInstanceOf(Array)
  })

  it('POST /workflow/execute returns 404 for unmatched', async () => {
    const res = await app.inject({
      method: 'POST',
      url: '/workflow/execute',
      payload: { message: 'xyzqwerty12345' },
    })
    expect(res.statusCode).toBe(404)
  })

  it('POST /workflow/execute returns 400 for empty message', async () => {
    const res = await app.inject({
      method: 'POST',
      url: '/workflow/execute',
      payload: {},
    })
    expect(res.statusCode).toBe(400)
  })

  it('GET /workflow/executions returns list', async () => {
    const res = await app.inject({ method: 'GET', url: '/workflow/executions' })
    expect(res.statusCode).toBe(200)
    const body = res.json()
    expect(body.success).toBe(true)
    expect(body.data).toBeInstanceOf(Array)
  })
})
