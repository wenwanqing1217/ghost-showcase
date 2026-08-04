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
