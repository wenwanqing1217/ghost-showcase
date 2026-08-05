import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import Fastify from 'fastify'
import cors from '@fastify/cors'
import { registerAidRoutes } from '../src/routes/aid'

describe('AID Routes', () => {
  const app = Fastify()
  beforeAll(async () => {
    await app.register(cors, { origin: ['http://localhost:3000'] })
    await app.register(registerAidRoutes, { prefix: '/aid' })
    await app.ready()
  })
  afterAll(async () => {
    await app.close()
  })

  it('GET /aid/capabilities returns capability list', async () => {
    const res = await app.inject({ method: 'GET', url: '/aid/capabilities' })
    expect(res.statusCode).toBe(200)
    const body = res.json()
    expect(body.success).toBe(true)
    expect(body.data).toBeInstanceOf(Array)
    expect(body.data.length).toBeGreaterThan(0)
    expect(body.data[0].id).toBeDefined()
    expect(body.data[0].name).toBeDefined()
  })

  it('POST /aid/sessions creates a session', async () => {
    const res = await app.inject({
      method: 'POST',
      url: '/aid/sessions',
      payload: {},
    })
    expect(res.statusCode).toBe(201)
    const body = res.json()
    expect(body.success).toBe(true)
    expect(body.data.id).toMatch(/^sess-/)
    expect(body.data.messages).toEqual([])
  })

  it('GET /aid/sessions/:id returns session', async () => {
    const created = await app.inject({
      method: 'POST',
      url: '/aid/sessions',
      payload: {},
    })
    const sessionId = created.json().data.id
    const res = await app.inject({ method: 'GET', url: `/aid/sessions/${sessionId}` })
    expect(res.statusCode).toBe(200)
    const body = res.json()
    expect(body.data.id).toBe(sessionId)
  })

  it('GET /aid/sessions/:id returns 404 for unknown', async () => {
    const res = await app.inject({ method: 'GET', url: '/aid/sessions/nonexistent' })
    expect(res.statusCode).toBe(404)
  })

  it('POST /aid/sessions/:id/messages sends message', async () => {
    const created = await app.inject({
      method: 'POST',
      url: '/aid/sessions',
      payload: {},
    })
    const sessionId = created.json().data.id
    const res = await app.inject({
      method: 'POST',
      url: `/aid/sessions/${sessionId}/messages`,
      payload: { message: 'hello' },
    })
    expect(res.statusCode).toBe(200)
    const body = res.json()
    expect(body.success).toBe(true)
    expect(body.data.user.role).toBe('user')
    expect(body.data.assistant.role).toBe('assistant')
  })

  it('DELETE /aid/sessions/:id deletes session', async () => {
    const created = await app.inject({
      method: 'POST',
      url: '/aid/sessions',
      payload: {},
    })
    const sessionId = created.json().data.id
    const res = await app.inject({
      method: 'DELETE',
      url: `/aid/sessions/${sessionId}`,
    })
    expect(res.statusCode).toBe(200)
    const body = res.json()
    expect(body.data.deleted).toBe(true)
  })
})
