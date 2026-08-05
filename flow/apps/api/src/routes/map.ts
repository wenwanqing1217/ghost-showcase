/**
 * Map routes — 地图 POI 搜索与路线管理
 *
 * 提供地点搜索、路线保存与查询能力。
 * 实际地理编码/路线规划可对接百度/高德 API。
 */
import { FastifyInstance } from 'fastify'
import type { LocationPoint, MapRoute } from '@mindflow/shared'

// ── 内存存储 ──
const routes = new Map<string, MapRoute>()

/** 类型收窄：metadata 为 Record<string, unknown>，city 可能缺失 */
function cityOf(p: LocationPoint): string {
  const city = p.metadata?.city
  return typeof city === 'string' ? city : ''
}

// 示例 POI 数据
const samplePOIs: LocationPoint[] = [
  { lat: 39.9042, lng: 116.4074, label: '北京天安门', metadata: { city: '北京' } },
  { lat: 39.9163, lng: 116.3972, label: '北京故宫', metadata: { city: '北京' } },
  { lat: 31.2304, lng: 121.4737, label: '上海外滩', metadata: { city: '上海' } },
  { lat: 22.5431, lng: 114.0579, label: '深圳福田', metadata: { city: '深圳' } },
  { lat: 30.5728, lng: 104.0668, label: '成都天府广场', metadata: { city: '成都' } },
]

export async function registerMapRoutes(app: FastifyInstance) {
  // POI 搜索
  app.get<{ Querystring: { q?: string; city?: string } }>(
    '/search',
    async (request) => {
      const { q, city } = request.query
      let results = samplePOIs

      if (q) {
        results = results.filter(
          (p) =>
            p.label?.toLowerCase().includes(q.toLowerCase()) ||
            cityOf(p).toLowerCase().includes(q.toLowerCase())
        )
      }
      if (city) {
        results = results.filter((p) => cityOf(p).toLowerCase() === city.toLowerCase())
      }

      return { success: true, data: results }
    }
  )

  // 获取所有 POI
  app.get('/pois', async () => {
    return { success: true, data: samplePOIs }
  })

  // 保存路线
  app.post<{ Body: { name: string; points: LocationPoint[] } }>(
    '/routes',
    async (request, reply) => {
      const { name, points } = request.body || {}
      if (!name || !points || points.length < 2) {
        return reply.status(400).send({
          success: false,
          error: 'name 和至少 2 个 points 为必填',
        })
      }

      const route: MapRoute = {
        id: `route-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        name,
        points,
        createdAt: Date.now(),
      }
      routes.set(route.id, route)
      return reply.status(201).send({ success: true, data: route })
    }
  )

  // 列出所有路线
  app.get('/routes', async () => {
    return { success: true, data: Array.from(routes.values()) }
  })

  // 获取单条路线
  app.get<{ Params: { id: string } }>(
    '/routes/:id',
    async (request, reply) => {
      const route = routes.get(request.params.id)
      if (!route) {
        return reply
          .status(404)
          .send({ success: false, error: '路线不存在' })
      }
      return { success: true, data: route }
    }
  )

  // 删除路线
  app.delete<{ Params: { id: string } }>(
    '/routes/:id',
    async (request, reply) => {
      if (!routes.has(request.params.id)) {
        return reply
          .status(404)
          .send({ success: false, error: '路线不存在' })
      }
      routes.delete(request.params.id)
      return { success: true, data: { deleted: true } }
    }
  )
}
