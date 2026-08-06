/**
 * AI 文案生成服务 — 三档免费策略
 *
 * 1. Demo 模式（默认）：无需 API Key，本地模板生成
 * 2. Groq 免费：https://console.groq.com 注册即送额度，Llama 3.3 70B
 * 3. DeepSeek / OpenAI：付费但更强
 *
 * 环境变量：
 *   AI_API_KEY    ← 有值则调外部 API，无值则 Demo 模式
 *   AI_BASE_URL   ← API 端点
 *   AI_MODEL      ← 模型名
 */

// 安全: 允许的 AI API 域名白名单（防止 SSRF）
const AI_ALLOWED_HOSTS = [
  'api.groq.com',
  'api.openai.com',
  'api.deepseek.com',
  'api.deepseek.cn',
];

function resolveAiBaseUrl(): string {
  const raw = process.env.AI_BASE_URL || 'https://api.groq.com/openai/v1';
  let parsed: URL;
  try {
    parsed = new URL(raw);
  } catch {
    console.warn('[AI] AI_BASE_URL 无效，回退到默认');
    return 'https://api.groq.com/openai/v1';
  }
  // 仅允许 https
  if (parsed.protocol !== 'https:') {
    console.warn('[AI] AI_BASE_URL 必须使用 HTTPS，回退到默认');
    return 'https://api.groq.com/openai/v1';
  }
  // 域名白名单校验
  if (!AI_ALLOWED_HOSTS.includes(parsed.hostname)) {
    console.warn(`[AI] AI_BASE_URL 域名 ${parsed.hostname} 不在白名单，回退到默认`);
    return 'https://api.groq.com/openai/v1';
  }
  return raw;
}

const AI_BASE_URL = resolveAiBaseUrl();
const AI_MODEL = process.env.AI_MODEL || 'llama-3.3-70b-versatile';
const AI_API_KEY = process.env.AI_API_KEY || '';

// ── 类型 ──
export interface ProductCopyInput {
  title: string;
  description?: string | null;
  keywords?: string[];
  tone?: 'professional' | 'casual' | 'luxury' | 'fun';
  lang?: 'zh' | 'en';
}

export interface ProductCopyOutput {
  title: string;
  description: string;
  keywords: string[];
  mode: 'demo' | 'api';  // 标识生成方式
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
  };
}

// ── 检查可用性 ──
export function isAiAvailable(): boolean {
  return true; // Demo 模式始终可用
}

export function getAiMode(): 'demo' | 'api' {
  return AI_API_KEY ? 'api' : 'demo';
}

// ════════════════════════════════════════════════════════════════════
// Demo 模式：本地模板生成（零成本，无需网络）
// ════════════════════════════════════════════════════════════════════

const TONE_PREFIXES: Record<string, string[]> = {
  professional: ['精选', '品质', '匠心打造', '专业之选'],
  casual: ['好物推荐', '生活必备', '轻松拥有', '日常好物'],
  luxury: ['臻品', '限量', '尊享', '高端定制'],
  fun: ['宝藏好物', '神仙单品', '绝绝子', 'yyds'],
};

const TONE_SUFFIXES: Record<string, string[]> = {
  professional: ['品质保障', '值得信赖', '专业认证'],
  casual: ['好用不贵', '居家必备', '入手不亏'],
  luxury: ['彰显品味', '独一无二', '尊贵体验'],
  fun: ['冲就完了', '不买后悔', '真的绝了'],
};

function demoGenerate(input: ProductCopyInput): ProductCopyOutput {
  const { title, description, tone = 'professional', lang = 'zh' } = input;

  if (lang === 'en') {
    return demoGenerateEn(title, description, tone);
  }

  const prefixes = TONE_PREFIXES[tone] || TONE_PREFIXES.professional;
  const suffixes = TONE_SUFFIXES[tone] || TONE_SUFFIXES.professional;

  // 智能提取核心词
  const coreWord = extractCoreWord(title);

  // 生成标题：前缀 + 核心词 + 卖点
  const prefix = prefixes[Math.floor(Math.random() * prefixes.length)];
  const newTitle = `${prefix}${coreWord} | ${suffixes[0]} · ${suffixes[1]}`;

  // 生成描述：HTML 格式
  const descPoints = [
    description ? `【产品亮点】${description}` : `【核心卖点】${coreWord}，${suffixes[0]}`,
    `【品质承诺】${prefix}标准，${suffixes[1]}`,
    `【适用场景】居家、办公、送礼皆宜，${suffixes[2]}`,
    `【售后保障】7天无理由退换，品质保证`,
  ];

  const newDescription = descPoints.map((p) => `<p>${p}</p>`).join('\n');

  // 生成关键词
  const keywords = [
    coreWord,
    prefix + coreWord,
    suffixes[0],
    tone === 'professional' ? '品质好物' : tone === 'luxury' ? '高端好物' : '性价比好物',
    '跨境电商',
    '独立站热销',
  ];

  return {
    title: newTitle.slice(0, 60),
    description: newDescription,
    keywords: keywords.slice(0, 6),
    mode: 'demo',
    usage: { prompt_tokens: 0, completion_tokens: 0 },
  };
}

function demoGenerateEn(title: string, description: string | null | undefined, tone: string): ProductCopyOutput {
  const toneMap: Record<string, { adj: string; tag: string }> = {
    professional: { adj: 'Premium', tag: 'Quality Guaranteed' },
    casual: { adj: 'Everyday Essential', tag: 'Great Value' },
    luxury: { adj: 'Luxury', tag: 'Exclusive Collection' },
    fun: { adj: 'Awesome', tag: 'Must-Have' },
  };
  const t = toneMap[tone] || toneMap.professional;
  const coreWord = extractCoreWord(title);

  const newTitle = `${t.adj} ${coreWord} | ${t.tag} - Free Shipping`;

  const descPoints = [
    description ? `<p><strong>Feature:</strong> ${description}</p>` : '',
    `<p><strong>Quality:</strong> ${t.adj} grade materials, ${t.tag.toLowerCase()}.</p>`,
    `<p><strong>Versatile:</strong> Perfect for home, office, or as a gift.</p>`,
    `<p><strong>Guarantee:</strong> 30-day money back, hassle-free returns.</p>`,
  ];

  return {
    title: newTitle.slice(0, 80),
    description: descPoints.filter(Boolean).join('\n'),
    keywords: [coreWord, t.adj + ' ' + coreWord, t.tag, 'cross-border', 'free shipping', 'best seller'],
    mode: 'demo',
    usage: { prompt_tokens: 0, completion_tokens: 0 },
  };
}

/** 从标题提取核心产品词 */
function extractCoreWord(title: string): string {
  // 去掉常见修饰词，提取核心名词
  const noise = ['简约', '现代', '北欧', '日式', '美式', '复古', '新款', '爆款', '网红', 'ins'];
  let result = title;
  for (const n of noise) {
    result = result.replace(n, '');
  }
  return result.trim() || title;
}

// ════════════════════════════════════════════════════════════════════
// API 模式：调用外部 LLM（Groq / DeepSeek / OpenAI）
// ════════════════════════════════════════════════════════════════════

async function apiGenerate(input: ProductCopyInput): Promise<ProductCopyOutput> {
  const { title, description, keywords = [], tone = 'professional', lang = 'zh' } = input;

  const toneMap: Record<string, string> = {
    professional: '专业可信',
    casual: '亲切自然',
    luxury: '高端奢华',
    fun: '活泼有趣',
  };

  const systemPrompt = `你是跨境电商运营专家，为独立站商品写 SEO 文案。
- 风格：${toneMap[tone]}
- 语言：${lang === 'zh' ? '中文' : '英文'}
- 标题：突出卖点+关键词，60字以内
- 描述：3-5个卖点，HTML格式（<p>和<strong>标签）
- 输出纯JSON：{"title":"...","description":"...","keywords":["..."]}
- 不要 Markdown 包裹`;

  const response = await fetch(`${AI_BASE_URL}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${AI_API_KEY}`,
    },
    body: JSON.stringify({
      model: AI_MODEL,
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: JSON.stringify({ title, description, keywords }) },
      ],
      temperature: 0.7,
      max_tokens: 1000,
      response_format: { type: 'json_object' },
    }),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`AI API ${response.status}: ${text}`);
  }

  const data = await response.json();
  const content = data.choices?.[0]?.message?.content;
  if (!content) throw new Error('AI 返回空内容');

  let result: { title: string; description: string; keywords: string[] };
  try {
    result = JSON.parse(content);
  } catch {
    const match = content.match(/```(?:json)?\s*([\s\S]+?)\s*```/);
    result = match ? JSON.parse(match[1]) : { title, description: description || '', keywords };
  }

  return {
    title: result.title || title,
    description: result.description || description || '',
    keywords: result.keywords || keywords,
    mode: 'api',
    usage: {
      prompt_tokens: data.usage?.prompt_tokens || 0,
      completion_tokens: data.usage?.completion_tokens || 0,
    },
  };
}

// ════════════════════════════════════════════════════════════════════
// 统一入口
// ════════════════════════════════════════════════════════════════════

export async function generateProductCopy(input: ProductCopyInput): Promise<ProductCopyOutput> {
  if (!AI_API_KEY) {
    // Demo 模式：本地模板生成
    return demoGenerate(input);
  }
  return apiGenerate(input);
}

export async function batchGenerateCopy(
  items: ProductCopyInput[],
  onProgress?: (done: number, total: number) => void
): Promise<ProductCopyOutput[]> {
  const results: ProductCopyOutput[] = [];
  for (let i = 0; i < items.length; i++) {
    try {
      results.push(await generateProductCopy(items[i]));
    } catch (err) {
      // 失败时回退到 Demo 模式
      results.push(demoGenerate(items[i]));
    }
    onProgress?.(i + 1, items.length);
    if (i < items.length - 1) {
      await new Promise((r) => setTimeout(r, 500));
    }
  }
  return results;
}

// ════════════════════════════════════════════════════════════════════
// 渠道文案生成 — 闲鱼 / 小红书（低成本出海/变现渠道）
// 复用 AI_API_KEY：有 Key 走 LLM，无 Key 走本地模板（零成本）
// ════════════════════════════════════════════════════════════════════

export type ChannelPlatform = 'xianyu' | 'xiaohongshu' | 'douyin';

export interface ChannelCopyInput {
  platform: ChannelPlatform;
  product: string;          // 商品名/主题
  description?: string;     // 卖点描述
  price?: string;           // 价格（闲鱼用）
  condition?: string;       // 成色（闲鱼用，如"全新未拆"）
  tone?: 'professional' | 'casual' | 'luxury' | 'fun';
}

export interface ChannelCopyOutput {
  platform: ChannelPlatform;
  title: string;
  body: string;             // 正文（小红书笔记 / 闲鱼描述）
  tags: string[];           // 话题标签
  checklist: string[];      // 发布清单提示
  mode: 'demo' | 'api';
  usage: { prompt_tokens: number; completion_tokens: number };
}

// ── 闲鱼本地模板 ──
function demoXianyu(input: ChannelCopyInput): ChannelCopyOutput {
  const { product, description, price, condition, tone = 'casual' } = input;
  const core = extractCoreWord(product);

  const title = `${condition || '全新'} · ${core} ${price ? `¥${price}` : '低价出'}`.slice(0, 50);

  const body = [
    `【出】${product} ${condition || '全新未拆'}`,
    description ? `【卖点】${description}` : `【卖点】${core}，正品保证，成色极佳`,
    price ? `【价格】${price} 元，爽快包邮` : `【价格】私聊，爽快包邮`,
    `【交易】支持验货，闲鱼担保交易，发货前拍视频确认`,
    `【原因】个人闲置，回血出，非诚勿扰`,
  ].join('\n');

  const tags = [core, condition || '全新', '闲置回血', '包邮', '正品保证', '个人闲置'];
  const checklist = [
    '上传 3-9 张实拍图（首图最关键）',
    '标题前缀加【出】或【全新】提高点击率',
    '价格设略低于心理价，留议价空间',
    '发布后每天顶帖 1-2 次保持曝光',
    '回复问价要快，"亲要吗"主动促单',
  ];

  return { platform: 'xianyu', title, body, tags, checklist, mode: 'demo', usage: { prompt_tokens: 0, completion_tokens: 0 } };
}

// ── 小红书本地图 ──
function demoXiaohongshu(input: ChannelCopyInput): ChannelCopyOutput {
  const { product, description, tone = 'fun' } = input;
  const core = extractCoreWord(product);

  const emoji = ['✨', '🔥', '💕', '🌟', '💫', '🎁'];
  const e1 = emoji[Math.floor(Math.random() * emoji.length)];
  const e2 = emoji[Math.floor(Math.random() * emoji.length)];

  const titleMap: Record<string, string> = {
    professional: `${e1} ${core} 深度测评｜入手前必看`,
    casual: `${e1} 被问爆的${core}！真心推荐给大家`,
    luxury: `${e1} 高质感${core}｜提升幸福感的好物`,
    fun: `${e1}${e2} 救命！这个${core}也太绝了吧`,
  };

  const title = (titleMap[tone] || titleMap.fun).slice(0, 20);

  const body = [
    `${e1} 姐妹们！！这个${core}我真的逢人就推`,
    description ? `📌 ${description}` : `📌 用了一段时间，真心觉得值`,
    ``,
    `✅ 优点：`,
    `1️⃣ 颜值在线，摆哪儿都好看`,
    `2️⃣ 实用性强，日常必备`,
    `3️⃣ 性价比高，闭眼入不亏`,
    ``,
    `💡 适合人群：学生党 / 上班族 / 送礼`,
    ``,
    `姐妹们冲就完了！评论区问链接哈～`,
    `${e2} 收藏不迷路，点赞分享给需要的人`,
  ].join('\n');

  const tags = [`#${core}`, `#${core}推荐`, '#好物分享', '#种草', '#生活好物', '#平价好物', `#${core}测评`];
  const checklist = [
    '封面图用 3:4 竖图，文字大且醒目',
    '首图加 1-2 行大字标题（吸引点击）',
    '正文用 emoji 分段，易读性强',
    '发布时间：午休 12-13 点 / 晚上 20-22 点',
    '话题标签 5-8 个，混搭大词+精准词',
    '评论区主动互动，引导私信成交',
  ];

  return { platform: 'xiaohongshu', title, body, tags, checklist, mode: 'demo', usage: { prompt_tokens: 0, completion_tokens: 0 } };
}

// ── 抖音本地模板（图文/短视频配套文案：短句、有钩子、口语化） ──
function demoDouyin(input: ChannelCopyInput): ChannelCopyOutput {
  const { product, description, price, tone = 'fun' } = input;
  const core = extractCoreWord(product);

  const title = `${core}真实体验一周，值不值得买？`.slice(0, 30);

  const body = [
    `${core}，用了一周的真实感受👇`,
    description ? description : '颜值能打、日常刚需、性价比真的高',
    '',
    '✅ 优点：',
    '1️⃣ 上手简单，不用折腾',
    '2️⃣ 颜值在线，摆家里很出片',
    '3️⃣ 价格实在，学生党也友好',
    '',
    '📌 想看细节的评论区扣1，下期出教程',
  ].join('\n');

  const tags = [`#${core}`, '#种草', '#好物分享', '#测评', '#生活好物'];
  const checklist = [
    '视频/图文前 3 秒给结果或悬念（"值不值得买"钩子）',
    '文案口语化，短句快节奏，别念稿',
    '配 3-4 张实拍图或 15-30s 竖版视频',
    '结尾引导：关注/评论/收藏（提升完播和互动）',
    '发布时段：午 12-13 点 / 晚 19-22 点（流量高峰）',
    '置顶一条评论补充价格和购买方式',
  ];

  return { platform: 'douyin', title, body, tags, checklist, mode: 'demo', usage: { prompt_tokens: 0, completion_tokens: 0 } };
}

function demoChannel(input: ChannelCopyInput): ChannelCopyOutput {
  if (input.platform === 'xianyu') return demoXianyu(input);
  if (input.platform === 'douyin') return demoDouyin(input);
  return demoXiaohongshu(input);
}

// ── LLM 模式 ──
async function apiChannel(input: ChannelCopyInput): Promise<ChannelCopyOutput> {
  const { platform, product, description, price, condition, tone = 'casual' } = input;

  const platformBrief = platform === 'xianyu'
    ? `闲鱼二手交易平台。标题≤50字前缀加成色/价格；正文含【出】【卖点】【价格】【交易】【原因】；风格真诚简短；tags 5-6 个含"全新/闲置/包邮"等。`
    : platform === 'douyin'
    ? `抖音短视频/图文平台。标题≤30字有钩子（如"值不值得买/真实体验"）引导点击；正文口语化、短句快节奏、开头抓注意力、结尾引导关注评论；tags 3-5 个带 # 话题。`
    : `小红书种草平台。标题≤20字带 emoji 制造好奇；正文 emoji 分段，语气亲切（姐妹们/绝绝子）；结尾引导互动；tags 5-8 个带 # 话题。`;

  const systemPrompt = `你是社媒运营专家，为商品生成平台原生文案。
- 平台：${platformBrief}
- 风格：${tone}
- 输出纯 JSON：{"title":"...","body":"...","tags":["..."],"checklist":["..."]}
- checklist 给 5 条发布实操建议
- 不要 Markdown 包裹`;

  const userContent = JSON.stringify({ product, description, price, condition });

  const response = await fetch(`${AI_BASE_URL}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${AI_API_KEY}`,
    },
    body: JSON.stringify({
      model: AI_MODEL,
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userContent },
      ],
      temperature: 0.8,
      max_tokens: 1200,
      response_format: { type: 'json_object' },
    }),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`AI API ${response.status}: ${text}`);
  }

  const data = await response.json();
  const content = data.choices?.[0]?.message?.content;
  if (!content) throw new Error('AI 返回空内容');

  let parsed: { title: string; body: string; tags: string[]; checklist: string[] };
  try {
    parsed = JSON.parse(content);
  } catch {
    const m = content.match(/```(?:json)?\s*([\s\S]+?)\s*```/);
    parsed = m ? JSON.parse(m[1]) : demoChannel(input);
  }

  return {
    platform,
    title: parsed.title || '',
    body: parsed.body || '',
    tags: parsed.tags || [],
    checklist: parsed.checklist || [],
    mode: 'api',
    usage: {
      prompt_tokens: data.usage?.prompt_tokens || 0,
      completion_tokens: data.usage?.completion_tokens || 0,
    },
  };
}

export async function generateChannelCopy(input: ChannelCopyInput): Promise<ChannelCopyOutput> {
  if (!AI_API_KEY) {
    return demoChannel(input);
  }
  try {
    return await apiChannel(input);
  } catch (err) {
    console.warn('[AI] channel API 失败，回退 Demo:', err);
    return demoChannel(input);
  }
}
