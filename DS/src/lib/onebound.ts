/**
 * OneBound Dropshipping API 客户端
 *
 * OneBound 是供应链/代发平台，提供：
 *   - 商品目录搜索与同步（从 OneBound 拉取货源）
 *   - 订单代发（将订单提交给 OneBound 履约）
 *   - 物流追踪（查询代发订单的物流状态）
 *
 * 认证方式：API Key（请求头 X-API-Key）
 * 限流：令牌桶 5 req/s（OneBound 通常比 Shoplazta 更严格）
 * 重试：指数退避 1s → 2s → 4s，最多 3 次
 *
 * 环境变量：
 *   ONEBOUND_API_KEY    — 必填，OneBound 控制台获取
 *   ONEBOUND_BASE_URL   — 可选，默认 https://api.onebound.com
 */

import { z } from 'zod';

// ── 配置常量 ──

const MAX_RETRIES = 3;
const RETRY_BASE_DELAY_MS = 1000;
const RATE_LIMIT_PER_SECOND = 5;

// ── Zod Schema（运行时校验 API 返回） ──

/** OneBound 商品 */
const OneBoundProductSchema = z.object({
  id: z.union([z.string(), z.number()]),
  title: z.string(),
  description: z.string().optional(),
  brief: z.string().optional(),
  sku: z.string().optional(),
  category: z.string().optional(),
  tags: z.array(z.string()).optional(),
  images: z.array(z.object({
    url: z.string(),
    alt: z.string().optional(),
  })).optional(),
  variants: z.array(z.object({
    id: z.union([z.string(), z.number()]),
    sku: z.string().optional(),
    title: z.string().optional(),
    price: z.union([z.string(), z.number()]),
    compare_price: z.union([z.string(), z.number()]).optional(),
    inventory: z.number().optional(),
    weight: z.number().optional(),
    weight_unit: z.string().optional(),
  })).optional(),
  price: z.union([z.string(), z.number()]).optional(),
  compare_price: z.union([z.string(), z.number()]).optional(),
  inventory: z.number().optional(),
  supplier: z.string().optional(),
  shipping_days: z.number().optional(),
  status: z.string().optional(),
});

const ProductListSchema = z.object({
  products: z.array(OneBoundProductSchema),
  total: z.number().optional(),
  page: z.number().optional(),
  page_size: z.number().optional(),
  has_more: z.boolean().optional(),
});

/** OneBound 订单（代发订单） */
const OneBoundOrderSchema = z.object({
  id: z.union([z.string(), z.number()]),
  order_number: z.string().optional(),
  status: z.string().optional(),
  total: z.union([z.string(), z.number()]).optional(),
  currency: z.string().optional(),
  tracking_number: z.string().optional(),
  tracking_company: z.string().optional(),
  items: z.array(z.object({
    product_id: z.union([z.string(), z.number()]).optional(),
    sku: z.string().optional(),
    title: z.string().optional(),
    quantity: z.number(),
    price: z.union([z.string(), z.number()]).optional(),
  })).optional(),
  shipping_address: z.object({
    name: z.string().optional(),
    phone: z.string().optional(),
    address: z.string().optional(),
    city: z.string().optional(),
    state: z.string().optional(),
    country: z.string().optional(),
    zip: z.string().optional(),
  }).optional(),
  created_at: z.string().optional(),
  updated_at: z.string().optional(),
});

const OrderListSchema = z.object({
  orders: z.array(OneBoundOrderSchema).default([]),
  total: z.number().optional(),
  has_more: z.boolean().optional(),
});

/** 订单创建响应 */
const CreateOrderResponseSchema = z.object({
  id: z.union([z.string(), z.number()]),
  order_number: z.string().optional(),
  status: z.string().optional(),
  tracking_number: z.string().optional(),
  tracking_company: z.string().optional(),
});

// ── 类型导出 ──

export type OneBoundProduct = z.infer<typeof OneBoundProductSchema>;
export type OneBoundOrder = z.infer<typeof OneBoundOrderSchema>;

// ── 自定义错误 ──

export class OneBoundError extends Error {
  constructor(
    message: string,
    public status?: number,
    public responseBody?: unknown
  ) {
    super(message);
    this.name = 'OneBoundError';
  }
}

// ── 令牌桶限流器 ──

class TokenBucket {
  private tokens: number;
  private lastRefill: number;

  constructor(
    private capacity: number,
    private refillIntervalMs: number = 1000
  ) {
    this.tokens = capacity;
    this.lastRefill = Date.now();
  }

  async acquire(): Promise<void> {
    this.refill();
    if (this.tokens >= 1) {
      this.tokens -= 1;
      return;
    }
    const waitMs = this.refillIntervalMs / this.capacity;
    await sleep(waitMs);
    return this.acquire();
  }

  private refill(): void {
    const now = Date.now();
    const elapsed = now - this.lastRefill;
    if (elapsed >= this.refillIntervalMs) {
      this.tokens = this.capacity;
      this.lastRefill = now;
    }
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// ── 主客户端 ──

export class OneBoundClient {
  private baseUrl: string;
  private apiKey: string;
  private rateLimiter: TokenBucket;

  constructor(apiKey: string, baseUrl?: string) {
    if (!apiKey || apiKey.trim().length < 10) {
      throw new OneBoundError('OneBound API Key 无效，请检查配置');
    }
    this.baseUrl = (baseUrl || process.env.ONEBOUND_BASE_URL || 'https://api.onebound.com').replace(/\/+$/, '');
    this.apiKey = apiKey.trim();
    this.rateLimiter = new TokenBucket(RATE_LIMIT_PER_SECOND);
  }

  /**
   * 带限流和重试的请求核心
   */
  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
    schema?: z.ZodType<T>
  ): Promise<T> {
    let lastError: Error | undefined;

    for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
      try {
        await this.rateLimiter.acquire();

        const url = `${this.baseUrl}${path}`;
        const headers: Record<string, string> = {
          'X-API-Key': this.apiKey,
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        };

        const response = await fetch(url, {
          method,
          headers,
          body: body ? JSON.stringify(body) : undefined,
        });

        if (!response.ok) {
          const text = await response.text();
          throw new OneBoundError(
            `OneBound API ${response.status}: ${path}`,
            response.status,
            text
          );
        }

        const envelope = await response.json();

        // OneBound 返回格式: { success: true, data: { ... } }
        // 也兼容直接返回 data 的情况
        const payload = envelope.data !== undefined ? envelope.data : envelope;

        if (schema) {
          return schema.parse(payload);
        }
        return payload as T;
      } catch (err) {
        lastError = err as Error;

        if (err instanceof OneBoundError && err.status) {
          if (err.status >= 400 && err.status < 500 && err.status !== 429) {
            throw err;
          }
        }

        if (attempt < MAX_RETRIES) {
          const delay = RETRY_BASE_DELAY_MS * Math.pow(2, attempt);
          await sleep(delay);
        }
      }
    }

    throw lastError ?? new OneBoundError('未知错误');
  }

  // ── 商品 ──

  /**
   * 搜索商品（关键词 + 分页）
   */
  async searchProducts(query: string, page: number = 1, pageSize: number = 50): Promise<{
    products: OneBoundProduct[];
    total: number;
    hasMore: boolean;
  }> {
    const qs = new URLSearchParams({
      q: query,
      page: String(page),
      page_size: String(pageSize),
    });

    const data = await this.request(
      'GET',
      `/products/search?${qs.toString()}`,
      undefined,
      ProductListSchema
    );

    return {
      products: data.products,
      total: data.total || 0,
      hasMore: data.has_more || false,
    };
  }

  /**
   * 拉取商品列表（分页自动翻页）
   */
  async listProducts(page: number = 1, pageSize: number = 50): Promise<{
    products: OneBoundProduct[];
    hasMore: boolean;
  }> {
    const qs = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
    });

    const data = await this.request(
      'GET',
      `/products?${qs.toString()}`,
      undefined,
      ProductListSchema
    );

    return {
      products: data.products,
      hasMore: data.has_more || false,
    };
  }

  /**
   * 拉取所有商品（自动翻页）
   */
  async listAllProducts(maxItems: number = 1000): Promise<OneBoundProduct[]> {
    const all: OneBoundProduct[] = [];
    let page = 1;
    const pageSize = 50;

    while (all.length < maxItems) {
      const { products, hasMore } = await this.listProducts(page, pageSize);
      all.push(...products);
      if (!hasMore || products.length < pageSize) break;
      page++;
    }

    return all.slice(0, maxItems);
  }

  /**
   * 获取单个商品详情
   */
  async getProduct(productId: string | number): Promise<OneBoundProduct> {
    return this.request(
      'GET',
      `/products/${productId}`,
      undefined,
      OneBoundProductSchema
    );
  }

  // ── 订单 ──

  /**
   * 提交代发订单（履约）
   */
  async createFulfillmentOrder(input: {
    items: Array<{
      productId: string | number;
      sku?: string;
      quantity: number;
    }>;
    shippingAddress: {
      name: string;
      phone: string;
      address: string;
      city: string;
      state?: string;
      country: string;
      zip?: string;
    };
    orderNote?: string;
  }): Promise<{
    orderId: string;
    orderNumber: string;
    trackingNumber?: string;
    trackingCompany?: string;
    status: string;
  }> {
    const body = {
      items: input.items,
      shipping_address: input.shippingAddress,
      note: input.orderNote,
    };

    const data = await this.request(
      'POST',
      '/orders',
      body,
      CreateOrderResponseSchema
    );

    return {
      orderId: String(data.id),
      orderNumber: data.order_number || String(data.id),
      trackingNumber: data.tracking_number,
      trackingCompany: data.tracking_company,
      status: data.status || 'processing',
    };
  }

  /**
   * 查询订单状态/物流追踪
   */
  async getOrderTracking(orderId: string | number): Promise<{
    orderId: string;
    status: string;
    trackingNumber?: string;
    trackingCompany?: string;
    trackingHistory?: Array<{
      timestamp: string;
      status: string;
      location?: string;
      description: string;
    }>;
  }> {
    const data = await this.request(
      'GET',
      `/orders/${orderId}/tracking`,
      undefined,
      OneBoundOrderSchema
    );

    return {
      orderId: String(data.id),
      status: data.status || 'unknown',
      trackingNumber: data.tracking_number,
      trackingCompany: data.tracking_company,
    };
  }

  /**
   * 拉取代发订单列表
   */
  async listOrders(page: number = 1, pageSize: number = 50): Promise<{
    orders: OneBoundOrder[];
    hasMore: boolean;
  }> {
    const qs = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
    });

    const data = await this.request(
      'GET',
      `/orders?${qs.toString()}`,
      undefined,
      OrderListSchema
    );

    return {
      orders: data.orders,
      hasMore: data.has_more || false,
    };
  }

  /**
   * 拉取所有订单
   */
  async listAllOrders(maxItems: number = 1000): Promise<OneBoundOrder[]> {
    const all: OneBoundOrder[] = [];
    let page = 1;
    const pageSize = 50;

    while (all.length < maxItems) {
      const { orders, hasMore } = await this.listOrders(page, pageSize);
      all.push(...orders);
      if (!hasMore || orders.length < pageSize) break;
      page++;
    }

    return all.slice(0, maxItems);
  }
}

// ── 便捷工厂（从环境变量创建客户端） ──

export function createOneBoundClient(): OneBoundClient | null {
  const apiKey = process.env.ONEBOUND_API_KEY;

  if (!apiKey) return null;

  return new OneBoundClient(apiKey);
}
