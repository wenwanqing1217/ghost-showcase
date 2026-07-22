/**
 * Production-ready error handling and retry utilities
 */

export type RetryOptions = {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
  backoffFactor: number;
  retryableStatuses?: number[];
};

export type RateLimitOptions = {
  maxConcurrent: number;
  minDelayMs: number;
};

export class ExternalServiceError extends Error {
  constructor(
    public service: string,
    public statusCode: number,
    message: string,
    public retryable: boolean = false
  ) {
    super(message);
    this.name = 'ExternalServiceError';
  }
}

export class RateLimitError extends ExternalServiceError {
  readonly retryAfterMs: number;

  constructor(service: string, retryAfterMs: number) {
    super(service, 429, `Rate limit hit for ${service}. Retry after ${retryAfterMs}ms`, true);
    this.retryAfterMs = retryAfterMs;
    this.name = 'RateLimitError';
  }
}

export async function withRetry<T>(
  operation: () => Promise<T>,
  options: RetryOptions = {
    maxRetries: 3,
    baseDelayMs: 1000,
    maxDelayMs: 30000,
    backoffFactor: 2,
  }
): Promise<T> {
  const { maxRetries, baseDelayMs, maxDelayMs, backoffFactor, retryableStatuses = [429, 500, 502, 503, 504] } = options;

  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));

      if (!isRetryable(lastError, retryableStatuses)) {
        throw lastError;
      }

      if (attempt === maxRetries) {
        break;
      }

      const delay = Math.min(baseDelayMs * Math.pow(backoffFactor, attempt), maxDelayMs);
      await sleep(delay);
    }
  }

  throw lastError;
}

export async function withRateLimit<T>(
  operation: () => Promise<T>,
  options: RateLimitOptions = {
    maxConcurrent: 3,
    minDelayMs: 200,
  }
): Promise<T> {
  const { maxConcurrent, minDelayMs } = options;
  
  const queue: Array<() => Promise<void>> = [];
  let running = 0;

  const processQueue = async () => {
    while (queue.length > 0 && running < maxConcurrent) {
      const next = queue.shift();
      if (!next) break;
      
      running++;
      await next();
      running--;
      await sleep(minDelayMs);
    }
  };

  return new Promise((resolve, reject) => {
    queue.push(async () => {
      try {
        const result = await operation();
        resolve(result);
      } catch (error) {
        reject(error);
      }
    });
    processQueue();
  });
}

function isRetryable(error: Error, retryableStatuses: number[]): boolean {
  if (error instanceof RateLimitError) return true;
  if (error instanceof ExternalServiceError) return error.retryable;
  
  const statusMatch = error.message.match(/status[:\s]+(\d{3})/i);
  if (statusMatch) {
    const status = parseInt(statusMatch[1], 10);
    return retryableStatuses.includes(status);
  }
  
  return false;
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export function extractRetryAfter(error: unknown): number | null {
  if (error instanceof RateLimitError) {
    return error.retryAfterMs ?? null;
  }
  if (error instanceof Error && error.message.includes('Retry-After')) {
    const match = error.message.match(/Retry-After:\s*(\d+)/i);
    if (match) return parseInt(match[1], 10) * 1000;
  }
  return null;
}
