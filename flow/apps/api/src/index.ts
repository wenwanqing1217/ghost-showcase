/**
 * MindFlow API — Fastify backend for Ghost frontend portal
 *
 * 前端门户后端服务，提供：
 *   - /health          健康检查
 *   - /workflow/*      工作流管理与执行
 *   - /aid/*           AI 助手对话（流式）
 *   - /map/*           地图 POI 与路线
 *   - /computer-use/*  浏览器自动化
 *
 * 设计原则：
 *   - 无状态，可水平扩展
 *   - 统一 JSON 响应 { success, data, error }
 *   - CORS 允许 localhost:3000/3001/18080
 */

import Fastify from 'fastify'
import cors from '@fastify/cors'
import { registerHealthRoutes } from './routes/health'
import { registerWorkflowRoutes } from './routes/workflow'
import { registerAidRoutes } from './routes/aid'
import { registerMapRoutes } from './routes/map'
import { registerComputerUseRoutes } from './routes/computer-use'

// ── 配置 ──
const PORT = parseInt(process.env.PORT || '3036', 10)
const HOST = process.env.HOST || '127.0.0.1'
const GATEWAY_URL = process.env.GATEWAY_URL || 'http://localhost:18080'
const API_KEY = process.env.API_KEY || ''

// ── 应用构建 ──
async function build() {
  const app = Fastify({
    logger: {
      level: process.env.LOG_LEVEL || 'info',
    },
  })

  // CORS
  await app.register(cors, {
    origin: [
      'http://localhost:3000',
      'http://localhost:3001',
      'http://localhost:18080',
      'http://localhost:8000',
    ],
    credentials: true,
  })

  // 认证中间件：若设置了 API_KEY，则非健康检查路由需携带 x-api-key 头
  // 未设置 API_KEY 时放行（开发模式），但输出警告
  if (!API_KEY) {
    app.log.warn('API_KEY 未设置 — 所有端点公开访问。生产环境请设置 API_KEY 环境变量。')
  } else {
    app.addHook('onRequest', async (request, reply) => {
      // 健康检查端点免认证
      if (request.url.startsWith('/health')) return
      const provided = request.headers['x-api-key']
      if (!provided || provided !== API_KEY) {
        reply.status(401).send({ success: false, error: '未授权：缺少或无效的 x-api-key' })
      }
    })
  }

  // 统一错误处理
  app.setErrorHandler((error, request, reply) => {
    request.log.error(error)
    reply.status(error.statusCode || 500).send({
      success: false,
      error: error.message || 'Internal Server Error',
    })
  })

  // 404 处理
  app.setNotFoundHandler((request, reply) => {
    reply.status(404).send({
      success: false,
      error: `Route ${request.method} ${request.url} not found`,
    })
  })

  // 注册路由
  await app.register(registerHealthRoutes, { prefix: '/health' })
  await app.register(registerWorkflowRoutes, { prefix: '/workflow' })
  await app.register(registerAidRoutes, { prefix: '/aid' })
  await app.register(registerMapRoutes, { prefix: '/map' })
  await app.register(registerComputerUseRoutes, { prefix: '/computer-use' })

  return app
}

// ── 启动 ──
async function start() {
  const app = await build()
  try {
    await app.listen({ port: PORT, host: HOST })
    app.log.info(`MindFlow API running at http://${HOST}:${PORT}`)
    app.log.info(`Gateway proxy target: ${GATEWAY_URL}`)
  } catch (err) {
    app.log.error(err)
    process.exit(1)
  }
}

start()
