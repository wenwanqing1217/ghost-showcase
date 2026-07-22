import { ShopifyProduct, ShopifyOrder } from '@/types/shopify';
import { withRetry, ExternalServiceError, extractRetryAfter } from '@/lib/errors';
import { logger } from '@/lib/observability/logger';

const SHOPIFY_API_VERSION = '2024-10';
const SHOPIFY_DOMAIN_RE = /^[a-z0-9-]+\.myshopify\.com$/;

function validateShopifyDomain(shopDomain: string): string {
  const trimmed = (shopDomain || '').trim();
  if (!trimmed) {
    throw new Error('Missing SHOPIFY_SHOP_DOMAIN');
  }
  const lower = trimmed.toLowerCase();
  if (!SHOPIFY_DOMAIN_RE.test(lower)) {
    throw new Error(`Invalid SHOPIFY_SHOP_DOMAIN format: ${trimmed}`);
  }
  return lower;
}

function getHeaders() {
  const shopDomain = validateShopifyDomain(process.env.SHOPIFY_SHOP_DOMAIN || '');
  const token = process.env.SHOPIFY_ACCESS_TOKEN;

  if (!token) {
    throw new Error('Missing Shopify credentials: SHOPIFY_SHOP_DOMAIN and SHOPIFY_ACCESS_TOKEN are required');
  }

  return {
    'X-Shopify-Access-Token': token,
    'Content-Type': 'application/json',
  };
}

function shopifyUrl(path: string): string {
  const shopDomain = validateShopifyDomain(process.env.SHOPIFY_SHOP_DOMAIN || '');
  return `https://${shopDomain}/admin/api/${SHOPIFY_API_VERSION}${path}`;
}

// Demo/mock data for explicit demo mode only
const DEMO_PRODUCTS: ShopifyProduct[] = [
  {
    id: '1',
    title: 'Wireless Earbuds Pro',
    bodyHtml: '<p>High-quality wireless earbuds with active noise cancellation and 24-hour battery life.</p>',
    vendor: 'MindFlow Store',
    product_type: 'Audio',
    tags: 'audio,wireless,bluetooth',
    status: 'active',
    createdAt: new Date().toISOString(),
  },
  {
    id: '2',
    title: 'Smart Watch X',
    bodyHtml: '<p>Advanced smartwatch with health monitoring, GPS, and 7-day battery life.</p>',
    vendor: 'MindFlow Store',
    product_type: 'Wearables',
    tags: 'wearable,smartwatch,fitness',
    status: 'active',
    createdAt: new Date().toISOString(),
  },
  {
    id: '3',
    title: 'Portable Power Bank 20000mAh',
    bodyHtml: '<p>High-capacity power bank with fast charging and USB-C PD support.</p>',
    vendor: 'MindFlow Store',
    product_type: 'Accessories',
    tags: 'accessories,charging,portable',
    status: 'draft',
    createdAt: new Date().toISOString(),
  },
];

const DEMO_ORDERS: ShopifyOrder[] = [
  {
    id: '1',
    orderNumber: 1001,
    totalPrice: '129.99',
    currency: 'USD',
    fulfillmentStatus: 'fulfilled',
    createdAt: new Date(Date.now() - 86400000).toISOString(),
    customer: { firstName: 'Alice', lastName: 'Chen', email: 'alice@example.com' },
    lineItems: [
      { id: 1, title: 'Wireless Earbuds Pro', quantity: 1, price: '129.99' },
    ],
    riskLevel: 'low',
  },
  {
    id: '2',
    orderNumber: 1002,
    totalPrice: '249.50',
    currency: 'USD',
    fulfillmentStatus: 'partial',
    createdAt: new Date(Date.now() - 172800000).toISOString(),
    customer: { firstName: 'Bob', lastName: 'Smith', email: 'bob@example.com' },
    lineItems: [
      { id: 2, title: 'Smart Watch X', quantity: 1, price: '249.50' },
    ],
    riskLevel: 'medium',
  },
  {
    id: '3',
    orderNumber: 1003,
    totalPrice: '89.00',
    currency: 'USD',
    fulfillmentStatus: 'unfulfilled',
    createdAt: new Date(Date.now() - 259200000).toISOString(),
    customer: { firstName: 'Carol', lastName: 'Wu', email: 'carol@example.com' },
    lineItems: [
      { id: 3, title: 'Portable Power Bank', quantity: 1, price: '89.00' },
    ],
    riskLevel: 'low',
  },
];

function isDemoMode(): boolean {
  return process.env.DEMO_MODE === 'true';
}

async function shopifyFetch<T>(path: string, options?: RequestInit): Promise<T> {
  logger.debug('Shopify request', { path, method: options?.method || 'GET' });

  // Return demo data ONLY when explicitly enabled via DEMO_MODE=true
  if (isDemoMode()) {
    logger.debug('Shopify demo mode', { path });
    await new Promise((r) => setTimeout(r, 300)); // Simulate network delay

    if (path.includes('/products.json')) {
      return { products: DEMO_PRODUCTS } as T;
    }
    if (path.includes('/orders.json')) {
      return { orders: DEMO_ORDERS } as T;
    }
    if (path.includes('/products/') && path.includes('.json')) {
      const id = parseInt(path.split('/products/')[1]?.split('.')[0]);
      const product = DEMO_PRODUCTS.find((p) => p.id === String(id));
      return { product: product || DEMO_PRODUCTS[0] } as T;
    }
    throw new Error(`Demo mode: unknown Shopify path ${path}`);
  }

  // Real Shopify API call - requires credentials
  try {
    const res = await fetch(shopifyUrl(path), {
      ...options,
      headers: {
        ...getHeaders(),
        ...(options?.headers || {}),
      },
    });

    if (!res.ok) {
      const retryAfter = extractRetryAfter(new Error(`Shopify API error: ${res.status}`));
      logger.error('Shopify API error', { path, status: res.status, statusText: res.statusText });
      throw new ExternalServiceError(
        'shopify',
        res.status,
        `Shopify API error: ${res.status} ${res.statusText}`,
        retryAfter !== null || res.status >= 500,
      );
    }

    logger.debug('Shopify request completed', { path, status: res.status });
    return res.json();
  } catch (error) {
    logger.error('Shopify request failed', { path, error });
    throw error;
  }
}

export async function getProducts() {
  logger.info('Fetching Shopify products');
  return withRetry(
    () => shopifyFetch<{ products: ShopifyProduct[] }>('/products.json?limit=20'),
    {
      maxRetries: 3,
      baseDelayMs: 1000,
      maxDelayMs: 10000,
      backoffFactor: 2,
    }
  ).then((data) => {
    logger.info('Products fetched', { count: data.products.length });
    return data.products;
  }).catch((error) => {
    logger.error('Failed to fetch products', { error });
    throw error;
  });
}

export async function getProduct(id: string) {
  logger.info('Fetching Shopify product', { id });
  return withRetry(
    () => shopifyFetch<{ product: ShopifyProduct }>(`/products/${id}.json`),
    {
      maxRetries: 3,
      baseDelayMs: 500,
      maxDelayMs: 5000,
      backoffFactor: 2,
    }
  ).then((data) => data.product);
}

export async function createProductDraft(input: { title: string; bodyHtml: string; tags: string }) {
  logger.info('Creating Shopify product draft', { title: input.title });
  return withRetry(
    () =>
      shopifyFetch<{ product: ShopifyProduct }>('/products.json', {
        method: 'POST',
        body: JSON.stringify({
          product: {
            title: input.title,
            body_html: input.bodyHtml,
            tags: input.tags,
            status: 'draft',
          },
        }),
      }),
    {
      maxRetries: 2,
      baseDelayMs: 1000,
      maxDelayMs: 5000,
      backoffFactor: 2,
    }
  ).then((data) => data.product);
}

export async function getOrders() {
  logger.info('Fetching Shopify orders');
  return withRetry(
    () => shopifyFetch<{ orders: ShopifyOrder[] }>('/orders.json?limit=20&status=any'),
    {
      maxRetries: 3,
      baseDelayMs: 1000,
      maxDelayMs: 10000,
      backoffFactor: 2,
    }
  ).then((data) => data.orders);
}

export { isDemoMode };
