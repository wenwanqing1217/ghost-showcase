/**
 * Shoplazza API 客户端
 * - 鉴权：access-token 请求头
 * - 限流：令牌桶 10 req/s
 * - 重试：指数退避 1s → 2s → 4s，最多 3 次
 * - API 版本：2026-07
 */

import { z } from 'zod';

// ── 配置常量 ──
const API_VERSION = '2026-07';
const MAX_RETRIES = 3;
const RETRY_BASE_DELAY_MS = 1000;
const RATE_LIMIT_PER_SECOND = 10;

// ── 域名校验（类 Shopify 的 .myshopify.com 格式） ──
const SHOPLAZZA_DOMAIN_RE = /^[a-z0-9-]+\.myshoplaza\.com$/;

// ── Zod Schema（运行时校验 API 返回） ──
// Shoplazza 实际返回格式：{ code: "Success", data: { ... } }

const ShopInfoSchema = z.object({
  id: z.union([z.string(), z.number()]).optional(),
  name: z.string().optional(),
  domain: z.string().optional(),
  email: z.string().optional(),
  currency: z.string().optional(),
  timezone: z.string().optional(),
  phone: z.string().optional(),
  address1: z.string().optional(),
  city: z.string().optional(),
  country_code: z.string().optional(),
  state: z.string().optional(),
});

const ProductSchema = z.object({
  id: z.string(),
  title: z.string(),
  description: z.string().optional(),
  brief: z.string().optional(),
  handle: z.string().optional(),
  published: z.boolean().optional(),
  tags: z.array(z.string()).optional(),
  images: z.array(z.object({
    id: z.string().optional(),
    src: z.string(),
    width: z.number().optional(),
    height: z.number().optional(),
  })).optional(),
  variants: z.array(z.object({
    id: z.string(),
    price: z.union([z.string(), z.number()]).optional(),
    weight: z.number().optional(),
    weight_unit: z.string().optional(),
    whole_prices: z.array(z.object({
      price: z.union([z.string(), z.number()]),
      min_quantity: z.number(),
    })).optional(),
  })).optional(),
  price_min: z.union([z.string(), z.number()]).optional(),
  price_max: z.union([z.string(), z.number()]).optional(),
  origin_price_min: z.union([z.string(), z.number()]).optional(),
  origin_price_max: z.union([z.string(), z.number()]).optional(),
  created_at: z.string().optional(),
  updated_at: z.string().optional(),
  published_at: z.string().optional(),
});

const ProductListSchema = z.object({
  products: z.array(ProductSchema),
  cursor: z.string().optional(),
  pre_cursor: z.string().optional(),
});

const OrderSchema = z.object({
  id: z.string(),
  order_number: z.string().optional(),
  name: z.string().optional(),
  total_price: z.union([z.string(), z.number()]).optional(),
  financial_status: z.string().optional(),
  fulfillment_status: z.string().optional(),
  customer: z.object({
    name: z.string().optional(),
    email: z.string().optional(),
  }).optional(),
  line_items: z.array(z.object({
    quantity: z.number(),
    title: z.string().optional(),
    price: z.union([z.string(), z.number()]).optional(),
  })).optional(),
  created_at: z.string().optional(),
  updated_at: z.string().optional(),
});

const OrderListSchema = z.object({
  orders: z.array(OrderSchema).default([]),
  cursor: z.string().optional(),
  pre_cursor: z.string().optional(),
});

// ── 类型导出 ──
export type ShopInfo = z.infer<typeof ShopInfoSchema>;
export type ShoplazzaProduct = z.infer<typeof ProductSchema>;
export type ShoplazzaOrder = z.infer<typeof OrderSchema>;

// ── 自定义错误 ──
export class ShoplazzaError extends Error {
  constructor(
    message: string,
    public status?: number,
    public responseBody?: unknown
  ) {
    super(message);
    this.name = 'ShoplazzaError';
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
    // 等待下一个令牌
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
export class ShoplazzaClient {
  private baseUrl: string;
  private accessToken: string;
  private rateLimiter: TokenBucket;

  constructor(domain: string, accessToken: string) {
    // 安全: 严格校验域名格式，防止 SSRF
    // 只允许 xxx.myshoplaza.com 格式（小写字母、数字、连字符 + .myshoplaza.com）
    if (!SHOPLAZZA_DOMAIN_RE.test(domain)) {
      throw new ShoplazzaError(
        `无效的 Shoplazza 域名: ${domain}。格式应为 xxx.myshoplaza.com`
      );
    }
    this.baseUrl = `https://${domain}/openapi/${API_VERSION}`;
    this.accessToken = accessToken;
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
        // 限流等待
        await this.rateLimiter.acquire();

        const url = `${this.baseUrl}${path}`;
        const headers: Record<string, string> = {
          'access-token': this.accessToken,
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
          throw new ShoplazzaError(
            `Shoplazza API ${response.status}: ${path}`,
            response.status,
            text
          );
        }

        const envelope = await response.json();

        // Shoplazza 返回 { code, data } 包装
        const payload = envelope.data !== undefined ? envelope.data : envelope;

        // 有 schema 则校验
        if (schema) {
          return schema.parse(payload);
        }
        return payload as T;
      } catch (err) {
        lastError = err as Error;

        // 不重试客户端错误（4xx，除了 429 限流）
        if (err instanceof ShoplazzaError && err.status) {
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

    throw lastError ?? new ShoplazzaError('未知错误');
  }

  // ── 店铺 ──

  /** 获取店铺信息（用于验证 token 有效性） */
  async getShopInfo(): Promise<ShopInfo> {
    return this.request('GET', '/shop', undefined, ShopInfoSchema);
  }

  // ── 商品 ──

  /** 拉取商品列表（cursor 分页） */
  async listProducts(cursor?: string, limit: number = 50): Promise<{ products: ShoplazzaProduct[]; nextCursor?: string }> {
    const qs = new URLSearchParams({ limit: String(limit) });
    if (cursor) qs.set('cursor', cursor);

    const data = await this.request(
      'GET',
      `/products?${qs.toString()}`,
      undefined,
      ProductListSchema
    );
    return { products: data.products, nextCursor: data.cursor };
  }

  /** 拉取所有商品（自动翻页） */
  async listAllProducts(): Promise<ShoplazzaProduct[]> {
    const all: ShoplazzaProduct[] = [];
    let cursor: string | undefined;
    const limit = 50;

    while (true) {
      const { products, nextCursor } = await this.listProducts(cursor, limit);
      all.push(...products);
      if (!nextCursor || products.length < limit) break;
      cursor = nextCursor;
      // 安全阀：最多翻 20 页（1000 商品）
      if (all.length >= 1000) break;
    }
    return all;
  }

  /** 创建商品 */
  async createProduct(input: {
    title: string;
    description?: string;
    price?: number;
    images?: string[];
  }): Promise<ShoplazzaProduct> {
    return this.request('POST', '/products', {
      product: {
        title: input.title,
        body_html: input.description,
        variants: input.price ? [{ price: String(input.price) }] : undefined,
        images: input.images?.map((src) => ({ src })),
      },
    }, ProductSchema);
  }

  // ── 订单 ──

  /** 拉取订单列表（cursor 分页） */
  async listOrders(params: { cursor?: string; limit?: number; status?: string } = {}): Promise<{ orders: ShoplazzaOrder[]; nextCursor?: string }> {
    const qs = new URLSearchParams();
    if (params.limit) qs.set('limit', String(params.limit));
    if (params.cursor) qs.set('cursor', params.cursor);
    if (params.status) qs.set('status', params.status);

    const path = `/orders${qs.toString() ? '?' + qs.toString() : ''}`;
    const data = await this.request('GET', path, undefined, OrderListSchema);
    return { orders: data.orders ?? [], nextCursor: data.cursor };
  }

  /** 拉取所有订单（自动翻页） */
  async listAllOrders(): Promise<ShoplazzaOrder[]> {
    const all: ShoplazzaOrder[] = [];
    let cursor: string | undefined;
    const limit = 50;

    while (true) {
      const { orders, nextCursor } = await this.listOrders({ cursor, limit });
      all.push(...orders);
      if (!nextCursor || orders.length < limit) break;
      cursor = nextCursor;
      if (all.length >= 1000) break;
    }
    return all;
  }

  // ── 履约 ──

  /** 标记发货 */
  async fulfillOrder(orderId: string, trackingNumber?: string, trackingCompany?: string): Promise<unknown> {
    return this.request('POST', `/orders/${orderId}/fulfillments`, {
      fulfillment: {
        tracking_number: trackingNumber,
        tracking_company: trackingCompany,
        notify_customer: true,
      },
    });
  }
}

// ── 便捷工厂（从环境变量创建客户端） ──
export function createShoplazzaClient(): ShoplazzaClient | null {
  const domain = process.env.SHOPLAZZA_SHOP_DOMAIN;
  const token = process.env.SHOPLAZZA_ACCESS_TOKEN;

  if (!domain || !token) return null;

  return new ShoplazzaClient(domain, token);
}
