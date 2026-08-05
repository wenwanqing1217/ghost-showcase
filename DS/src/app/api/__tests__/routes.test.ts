/**
 * Tests for DS e-commerce route handlers:
 *   GET  /api/orders       — order listing with pagination/filter/search/status-counts
 *   GET  /api/products     — product listing with pagination/filter/search
 *   POST /api/orders/[id]/fulfill — mark order as fulfilled
 *   POST /api/sync         — trigger data sync from OneBound
 *
 * Mock strategy:
 *   - @prisma/client → mockImplementation(class) with per-model vi.fn() refs
 *   - @/lib/prisma singleton → delete globalThis.prisma + assign fresh mock instance
 *   - @/lib/metrics → stub to avoid prom-client registration errors
 *   - @/app/api/metrics/route → identity withMetrics (no-op in tests)
 *   - @/lib/auth/verifyRequest → vi.spyOn after dynamic import, mockReturnValue per test
 *   - @/lib/onebound/OneBoundClient → vi.spyOn prototype methods (listAllProducts,
 *     listAllOrders, createFulfillmentOrder) after dynamic import
 *   - Real: getTenantId, tenantWhere, tenantCreateData (pure functions)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { NextRequest } from 'next/server';

// ══════════════════════════════════════════════════════════════════════
// vi.fn() references (module-top, hoisted, shared across tests)
// ══════════════════════════════════════════════════════════════════════

// ── Prisma ──

const mockOrderFindMany = vi.fn();
const mockOrderCount = vi.fn();
const mockOrderGroupBy = vi.fn();
const mockOrderFindFirst = vi.fn();
const mockOrderUpdate = vi.fn();
const mockOrderUpsert = vi.fn();
const mockProductFindMany = vi.fn();
const mockProductCount = vi.fn();
const mockProductUpsert = vi.fn();
const mockShopFindFirst = vi.fn();
const mockSyncLogCreate = vi.fn();
const mockSyncLogUpdate = vi.fn();

const MockPrismaClient = vi.fn().mockImplementation(
  class MockedPrismaClient {
    order = {
      findMany: mockOrderFindMany,
      count: mockOrderCount,
      groupBy: mockOrderGroupBy,
      findFirst: mockOrderFindFirst,
      update: mockOrderUpdate,
      upsert: mockOrderUpsert,
    };
    product = {
      findMany: mockProductFindMany,
      count: mockProductCount,
      upsert: mockProductUpsert,
    };
    shop = {
      findFirst: mockShopFindFirst,
    };
    syncLog = {
      create: mockSyncLogCreate,
      update: mockSyncLogUpdate,
    };
  }
);

// ══════════════════════════════════════════════════════════════════════
// @/lib/onebound — spy on real prototype methods instead of mocking
// the class itself. This avoids vitest v4 `new` interception issues.
// ══════════════════════════════════════════════════════════════════════

let spyListAllProducts: ReturnType<typeof vi.fn>;
let spyListAllOrders: ReturnType<typeof vi.fn>;
let spyCreateFulfillment: ReturnType<typeof vi.fn>;

async function setupOneBoundSpies() {
  const { OneBoundClient, OneBoundError } = await import('@/lib/onebound');
  spyListAllProducts = vi.spyOn(OneBoundClient.prototype, 'listAllProducts').mockResolvedValue([]);
  spyListAllOrders = vi.spyOn(OneBoundClient.prototype, 'listAllOrders').mockResolvedValue([]);
  spyCreateFulfillment = vi.spyOn(OneBoundClient.prototype, 'createFulfillmentOrder').mockResolvedValue({});
}

// ══════════════════════════════════════════════════════════════════════
// Register vi.mock() (hoisted before imports, executed at module init)
// ══════════════════════════════════════════════════════════════════════

// ── Register mocks (hoisted before imports) ──

vi.mock('@prisma/client', () => ({ PrismaClient: MockPrismaClient }));

// Stub metrics to avoid prom-client registration errors in tests
vi.mock('@/lib/metrics', () => ({
  httpRequestsTotal: { labels: vi.fn().mockReturnValue({ inc: vi.fn() }) },
  httpRequestDurationSeconds: { labels: vi.fn().mockReturnValue({ observe: vi.fn() }) },
  registry: { metrics: vi.fn().mockResolvedValue(''), contentType: 'text/plain' },
  ordersTotal: { labels: vi.fn().mockReturnValue({ inc: vi.fn() }) },
  productsTotal: { labels: vi.fn().mockReturnValue({ inc: vi.fn() }) },
  syncOperationsTotal: { labels: vi.fn().mockReturnValue({ inc: vi.fn() }) },
  activeTenants: { set: vi.fn() },
}));

// withMetrics is identity — don't wrap handler with real metrics logic
vi.mock('@/app/api/metrics/route', () => ({
  withMetrics: (handler: any) => handler,
}));

// ══════════════════════════════════════════════════════════════════════
// Lifecycle helpers
// ══════════════════════════════════════════════════════════════════════

/**
 * Clear @/lib/prisma singleton and reinitialize.
 * Strategy: clear globalThis.prisma and set a fresh mocked instance.
 * We intentionally do NOT call vi.resetModules() here because it
 * clears the module cache and can invalidate mock interceptors
 * registered by vi.mock() for other modules (e.g. @/lib/metrics).
 */
async function reinitPrisma() {
  delete (globalThis as unknown as Record<string, unknown>).prisma;
  // Set a fresh mocked PrismaClient directly on globalThis
  (globalThis as unknown as Record<string, unknown>).prisma = new MockPrismaClient();
}

// Spy on real @/lib/auth module — vi.mock factory doesn't reliably
// intercept named exports in vitest v4, so we spy after import.
let mockVerifyRequest: ReturnType<typeof vi.fn>;
async function setupAuthMock() {
  const authMod = await import('@/lib/auth');
  mockVerifyRequest = vi.spyOn(authMod, 'verifyRequest').mockReturnValue({ ok: true });
}

/**
 * Clear all mock call history between tests.
 * Uses direct mock references (no dynamic import needed).
 */
function clearMocks() {
  vi.clearAllMocks();
  if (mockVerifyRequest) mockVerifyRequest.mockReturnValue({ ok: true });
}

// ══════════════════════════════════════════════════════════════════════
// Handler references (populated by dynamic import in beforeEach)
// ══════════════════════════════════════════════════════════════════════

let getOrders: (req: NextRequest) => Promise<ReturnType<typeof NextResponse>>;
let getProducts: (req: NextRequest) => Promise<ReturnType<typeof NextResponse>>;
let fulfillOrder: (req: NextRequest, params: { id: string }) => Promise<ReturnType<typeof NextResponse>>;
let syncData: (req: NextRequest) => Promise<ReturnType<typeof NextResponse>>;

// ══════════════════════════════════════════════════════════════════════
// beforeEach — fresh mocks + reinit prisma + import handlers
// ══════════════════════════════════════════════════════════════════════

beforeEach(async () => {
  await reinitPrisma();
  await setupOneBoundSpies();
  await setupAuthMock(); // spy before importing routes

  const ordersMod = await import('@/app/api/orders/route');
  const productsMod = await import('@/app/api/products/route');
  const fulfillMod = await import('@/app/api/orders/[id]/fulfill/route');
  const syncMod = await import('@/app/api/sync/route');

  getOrders = ordersMod.GET;
  getProducts = productsMod.GET;
  fulfillOrder = fulfillMod.POST;
  syncData = syncMod.POST;

  clearMocks();
});

// ══════════════════════════════════════════════════════════════════════
// Helpers
// ══════════════════════════════════════════════════════════════════════

function makeRequest(
  url: string,
  init?: { method?: string; headers?: Record<string, string>; body?: string }
): NextRequest {
  return new NextRequest(url, init);
}

function orderFixture(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    id: 'order-1',
    externalId: 'ext-1',
    orderNo: 'ORD-001',
    amount: 99.99,
    currency: 'USD',
    status: 'paid',
    customerName: 'Test Customer',
    customerEmail: 'test@example.com',
    itemCount: 2,
    paidAt: new Date('2024-01-01'),
    fulfilledAt: null,
    createdAt: new Date('2024-01-01'),
    tenantId: 'test',
    ...overrides,
  };
}

function productFixture(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    id: 'prod-1',
    externalId: 'ext-1',
    title: 'Test Product',
    description: 'A test product',
    price: 29.99,
    comparePrice: 39.99,
    currency: 'USD',
    inventory: 100,
    images: ['https://example.com/img.jpg'],
    status: 'active',
    lastSyncedAt: new Date('2024-01-01'),
    ...overrides,
  };
}

function shopFixture(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    id: 'shop-1',
    name: 'Test Shop',
    domain: 'test.myshopify.com',
    platform: 'onebound',
    accessToken: 'key-12345678',
    active: true,
    tenantId: 'test',
    ...overrides,
  };
}

// ══════════════════════════════════════════════════════════════════════
// GET /api/orders
// ══════════════════════════════════════════════════════════════════════

describe('GET /api/orders', () => {
  it('returns orders with default pagination (page=1, limit=20)', async () => {
    mockOrderFindMany.mockResolvedValue([orderFixture(), orderFixture({ id: 'order-2' })]);
    mockOrderCount.mockResolvedValue(2);
    mockOrderGroupBy.mockResolvedValue([]);

    const req = makeRequest('http://localhost/api/orders', {
      headers: { 'x-tenant-id': 'tenant-test' },
    });
    const res = await getOrders(req);
    const data = await res.json();

    expect(res.status).toBe(200);
    expect(data.items).toHaveLength(2);
    expect(data.pagination).toEqual({ page: 1, limit: 20, total: 2, totalPages: 1 });
  });

  it('respects page and limit query params', async () => {
    mockOrderFindMany.mockResolvedValue([orderFixture()]);
    mockOrderCount.mockResolvedValue(10);
    mockOrderGroupBy.mockResolvedValue([]);

    const req = makeRequest('http://localhost/api/orders?page=2&limit=5', {
      headers: { 'x-tenant-id': 'tenant-test' },
    });
    const res = await getOrders(req);
    const data = await res.json();

    expect(res.status).toBe(200);
    expect(data.pagination.page).toBe(2);
    expect(data.pagination.limit).toBe(5);
    expect(data.pagination.total).toBe(10);
    expect(mockOrderFindMany).toHaveBeenCalledWith(
      expect.objectContaining({ skip: 5, take: 5 })
    );
  });

  it('clamps limit to max 100', async () => {
    mockOrderFindMany.mockResolvedValue([]);
    mockOrderCount.mockResolvedValue(0);
    mockOrderGroupBy.mockResolvedValue([]);

    const req = makeRequest('http://localhost/api/orders?limit=200', {
      headers: { 'x-tenant-id': 'tenant-test' },
    });
    const res = await getOrders(req);
    const data = await res.json();

    expect(data.pagination.limit).toBe(100);
    expect(mockOrderFindMany).toHaveBeenCalledWith(
      expect.objectContaining({ take: 100 })
    );
  });

  it('filters by status', async () => {
    mockOrderFindMany.mockResolvedValue([]);
    mockOrderCount.mockResolvedValue(0);
    mockOrderGroupBy.mockResolvedValue([]);

    const req = makeRequest('http://localhost/api/orders?status=paid', {
      headers: { 'x-tenant-id': 'tenant-test' },
    });
    await getOrders(req);

    expect(mockOrderFindMany).toHaveBeenCalledWith(
      expect.objectContaining({
        where: expect.objectContaining({ status: 'paid', tenantId: 'tenant-test' }),
      })
    );
  });

  it('searches by orderNo/customerName/customerEmail', async () => {
    mockOrderFindMany.mockResolvedValue([]);
    mockOrderCount.mockResolvedValue(0);
    mockOrderGroupBy.mockResolvedValue([]);

    const req = makeRequest('http://localhost/api/orders?search=ORD-001', {
      headers: { 'x-tenant-id': 'tenant-test' },
    });
    await getOrders(req);

    expect(mockOrderFindMany).toHaveBeenCalledWith(
      expect.objectContaining({
        where: expect.objectContaining({
          OR: expect.arrayContaining([
            expect.objectContaining({ orderNo: expect.objectContaining({ contains: 'ORD-001', mode: 'insensitive' }) }),
            expect.objectContaining({ customerName: expect.objectContaining({ contains: 'ORD-001', mode: 'insensitive' }) }),
            expect.objectContaining({ customerEmail: expect.objectContaining({ contains: 'ORD-001', mode: 'insensitive' }) }),
          ]),
        }),
      })
    );
  });

  it('returns status counts via groupBy', async () => {
    mockOrderFindMany.mockResolvedValue([]);
    mockOrderCount.mockResolvedValue(0);
    mockOrderGroupBy.mockResolvedValue([
      { status: 'paid', _count: { status: 3 } },
      { status: 'pending', _count: { status: 1 } },
    ]);

    const req = makeRequest('http://localhost/api/orders', {
      headers: { 'x-tenant-id': 'tenant-test' },
    });
    const res = await getOrders(req);
    const data = await res.json();

    expect(data.statusCounts).toEqual({ paid: 3, pending: 1 });
  });

  it('applies tenant isolation from x-tenant-id header', async () => {
    mockOrderFindMany.mockResolvedValue([]);
    mockOrderCount.mockResolvedValue(0);
    mockOrderGroupBy.mockResolvedValue([]);

    const req = makeRequest('http://localhost/api/orders', {
      headers: { 'x-tenant-id': 'my-tenant-42' },
    });
    await getOrders(req);

    expect(mockOrderFindMany).toHaveBeenCalledWith(
      expect.objectContaining({ where: expect.objectContaining({ tenantId: 'my-tenant-42' }) })
    );
  });

  it('defaults tenant to "default" when x-tenant-id header is absent', async () => {
    mockOrderFindMany.mockResolvedValue([]);
    mockOrderCount.mockResolvedValue(0);
    mockOrderGroupBy.mockResolvedValue([]);

    const req = makeRequest('http://localhost/api/orders');
    await getOrders(req);

    expect(mockOrderFindMany).toHaveBeenCalledWith(
      expect.objectContaining({ where: expect.objectContaining({ tenantId: 'default' }) })
    );
  });
});

// ══════════════════════════════════════════════════════════════════════
// GET /api/products
// ══════════════════════════════════════════════════════════════════════

describe('GET /api/products', () => {
  it('returns products with default pagination', async () => {
    mockProductFindMany.mockResolvedValue([productFixture(), productFixture({ id: 'prod-2' })]);
    mockProductCount.mockResolvedValue(2);

    const req = makeRequest('http://localhost/api/products', {
      headers: { 'x-tenant-id': 'tenant-test' },
    });
    const res = await getProducts(req);
    const data = await res.json();

    expect(res.status).toBe(200);
    expect(data.items).toHaveLength(2);
    expect(data.pagination).toEqual({ page: 1, limit: 20, total: 2, totalPages: 1 });
  });

  it('respects page and limit', async () => {
    mockProductFindMany.mockResolvedValue([productFixture()]);
    mockProductCount.mockResolvedValue(50);

    const req = makeRequest('http://localhost/api/products?page=3&limit=10', {
      headers: { 'x-tenant-id': 'tenant-test' },
    });
    const res = await getProducts(req);
    const data = await res.json();

    expect(data.pagination.page).toBe(3);
    expect(data.pagination.limit).toBe(10);
    expect(data.pagination.total).toBe(50);
    expect(mockProductFindMany).toHaveBeenCalledWith(
      expect.objectContaining({ skip: 20, take: 10 })
    );
  });

  it('filters by status', async () => {
    mockProductFindMany.mockResolvedValue([]);
    mockProductCount.mockResolvedValue(0);

    const req = makeRequest('http://localhost/api/products?status=active', {
      headers: { 'x-tenant-id': 'tenant-test' },
    });
    await getProducts(req);

    expect(mockProductFindMany).toHaveBeenCalledWith(
      expect.objectContaining({
        where: expect.objectContaining({ status: 'active', tenantId: 'tenant-test' }),
      })
    );
  });

  it('searches by title/description', async () => {
    mockProductFindMany.mockResolvedValue([]);
    mockProductCount.mockResolvedValue(0);

    const req = makeRequest('http://localhost/api/products?search=Widget', {
      headers: { 'x-tenant-id': 'tenant-test' },
    });
    await getProducts(req);

    expect(mockProductFindMany).toHaveBeenCalledWith(
      expect.objectContaining({
        where: expect.objectContaining({
          OR: expect.arrayContaining([
            expect.objectContaining({ title: expect.objectContaining({ contains: 'Widget', mode: 'insensitive' }) }),
            expect.objectContaining({ description: expect.objectContaining({ contains: 'Widget', mode: 'insensitive' }) }),
          ]),
        }),
      })
    );
  });

  it('orders by lastSyncedAt desc', async () => {
    mockProductFindMany.mockResolvedValue([]);
    mockProductCount.mockResolvedValue(0);

    const req = makeRequest('http://localhost/api/products', {
      headers: { 'x-tenant-id': 'tenant-test' },
    });
    await getProducts(req);

    expect(mockProductFindMany).toHaveBeenCalledWith(
      expect.objectContaining({ orderBy: { lastSyncedAt: 'desc' } })
    );
  });

  it('applies tenant isolation', async () => {
    mockProductFindMany.mockResolvedValue([]);
    mockProductCount.mockResolvedValue(0);

    const req = makeRequest('http://localhost/api/products', {
      headers: { 'x-tenant-id': 'tenant-test' },
    });
    await getProducts(req);

    expect(mockProductFindMany).toHaveBeenCalledWith(
      expect.objectContaining({ where: expect.objectContaining({ tenantId: 'tenant-test' }) })
    );
  });
});

// ══════════════════════════════════════════════════════════════════════
// POST /api/orders/[id]/fulfill
// ══════════════════════════════════════════════════════════════════════

describe('POST /api/orders/[id]/fulfill', () => {
  it('fulfills an order via OneBound and updates local status', async () => {
    const shop = shopFixture({ platform: 'onebound', accessToken: 'key-12345678' });
    const order = orderFixture({
      id: 'order-1',
      status: 'paid',
      shop,
      rawData: JSON.stringify({ items: [{ product_id: 'p1', sku: 'SKU-1', quantity: 1 }] }),
    });

    mockOrderFindFirst.mockResolvedValue(order);
    mockOrderUpdate.mockResolvedValue({
      ...order,
      status: 'fulfilled',
      fulfilledAt: new Date(),
      trackingNumber: 'TRACK-456',
      trackingCompany: 'UPS',
    });

    spyCreateFulfillment.mockResolvedValue({
      trackingNumber: 'TRACK-456',
      trackingCompany: 'UPS',
    });

    const req = makeRequest('http://localhost/api/orders/order-1/fulfill', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-tenant-id': 'tenant-test',
      },
      body: JSON.stringify({ trackingNumber: 'TRACK-456', trackingCompany: 'UPS' }),
    });

    const res = await fulfillOrder(req, { params: { id: 'order-1' } });
    const data = await res.json();

    expect(res.status).toBe(200);
    expect(data.ok).toBe(true);
    expect(data.order.status).toBe('fulfilled');
    expect(spyCreateFulfillment).toHaveBeenCalled();
  });

  it('returns 404 when order not found', async () => {
    mockOrderFindFirst.mockResolvedValue(null);

    const req = makeRequest('http://localhost/api/orders/nonexistent/fulfill', {
      method: 'POST',
      headers: { 'x-tenant-id': 'tenant-test' },
    });

    const res = await fulfillOrder(req, { params: { id: 'nonexistent' } });
    const data = await res.json();

    expect(res.status).toBe(404);
    expect(data.error).toBe('订单不存在');
  });

  it('returns 400 when order already fulfilled', async () => {
    mockOrderFindFirst.mockResolvedValue(
      orderFixture({ id: 'order-1', status: 'fulfilled' })
    );

    const req = makeRequest('http://localhost/api/orders/order-1/fulfill', {
      method: 'POST',
      headers: { 'x-tenant-id': 'tenant-test' },
    });

    const res = await fulfillOrder(req, { params: { id: 'order-1' } });
    const data = await res.json();

    expect(res.status).toBe(400);
    expect(data.error).toBe('订单已发货');
  });

  it('returns 400 when order is refunded/cancelled', async () => {
    mockOrderFindFirst.mockResolvedValue(
      orderFixture({ id: 'order-1', status: 'cancelled' })
    );

    const req = makeRequest('http://localhost/api/orders/order-1/fulfill', {
      method: 'POST',
      headers: { 'x-tenant-id': 'tenant-test' },
    });

    const res = await fulfillOrder(req, { params: { id: 'order-1' } });
    const data = await res.json();

    expect(res.status).toBe(400);
    expect(data.error).toBe('订单已退款/取消，无法发货');
  });

  it('updates local status even if OneBound API fails', async () => {
    const shop = shopFixture({ platform: 'onebound', accessToken: 'key-12345678' });
    const order = orderFixture({
      id: 'order-1',
      status: 'paid',
      shop,
      rawData: JSON.stringify({ items: [{ product_id: 'p1', sku: 'SKU-1', quantity: 1 }] }),
    });

    mockOrderFindFirst.mockResolvedValue(order);
    mockOrderUpdate.mockResolvedValue({
      ...order,
      status: 'fulfilled',
      fulfilledAt: new Date(),
    });

    spyCreateFulfillment.mockRejectedValue(new Error('OneBound down'));

    const req = makeRequest('http://localhost/api/orders/order-1/fulfill', {
      method: 'POST',
      headers: { 'x-tenant-id': 'tenant-test' },
    });

    const res = await fulfillOrder(req, { params: { id: 'order-1' } });
    const data = await res.json();

    expect(res.status).toBe(200);
    expect(data.ok).toBe(true);
    expect(data.order.status).toBe('fulfilled');
  });

  it('skips OneBound when order has no rawData items', async () => {
    const shop = shopFixture({ platform: 'onebound', accessToken: 'key-123' });
    const order = orderFixture({
      id: 'order-1',
      status: 'paid',
      shop,
      rawData: null,
    });

    mockOrderFindFirst.mockResolvedValue(order);
    mockOrderUpdate.mockResolvedValue({
      ...order,
      status: 'fulfilled',
      fulfilledAt: new Date(),
    });

    const req = makeRequest('http://localhost/api/orders/order-1/fulfill', {
      method: 'POST',
      headers: { 'x-tenant-id': 'tenant-test' },
    });

    const res = await fulfillOrder(req, { params: { id: 'order-1' } });
    const data = await res.json();

    expect(res.status).toBe(200);
    expect(data.ok).toBe(true);
    expect(spyCreateFulfillment).not.toHaveBeenCalled();
  });

  it('applies tenant isolation when finding order', async () => {
    mockOrderFindFirst.mockResolvedValue(null);

    const req = makeRequest('http://localhost/api/orders/order-1/fulfill', {
      method: 'POST',
      headers: { 'x-tenant-id': 'tenant-test' },
    });
    await fulfillOrder(req, { params: { id: 'order-1' } });

    expect(mockOrderFindFirst).toHaveBeenCalledWith(
      expect.objectContaining({
        where: expect.objectContaining({
          id: 'order-1',
          tenantId: 'tenant-test',
        }),
      })
    );
  });
});

// ══════════════════════════════════════════════════════════════════════
// POST /api/sync
// ══════════════════════════════════════════════════════════════════════

describe('POST /api/sync', () => {
  it('returns 401 when auth fails', async () => {
    mockVerifyRequest.mockReturnValueOnce({ ok: false, error: 'Missing auth' });

    const req = makeRequest('http://localhost/api/sync', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-tenant-id': 'tenant-test',
      },
      body: JSON.stringify({ entity: 'products' }),
    });

    const res = await syncData(req);
    const data = await res.json();

    expect(res.status).toBe(401);
    expect(data.error).toBe('Missing auth');
  });

  it('returns 404 when no active shop connected', async () => {
    mockShopFindFirst.mockResolvedValue(null);

    const req = makeRequest('http://localhost/api/sync', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-tenant-id': 'tenant-test',
      },
      body: JSON.stringify({ entity: 'products' }),
    });

    const res = await syncData(req);
    const data = await res.json();

    expect(res.status).toBe(404);
    expect(data.error).toBe('未找到货源连接，请先连接 OneBound');
  });

  it('returns 400 for invalid OneBound API key (constructor throws)', async () => {
    mockShopFindFirst.mockResolvedValue(
      shopFixture({ accessToken: 'short' })
    );

    // OneBoundClient constructor — mock doesn't throw, so we test
    // the handler's fallback path by letting it create the client normally

    const req = makeRequest('http://localhost/api/sync', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-tenant-id': 'tenant-test',
      },
      body: JSON.stringify({ entity: 'products' }),
    });

    const res = await syncData(req);
    const data = await res.json();

    expect(res.status).toBe(400);
    expect(data.error).toContain('API Key 无效');
  });

  it('syncs products and returns count', async () => {
    const shop = shopFixture({ accessToken: 'valid-key-12345678' });
    mockShopFindFirst.mockResolvedValue(shop);

    spyListAllProducts.mockResolvedValue([
      { id: 'p1', title: 'Product A', price: 10, status: 'active', images: [], variants: [] },
    ]);

    mockProductFindMany.mockResolvedValue([]);
    mockProductCount.mockResolvedValue(0);
    mockProductUpsert.mockResolvedValue({});
    mockSyncLogCreate.mockResolvedValue({ id: 'log-1' });
    mockSyncLogUpdate.mockResolvedValue({});

    const req = makeRequest('http://localhost/api/sync', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-tenant-id': 'tenant-test',
      },
      body: JSON.stringify({ entity: 'products' }),
    });

    const res = await syncData(req);
    const data = await res.json();

    expect(res.status).toBe(200);
    expect(data.ok).toBe(true);
    expect(data.results.products.count).toBe(1);
    expect(spyListAllProducts).toHaveBeenCalled();
  });

  it('syncs orders and returns count', async () => {
    const shop = shopFixture({ accessToken: 'valid-key-12345678' });
    mockShopFindFirst.mockResolvedValue(shop);

    spyListAllOrders.mockResolvedValue([
      { id: 'o1', order_number: 'ORD-001', total: 50, status: 'paid', shipping_address: { name: 'C' }, items: [{ quantity: 2 }] },
    ]);

    mockOrderFindMany.mockResolvedValue([]);
    mockOrderCount.mockResolvedValue(0);
    mockOrderUpsert.mockResolvedValue({});
    mockSyncLogCreate.mockResolvedValue({ id: 'log-1' });
    mockSyncLogUpdate.mockResolvedValue({});

    const req = makeRequest('http://localhost/api/sync', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-tenant-id': 'tenant-test',
      },
      body: JSON.stringify({ entity: 'orders' }),
    });

    const res = await syncData(req);
    const data = await res.json();

    expect(res.status).toBe(200);
    expect(data.ok).toBe(true);
    expect(data.results.orders.count).toBe(1);
    expect(spyListAllOrders).toHaveBeenCalled();
  });

  it('syncs both products and orders when entity is "all"', async () => {
    const shop = shopFixture({ accessToken: 'valid-key-12345678' });
    mockShopFindFirst.mockResolvedValue(shop);

    spyListAllProducts.mockResolvedValue([
      { id: 'p1', title: 'P', price: 10, status: 'active', images: [], variants: [] },
    ]);
    spyListAllOrders.mockResolvedValue([
      { id: 'o1', order_number: 'ORD-1', total: 50, status: 'paid', shipping_address: { name: 'C' }, items: [{ quantity: 1 }] },
    ]);

    mockProductFindMany.mockResolvedValue([]);
    mockProductCount.mockResolvedValue(0);
    mockOrderFindMany.mockResolvedValue([]);
    mockOrderCount.mockResolvedValue(0);
    mockOrderUpsert.mockResolvedValue({});
    mockSyncLogCreate.mockResolvedValue({ id: 'log-1' });
    mockSyncLogUpdate.mockResolvedValue({});

    const req = makeRequest('http://localhost/api/sync', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-tenant-id': 'tenant-test',
      },
      body: JSON.stringify({ entity: 'all' }),
    });

    const res = await syncData(req);
    const data = await res.json();

    expect(res.status).toBe(200);
    expect(data.ok).toBe(true);
    expect(data.results.products.count).toBe(1);
    expect(data.results.orders.count).toBe(1);
  });

  it('records failure when OneBound API throws during sync', async () => {
    const shop = shopFixture({ accessToken: 'valid-key-12345678' });
    mockShopFindFirst.mockResolvedValue(shop);

    spyListAllProducts.mockRejectedValue(new Error('Rate limited by OneBound'));

    mockSyncLogCreate.mockResolvedValue({ id: 'log-1' });
    mockSyncLogUpdate.mockResolvedValue({});

    const req = makeRequest('http://localhost/api/sync', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-tenant-id': 'tenant-test',
      },
      body: JSON.stringify({ entity: 'products' }),
    });

    const res = await syncData(req);
    const data = await res.json();

    expect(res.status).toBe(200);
    expect(data.ok).toBe(false);
    expect(data.results.products.error).toContain('Rate limited');
  });

  it('defaults entity to "all" when not provided', async () => {
    const shop = shopFixture({ accessToken: 'valid-key-12345678' });
    mockShopFindFirst.mockResolvedValue(shop);

    spyListAllProducts.mockResolvedValue([]);
    spyListAllOrders.mockResolvedValue([]);

    mockProductFindMany.mockResolvedValue([]);
    mockProductCount.mockResolvedValue(0);
    mockOrderFindMany.mockResolvedValue([]);
    mockOrderCount.mockResolvedValue(0);
    mockOrderUpsert.mockResolvedValue({});
    mockSyncLogCreate.mockResolvedValue({ id: 'log-1' });
    mockSyncLogUpdate.mockResolvedValue({});

    const req = makeRequest('http://localhost/api/sync', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-tenant-id': 'tenant-test',
      },
      body: JSON.stringify({}), // no entity field — Zod default kicks in
    });

    const res = await syncData(req);

    // Zod default makes entity = 'all', so both sync paths run
    expect(spyListAllProducts).toHaveBeenCalled();
    expect(spyListAllOrders).toHaveBeenCalled();
  });

  it('finds shop by requested shopId with tenant isolation', async () => {
    mockShopFindFirst.mockResolvedValue(
      shopFixture({ id: 'shop-2', name: 'Shop 2' })
    );

    mockProductFindMany.mockResolvedValue([]);
    mockProductCount.mockResolvedValue(0);
    mockProductUpsert.mockResolvedValue({});
    mockSyncLogCreate.mockResolvedValue({ id: 'log-1' });
    mockSyncLogUpdate.mockResolvedValue({});

    const req = makeRequest('http://localhost/api/sync', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-tenant-id': 'tenant-test',
      },
      body: JSON.stringify({ entity: 'products', shopId: 'shop-2' }),
    });

    await syncData(req);

    expect(mockShopFindFirst).toHaveBeenCalledWith(
      expect.objectContaining({
        where: expect.objectContaining({
          id: 'shop-2',
          tenantId: 'tenant-test',
        }),
      })
    );
  });
});
