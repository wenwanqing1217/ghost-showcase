import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import Fastify from 'fastify'
import cors from '@fastify/cors'
import { registerComputerUseRoutes } from '../src/routes/computer-use'

describe('Computer Use Routes', () => {
  const app = Fastify()
  beforeAll(async () => {
    await app.register(cors, { origin: ['http://localhost:3000'] })
    await app.register(registerComputerUseRoutes, { prefix: '/computer-use' })
    await app.ready()
  })
  afterAll(async () => {
    await app.close()
  })

  it('GET /computer-use/status returns status', async () => {
    const res = await app.inject({ method: 'GET', url: '/computer-use/status' })
    expect(res.statusCode).toBe(200)
    const body = res.json()
    expect(body.success).toBe(true)
    expect(body.data.engine).toBe('playwright')
  })

  it('POST /computer-use/tasks creates a task', async () => {
    const res = await app.inject({
      method: 'POST',
      url: '/computer-use/tasks',
      payload: { type: 'screenshot', params: { url: 'https://example.com' } },
    })
    expect(res.statusCode).toBe(201)
    const body = res.json()
    expect(body.success).toBe(true)
    expect(body.data.id).toMatch(/^task-/)
    expect(body.data.status).toBe('completed')
  })

  it('POST /computer-use/tasks returns 400 for invalid type', async () => {
    const res = await app.inject({
      method: 'POST',
      url: '/computer-use/tasks',
      payload: { type: 'invalid' },
    })
    expect(res.statusCode).toBe(400)
  })

  it('POST /computer-use/screenshot creates screenshot task', async () => {
    const res = await app.inject({
      method: 'POST',
      url: '/computer-use/screenshot',
      payload: { url: 'https://example.com' },
    })
    expect(res.statusCode).toBe(200)
    const body = res.json()
    expect(body.success).toBe(true)
  })

  it('GET /computer-use/tasks returns task list', async () => {
    const res = await app.inject({ method: 'GET', url: '/computer-use/tasks' })
    expect(res.statusCode).toBe(200)
    const body = res.json()
    expect(body.success).toBe(true)
    expect(body.data).toBeInstanceOf(Array)
  })
})
