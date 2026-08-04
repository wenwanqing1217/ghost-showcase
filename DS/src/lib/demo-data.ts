/**
 * Ghost Platform — 共享演示数据层
 *
 * 所有前端页面从这里读取一致的演示数据，
 * 避免各页面各自硬编码导致数据不连通。
 */

// ── 当前用户 ──
export const DEMO_USER = {
  alphaId: 'Alpha-001',
  did: 'did:alpha:alpha001',
  name: 'Ghost User',
  email: 'ghost@example.com',
  env: 'production',
};

// ── 演示商品（与数据库 seed 一致）──
export const DEMO_PRODUCTS = [
  {
    id: 'demo-p-001',
    externalId: 'demo-ext-001',
    title: 'Ghost Platform 智能助手订阅',
    description: 'AI 驱动的个人助理服务',
    price: 29.99,
    comparePrice: 39.99,
    currency: 'USD',
    inventory: 999,
    status: 'active',
  },
  {
    id: 'demo-p-002',
    externalId: 'demo-ext-002',
    title: 'AI 记忆图谱高级版',
    description: '三层记忆架构 + 因果图谱',
    price: 49.99,
    comparePrice: 69.99,
    currency: 'USD',
    inventory: 500,
    status: 'active',
  },
  {
    id: 'demo-p-003',
    externalId: 'demo-ext-003',
    title: 'A2A 智能体协作套件',
    description: '多智能体协作开发环境',
    price: 99.99,
    comparePrice: 149.99,
    currency: 'USD',
    inventory: 200,
    status: 'active',
  },
  {
    id: 'demo-p-004',
    externalId: 'demo-ext-004',
    title: 'DID 身份验证服务年卡',
    description: 'Ed25519 去中心化身份',
    price: 19.99,
    comparePrice: 29.99,
    currency: 'USD',
    inventory: 1000,
    status: 'active',
  },
  {
    id: 'demo-p-005',
    externalId: 'demo-ext-005',
    title: 'Web4.0 开发者工具包',
    description: '开源 A2A 基础设施',
    price: 0,
    comparePrice: null,
    currency: 'USD',
    inventory: 0,
    status: 'draft',
  },
];

// ── 演示订单（与商品关联）──
export const DEMO_ORDERS = [
  {
    id: 'demo-ord-001',
    externalId: 'ext-ord-001',
    orderNo: 'ORD-000001',
    amount: 29.99,
    currency: 'USD',
    status: 'pending',
    customerName: 'Alice Chen',
    customerEmail: 'alice@example.com',
    itemCount: 1,
    productId: 'demo-p-001',
    productTitle: 'Ghost Platform 智能助手订阅',
    createdAt: '2026-08-04T06:41:00Z',
  },
  {
    id: 'demo-ord-002',
    externalId: 'ext-ord-002',
    orderNo: 'ORD-000002',
    amount: 149.98,
    currency: 'USD',
    status: 'processing',
    customerName: 'Bob Wang',
    customerEmail: 'bob@example.com',
    itemCount: 2,
    productId: 'demo-p-003',
    productTitle: 'A2A 智能体协作套件',
    createdAt: '2026-08-04T07:41:00Z',
  },
  {
    id: 'demo-ord-003',
    externalId: 'ext-ord-003',
    orderNo: 'ORD-000003',
    amount: 49.99,
    currency: 'USD',
    status: 'shipped',
    customerName: 'Carol Li',
    customerEmail: 'carol@example.com',
    itemCount: 1,
    productId: 'demo-p-002',
    productTitle: 'AI 记忆图谱高级版',
    createdAt: '2026-08-04T05:41:00Z',
  },
  {
    id: 'demo-ord-004',
    externalId: 'ext-ord-004',
    orderNo: 'ORD-000004',
    amount: 99.99,
    currency: 'USD',
    status: 'delivered',
    customerName: 'David Zhang',
    customerEmail: 'david@example.com',
    itemCount: 1,
    productId: 'demo-p-003',
    productTitle: 'A2A 智能体协作套件',
    createdAt: '2026-08-03T08:41:00Z',
  },
  {
    id: 'demo-ord-005',
    externalId: 'ext-ord-005',
    orderNo: 'ORD-000005',
    amount: 0,
    currency: 'USD',
    status: 'cancelled',
    customerName: 'Eve Liu',
    customerEmail: 'eve@example.com',
    itemCount: 0,
    productId: null,
    productTitle: null,
    createdAt: '2026-08-04T08:11:00Z',
  },
];

// ── 演示客户 ──
export const DEMO_CUSTOMERS = [
  { id: 'c-001', name: 'Alice Chen', email: 'alice@example.com', orders: 1, totalSpent: 29.99 },
  { id: 'c-002', name: 'Bob Wang', email: 'bob@example.com', orders: 1, totalSpent: 149.98 },
  { id: 'c-003', name: 'Carol Li', email: 'carol@example.com', orders: 1, totalSpent: 49.99 },
  { id: 'c-004', name: 'David Zhang', email: 'david@example.com', orders: 1, totalSpent: 99.99 },
  { id: 'c-005', name: 'Eve Liu', email: 'eve@example.com', orders: 1, totalSpent: 0 },
];

// ── 演示社交数据 ──
export const DEMO_FRIENDS = [
  { alpha_id: 'Alpha-002', name: 'Bob Wang', status: 'accepted', created_at: '2026-07-20T00:00:00Z' },
  { alpha_id: 'Alpha-003', name: 'Carol Li', status: 'accepted', created_at: '2026-07-22T00:00:00Z' },
];

export const DEMO_MESSAGES = [
  { message_id: 'msg-001', from_alpha_id: 'Alpha-002', to_alpha_id: 'Alpha-001', content: '你好！看到你对 A2A 协议感兴趣，想聊聊合作。', created_at: '2026-08-03T10:00:00Z' },
  { message_id: 'msg-002', from_alpha_id: 'Alpha-001', to_alpha_id: 'Alpha-002', content: '好的，Ghost Platform 的 A2A 支持多种协议适配。', created_at: '2026-08-03T10:05:00Z' },
  { message_id: 'msg-003', from_alpha_id: 'Alpha-003', to_alpha_id: 'Alpha-001', content: '记忆图谱的功能很赞，有 API 可以接入吗？', created_at: '2026-08-04T08:00:00Z' },
];

// ── 演示记忆图谱 ──
export const DEMO_MEMORY_NODES = [
  { id: '1', type: 'atom', label: '用户身份', content: `${DEMO_USER.alphaId} 已注册`, timestamp: '2026-08-01T00:00:00Z', connections: ['2', '3'] },
  { id: '2', type: 'memory', label: '对话记忆 #1', content: '用户询问过产品推荐', timestamp: '2026-08-02T00:00:00Z', connections: ['1', '4'] },
  { id: '3', type: 'context', label: '上下文', content: '电商场景', timestamp: '2026-08-01T00:00:00Z', connections: ['1'] },
  { id: '4', type: 'relation', label: '关联', content: '产品 → 订单', timestamp: '2026-08-03T00:00:00Z', connections: ['2'] },
];

// ── 演示 A2A Agents ──
export const DEMO_AGENTS = [
  { alpha_id: 'Alpha-001', name: 'Ghost User', skills: ['chat', 'memory', 'workflow'], status: 'online' },
  { alpha_id: 'Alpha-002', name: 'Bob Agent', skills: ['code', 'analysis'], status: 'online' },
  { alpha_id: 'Alpha-003', name: 'Carol Agent', skills: ['writing', 'translation'], status: 'away' },
];

// ── 演示工作流执行记录 ──
export interface WorkflowExecution {
  id: string;
  template_id: string;
  status: 'running' | 'completed' | 'failed';
  input: string;
  result?: string;
  started_at: string;
  finished_at?: string;
}

export const DEMO_EXECUTIONS: WorkflowExecution[] = [
  {
    id: 'wf-001',
    template_id: 'map-navigation',
    status: 'completed',
    input: '怎么去中关村',
    result: '推荐路线：地铁4号线 → 中关村站，约35分钟',
    started_at: '2026-08-04T10:00:00Z',
    finished_at: '2026-08-04T10:00:05Z',
  },
  {
    id: 'wf-002',
    template_id: 'douyin-publish',
    status: 'completed',
    input: '生成一个霸道总裁剧本',
    result: '剧本已生成，包含3幕场景，共1200字',
    started_at: '2026-08-04T09:30:00Z',
    finished_at: '2026-08-04T09:30:12Z',
  },
  {
    id: 'wf-003',
    template_id: 'shopify-optimize',
    status: 'failed',
    input: '优化我的店铺',
    result: '未检测到 Shopify 店铺连接',
    started_at: '2026-08-04T08:00:00Z',
    finished_at: '2026-08-04T08:00:02Z',
  },
];

// ── 平台统计（用于首页和 dashboard）──
export const DEMO_STATS = {
  totalAtoms: 20,
  capabilityDomains: 9,
  thinkingFrameworks: 6,
  mvpDays: 90,
  totalProducts: DEMO_PRODUCTS.length,
  activeProducts: DEMO_PRODUCTS.filter(p => p.status === 'active').length,
  totalOrders: DEMO_ORDERS.length,
  totalRevenue: DEMO_ORDERS.reduce((sum, o) => sum + o.amount, 0),
};
