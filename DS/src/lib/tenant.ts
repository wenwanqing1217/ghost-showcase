/**
 * DS 租户工具 — 从 Gateway 注入的 X-Tenant-ID header 提取租户标识
 *
 * 数据流：
 *   DS Frontend → Gateway (:18080/v1/ecom/*) → DS API (:3001/api/*)
 *                                     ↑
 *                           Gateway 注入 X-Tenant-ID header
 *
 * 租户隔离策略：
 *   - 所有查询自动附加 tenantId 过滤条件
 *   - 创建/更新时自动设置 tenantId
 *   - Shop 特殊处理：domain 全局唯一，但属于特定 tenant
 *
 * 并发安全：
 *   - 使用 AsyncLocalStorage 维护请求级租户上下文
 *   - 避免模块级可变状态在 serverless/HMR 环境下泄漏
 *
 * Alpha-ID 映射：
 *   - Gateway 从 JWT 提取 alpha_id 作为 tenant_id
 *   - DS 使用 TenantMapping 表持久化 alpha_id → tenant_id 映射
 *   - getOrCreateTenantId() 确保每个 alpha_id 都有对应的 tenant_id
 */

import { AsyncLocalStorage } from 'async_hooks';
import type { NextRequest } from 'next/server';

// ── 请求级租户上下文（AsyncLocalStorage 保证并发安全）──
// Next.js serverless 环境下，模块级变量会在请求间共享。
// AsyncLocalStorage 为每个异步调用链维护独立的 tenant 上下文。

const tenantContext = new AsyncLocalStorage<string>();

/** 在请求开始时设置租户上下文（返回 run 回调） */
export function withTenantContext<R>(tenantId: string, callback: () => R): R {
  return tenantContext.run(tenantId, callback);
}

/** 获取当前请求的租户 ID（无上下文时返回 'default'） */
export function getTenantContext(): string {
  return tenantContext.getStore() || 'default';
}

/** 判断当前请求是否有租户上下文 */
export function hasTenantContext(): boolean {
  return tenantContext.getStore() !== undefined;
}

/** 从请求头提取租户 ID（Gateway 注入的 X-Tenant-ID） */
export function getTenantId(req: NextRequest): string {
  return req.headers.get('x-tenant-id')?.trim() || 'default';
}

/** 生成带租户隔离的 where 条件 */
export function tenantWhere(tenantId: string, extra: Record<string, unknown> = {}): Record<string, unknown> {
  return { ...extra, tenantId };
}

/** 创建时自动注入 tenantId 的数据 */
export function tenantCreateData<T extends Record<string, unknown>>(
  tenantId: string,
  data: T,
): T & { tenantId: string } {
  return { ...data, tenantId } as T & { tenantId: string };
}

// ── Alpha-ID → Tenant-ID 映射（服务端，需 Prisma 客户端）──
// 以下函数仅用于 Next.js API Routes / Server Components（服务端），
// 不可在客户端组件中调用。

import { prisma } from '@/lib/prisma';

/**
 * 根据 alpha_id 解析或创建对应的 tenant_id。
 *
 * 这是 Gateway 认证（JWT → alpha_id）与 DS 数据隔离（tenantId）
 * 之间的桥梁。每个 alpha_id 在首次使用时自动创建 TenantMapping
 * 记录，确保后续查询都能正确按 tenant_id 过滤。
 *
 * 典型用法（API Route）：
 *   const alphaId = req.headers.get('x-alpha-id') || 'default';
 *   const tenantId = await getOrCreateTenantId(alphaId);
 *   const results = await prisma.content.findMany({
 *     where: { tenantId, ...filters },
 *   });
 *
 * @param alphaId - Alpha-ID 用户标识（来自 JWT claim 或 Gateway 注入的 header）
 * @returns 对应的 tenant_id，用于所有 Prisma 查询的 tenantId 过滤
 * @throws Error 如果 alphaId 为空或无效
 */
export async function getOrCreateTenantId(alphaId: string): Promise<string> {
  if (!alphaId || typeof alphaId !== 'string' || alphaId.trim() === '') {
    throw new Error(`Invalid alphaId: "${alphaId}". Must be a non-empty string.`);
  }

  const trimmedAlphaId = alphaId.trim();

  // 查询是否已存在映射
  const existing = await prisma.tenantMapping.findUnique({
    where: { alphaId: trimmedAlphaId },
    select: { tenantId: true },
  });

  if (existing) {
    return existing.tenantId;
  }

  // 首次使用：创建映射，tenantId 使用 alphaId 本身（确保命名空间确定性）
  const created = await prisma.tenantMapping.create({
    data: {
      alphaId: trimmedAlphaId,
      tenantId: trimmedAlphaId,
    },
    select: { tenantId: true },
  });

  return created.tenantId;
}

/**
 * 批量解析多个 alpha_id 的 tenant_id（一次 DB 查询，性能更优）。
 *
 * @param alphaIds - Alpha-ID 列表
 * @returns Map<alphaId, tenantId>，不存在的 alpha_id 不会出现在返回中
 */
export async function batchGetTenantIds(alphaIds: string[]): Promise<Map<string, string>> {
  const trimmed = alphaIds
    .map(id => id?.trim())
    .filter((id): id is string => !!id && id.length > 0);

  if (trimmed.length === 0) {
    return new Map();
  }

  const mappings = await prisma.tenantMapping.findMany({
    where: { alphaId: { in: trimmed } },
    select: { alphaId: true, tenantId: true },
  });

  return new Map(mappings.map(m => [m.alphaId, m.tenantId]));
}
