/**
 * DS API 认证工具
 *
 * 通过 Authorization: Bearer <token> 头验证请求。
 * 环境变量 DS_API_KEY 设置后，所有受保护端点都需要验证。
 * 未设置时，认证禁用（开发模式）。
 */

const DS_API_KEY = process.env.DS_API_KEY || '';

export interface AuthResult {
  ok: boolean;
  error?: string;
}

/**
 * 验证请求是否已认证
 * 返回 { ok: true } 或 { ok: false, error: '...' }
 */
export function verifyRequest(req: Request): AuthResult {
  // 未配置 API Key 时跳过认证（开发模式）
  if (!DS_API_KEY) {
    return { ok: true };
  }

  const authHeader = req.headers.get('authorization') || '';
  const token = authHeader.startsWith('Bearer ') ? authHeader.slice(7) : '';

  if (!token) {
    return { ok: false, error: '缺少 Authorization 头' };
  }

  // 恒定时间比较（防时序攻击）
  if (!timingSafeEqual(token, DS_API_KEY)) {
    return { ok: false, error: '无效的 API Key' };
  }

  return { ok: true };
}

/**
 * 恒定时间字符串比较（防时序攻击）
 */
function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) {
    // 长度不等时仍执行比较（避免泄露长度信息），但返回 false
    // 使用固定长度比较
    const maxLen = Math.max(a.length, b.length);
    const aPadded = a.padEnd(maxLen, '\0');
    const bPadded = b.padEnd(maxLen, '\0');
    let result = 0;
    for (let i = 0; i < maxLen; i++) {
      result |= aPadded.charCodeAt(i) ^ bPadded.charCodeAt(i);
    }
    return false; // 长度不等必定不匹配
  }
  let result = 0;
  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return result === 0;
}
