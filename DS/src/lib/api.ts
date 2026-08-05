/**
 * Ghost Platform — API 客户端
 *
 * 统一的后端 API 调用层
 * 所有请求通过 Gateway (:18080) 转发到对应服务
 *
 * 清理说明（2026-08-05）：删除了 agentApi/flowApi/internalApi/netApi/healthApi
 * 等 15+ 个指向不存在端点的死方法。只保留 humanApi 中被 chat/memory 页面实际使用的 4 个方法。
 * 如果未来需要新端点，请先在 DS/src/app/api/ 下创建对应 route.ts 再在此添加方法。
 */

// ── 基础配置 ──
// 所有请求通过 Next.js API 路由（/api/v1/*）转发到 Gateway
// 这样在 Docker 和本地开发都能正常工作
const API_PREFIX = '/api/v1';

// ── 请求拦截器 ──
async function request<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_PREFIX}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    credentials: 'include', // 携带 cookie（用于 session）
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      error: `HTTP ${response.status}: ${response.statusText}`,
    }));
    throw new Error(error.error || `Request failed: ${response.status}`);
  }

  return response.json();
}

// ── Human API（身份、聊天、记忆）──
// 仅保留被 chat/page.tsx 和 memory/page.tsx 实际使用的方法
export const humanApi = {
  /** 获取当前用户身份信息 */
  getIdentity: () => request('/human/identity'),

  /** 发送聊天消息 */
  chat: (message: string, alphaId?: string) =>
    request('/human/chat', {
      method: 'POST',
      body: JSON.stringify({ message, alpha_id: alphaId }),
    }),

  /** 获取记忆图谱 */
  getMemoryGraph: () => request('/human/memory/graph'),

  /** 搜索记忆 */
  searchMemory: (query: string) =>
    request(`/human/memory/search?q=${encodeURIComponent(query)}`),
};
