import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import Fastify from 'fastify'
import cors from '@fastify/cors'
import { registerMapRoutes } from '../src/routes/map'

describe('Map Routes', () => {
  const app = Fastify()
  beforeAll(async () => {
    await app.register(cors, { origin: ['http://localhost:3000'] })
    await app.register(registerMapRoutes, { prefix: '/map' })
    await app.ready()
  })
  afterAll(async () => {
    await app.close()
  })

  it('GET /map/pois returns all POIs', async () => {
    const res = await app.inject({ method: 'GET', url: '/map/pois' })
    expect(res.statusCode).toBe(200)
    const body = res.json()
    expect(body.success).toBe(true)
    expect(body.data).toBeInstanceOf(Array)
    expect(body.data.length).toBeGreaterThan(0)
  })

  it('GET /map/search?q= filters POIs', async () => {
    const res = await app.inject({ method: 'GET', url: '/map/search?q=北京' })
    expect(res.statusCode).toBe(200)
    const body = res.json()
    expect(body.success).toBe(true)
    expect(body.data.every((p: { metadata?: { city?: string } }) => p.metadata?.city === '北京')).toBe(true)
  })

  it('POST /map/routes creates a route', async () => {
    const res = await app.inject({
      method: 'POST',
      url: '/map/routes',
      payload: {
        name: 'Test Route',
        points: [
          { lat: 39.9, lng: 116.4 },
          { lat: 31.2, lng: 121.5 },
        ],
      },
    })
    expect(res.statusCode).toBe(201)
    const body = res.json()
    expect(body.success).toBe(true)
    expect(body.data.id).toMatch(/^route-/)
    expect(body.data.name).toBe('Test Route')
  })

  it('POST /map/routes returns 400 for invalid input', async () => {
    const res = await app.inject({
      method: 'POST',
      url: '/map/routes',
      payload: { name: 'Test' },
    })
    expect(res.statusCode).toBe(400)
  })

  it('GET /map/routes returns route list', async () => {
    const res = await app.inject({ method: 'GET', url: '/map/routes' })
    expect(res.statusCode).toBe(200)
    const body = res.json()
    expect(body.success).toBe(true)
    expect(body.data).toBeInstanceOf(Array)
  })
})
