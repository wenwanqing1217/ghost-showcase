/**
 * Ghost Platform — DS → Gateway API 代理工具
 *
 * 统一处理 Next.js API Route → Gateway 的转发逻辑：
 *   - 自动转发 X-Tenant-ID、Authorization 等关键 header
 *   - 透传请求 body（JSON）
 *   - 超时处理（15s）
 *   - 错误统一封装
 */

const GATEWAY_URL = process.env.GATEWAY_URL || 'http://gateway:18080';
const REQUEST_TIMEOUT_MS = 15_000;

/** 需要从客户端请求转发到 Gateway 的 header 白名单 */
const FORWARD_HEADERS = [
  'x-tenant-id',
  'authorization',
  'x-request-id',
  'x-correlation-id',
];

/** 开发环境默认 tenant ID（生产环境应由前端登录后获取真实 JWT） */
const DEFAULT_TENANT_ID = process.env.NEXT_PUBLIC_DEFAULT_TENANT_ID || 'ds-dev-tenant';

function buildGatewayHeaders(req: Request): HeadersInit {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  for (const key of FORWARD_HEADERS) {
    const value = req.headers.get(key);
    if (value) {
      headers[key] = value;
    }
  }
  // Alpha-ID CSRF middleware requires X-Requested-With for non-GET methods
  const method = req.method;
  if (method && method !== 'GET' && method !== 'HEAD' && !headers['x-requested-with']) {
    headers['x-requested-with'] = 'XMLHttpRequest';
  }
  // 开发环境：如果客户端未提供 X-Tenant-ID，使用默认值
  if (!headers['x-tenant-id']) {
    headers['x-tenant-id'] = DEFAULT_TENANT_ID;
  }
  return headers;
}

export async function proxyToGateway(
  req: Request,
  gatewayPath: string,
  options?: {
    method?: string;
    timeout?: number;
    body?: string;
  },
): Promise<Response> {
  const method = options?.method || req.method;
  const timeout = options?.timeout || REQUEST_TIMEOUT_MS;

  let body: BodyInit | undefined;
  if (options?.body !== undefined) {
    body = options.body;
  } else if (method !== 'GET' && method !== 'HEAD') {
    body = await req.text();
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);

  try {
    const res = await fetch(`${GATEWAY_URL}${gatewayPath}`, {
      method,
      headers: buildGatewayHeaders(req),
      body,
      signal: controller.signal,
    });
    return res;
  } catch (err) {
    if (err instanceof Error && err.name === 'AbortError') {
      return new Response(
        JSON.stringify({ error: 'Gateway 请求超时', detail: (err as Error).message }),
        { status: 504, headers: { 'Content-Type': 'application/json' } },
      );
    }
    return new Response(
      JSON.stringify({ error: 'Gateway 连接失败', detail: (err as Error).message }),
      { status: 502, headers: { 'Content-Type': 'application/json' } },
    );
  } finally {
    clearTimeout(timer);
  }
}
