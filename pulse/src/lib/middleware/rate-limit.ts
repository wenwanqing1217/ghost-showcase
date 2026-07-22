type Store = Map<string, { count: number; resetAt: number }>;

const stores = new Map<string, Store>();

export interface RateLimitOptions {
  /** Maximum number of requests allowed in the window */
  limit: number;
  /** Window duration in milliseconds */
  windowMs: number;
  /** Identifier function — defaults to IP address */
  keyGenerator?: (request: Request) => string;
  /** Custom store name for isolating rate limiters */
  storeName?: string;
}

export interface RateLimitResult {
  success: boolean;
  remaining: number;
  resetAt: number;
  retryAfterMs?: number;
}

const DEFAULT_STORE = 'default';

function getStore(name: string): Store {
  const existing = stores.get(name);
  if (existing) return existing;

  const store: Store = new Map();
  stores.set(name, store);
  return store;
}

function cleanup(store: Store) {
  const now = Date.now();
  for (const [key, entry] of Array.from(store.entries())) {
    if (entry.resetAt <= now) {
      store.delete(key);
    }
  }
}

export function createRateLimiter(options: RateLimitOptions) {
  const {
    limit,
    windowMs,
    keyGenerator = (req) => {
      const headers = req?.headers;
      const forwarded = headers?.get ? headers.get('x-forwarded-for') : undefined;
      const ip = forwarded ? forwarded.split(',')[0].trim() : 'unknown';
      return ip;
    },
    storeName = DEFAULT_STORE,
  } = options;

  const store = getStore(storeName);

  return async function rateLimit(request?: Request): Promise<RateLimitResult> {
    if (!request) {
      return {
        success: true,
        remaining: limit,
        resetAt: Date.now() + windowMs,
      };
    }

    const key = `${storeName}:${keyGenerator(request)}`;
    const now = Date.now();

    cleanup(store);

    const entry = store.get(key);

    if (!entry || entry.resetAt <= now) {
      const resetAt = now + windowMs;
      store.set(key, { count: 1, resetAt });
      return {
        success: true,
        remaining: limit - 1,
        resetAt,
      };
    }

    if (entry.count >= limit) {
      const retryAfterMs = entry.resetAt - now;
      return {
        success: false,
        remaining: 0,
        resetAt: entry.resetAt,
        retryAfterMs,
      };
    }

    entry.count += 1;
    return {
      success: true,
      remaining: limit - entry.count,
      resetAt: entry.resetAt,
    };
  };
}

export function rateLimitHeaders(result: RateLimitResult) {
  const headers: Record<string, string> = {
    'X-RateLimit-Limit': String(result.remaining + (result.success ? 0 : 1)),
    'X-RateLimit-Remaining': String(result.remaining),
    'X-RateLimit-Reset': String(Math.ceil(result.resetAt / 1000)),
  };

  if (result.retryAfterMs) {
    headers['Retry-After'] = String(Math.ceil(result.retryAfterMs / 1000));
  }

  return headers;
}

export const defaultRateLimiter = createRateLimiter({
  limit: 60,
  windowMs: 60_000,
});

export const strictRateLimiter = createRateLimiter({
  limit: 10,
  windowMs: 60_000,
});

export const aiRateLimiter = createRateLimiter({
  limit: 10,
  windowMs: 60_000,
});
