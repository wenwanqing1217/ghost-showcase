import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import Fastify from 'fastify'
import cors from '@fastify/cors'
import { registerHealthRoutes } from '../src/routes/health'

describe('Health Routes', () => {
  const app = Fastify()
  beforeAll(async () => {
    await app.register(cors, { origin: ['http://localhost:3000'] })
    await app.register(registerHealthRoutes, { prefix: '/health' })
    await app.ready()
  })
  afterAll(async () => {
    await app.close()
  })

  it('GET /health returns service status', async () => {
    const res = await app.inject({ method: 'GET', url: '/health' })
    expect(res.statusCode).toBe(200)
    const body = res.json()
    expect(body.success).toBe(true)
    expect(body.data.service).toBe('mindflow-api')
    expect(body.data.status).toBe('ok')
    expect(body.data.version).toBe('0.1.0')
    expect(body.data.timestamp).toBeGreaterThan(0)
  })

  it('GET /health/detailed returns extended info', async () => {
    const res = await app.inject({ method: 'GET', url: '/health/detailed' })
    expect(res.statusCode).toBe(200)
    const body = res.json()
    expect(body.success).toBe(true)
    expect(body.data.uptime).toBeGreaterThan(0)
    expect(body.data.memory).toBeDefined()
  })
})
