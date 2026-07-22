/**
 * 服务间认证中间件
 *
 * 验证来自其他内部服务（如 mindflow-map）的 API 调用。
 * 通过 X-Service-Key 头与 DS_API_KEY 环境变量对比。
 *
 * 用法：
 *   const auth = validateServiceKey(request);
 *   if (!auth.valid) {
 *     return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
 *   }
 */

export interface ServiceAuthResult {
  valid: boolean;
  error?: string;
}

/**
 * 验证服务间调用密钥
 */
export function validateServiceKey(request: Request): ServiceAuthResult {
  const serviceKey = request.headers.get('x-service-key');
  const expectedKey = process.env.DS_API_KEY;

  // 如果未配置 DS_API_KEY，则拒绝所有服务调用
  if (!expectedKey) {
    return { valid: false, error: 'Service auth not configured' };
  }

  if (!serviceKey) {
    return { valid: false, error: 'Missing X-Service-Key header' };
  }

  // 恒定时间比较防止时序攻击
  if (!timingSafeEqual(serviceKey, expectedKey)) {
    return { valid: false, error: 'Invalid service key' };
  }

  return { valid: true };
}

/**
 * 恒定时间字符串比较（防止时序攻击）
 */
function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) {
    // 仍然执行比较以防止泄露长度信息
    const dummy = 'x'.repeat(b.length);
    let result = 0;
    for (let i = 0; i < b.length; i++) {
      result |= dummy.charCodeAt(i) ^ b.charCodeAt(i);
    }
    return false;
  }

  let result = 0;
  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return result === 0;
}
