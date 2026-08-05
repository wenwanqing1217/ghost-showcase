/**
 * Gateway API Client — routes ecommerce requests through Gateway
 * 
 * In production (Docker): browser → Gateway (:18080/v1/ecom/*) → DS API
 * In development: browser → DS API routes directly (localhost:3000/api/*)
 * 
 * The Gateway provides:
 * - Tenant injection (X-Tenant-ID header)
 * - Rate limiting
 * - Audit logging
 * - Centralized auth
 */

const GATEWAY_URL = process.env.NEXT_PUBLIC_GATEWAY_URL || '';
const DS_API_PREFIX = '/api';
const GATEWAY_ECOM_PREFIX = '/v1/ecom';

// Map DS API routes to Gateway ecom routes
const ROUTE_MAP: Record<string, string> = {
  '/api/products': '/products',
  '/api/orders': '/orders',
  '/api/stats': '/stats',
  '/api/sync': '/sync',
  '/api/shop': '/shop',
  '/api/health': '/health',
};

/**
 * Get the full URL for an API call.
 * If GATEWAY_URL is configured, route ecom calls through Gateway.
 * Otherwise, use DS API routes directly.
 */
export function getApiUrl(path: string, searchParams?: URLSearchParams): string {
  // If Gateway URL is configured, route ecom calls through Gateway
  if (GATEWAY_URL && ROUTE_MAP[path]) {
    const gatewayPath = ROUTE_MAP[path];
    const queryString = searchParams ? `?${searchParams.toString()}` : '';
    return `${GATEWAY_URL}${GATEWAY_ECOM_PREFIX}${gatewayPath}${queryString}`;
  }
  
  // Default: DS API route directly
  const queryString = searchParams ? `?${searchParams.toString()}` : '';
  return `${path}${queryString}`;
}

/**
 * Check if a path should be routed through Gateway
 */
export function isEcomPath(path: string): boolean {
  return path in ROUTE_MAP;
}

/**
 * Get headers for Gateway requests
 */
export function getGatewayHeaders(extraHeaders?: Record<string, string>): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...extraHeaders,
  };
  return headers;
}
