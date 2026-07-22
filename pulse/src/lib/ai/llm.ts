import OpenAI from 'openai';
import { withRetry, ExternalServiceError, RateLimitError, extractRetryAfter } from '@/lib/errors';

export const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
  maxRetries: 0, // We handle retries ourselves
});

export type CompletionOptions = {
  model?: string;
  temperature?: number;
  maxTokens?: number;
  systemPrompt?: string;
  fallback?: string;
};

const DEMO_LISTING = {
  title: 'Wireless Earbuds Pro - Premium Sound',
  description: 'Experience studio-quality sound with our premium wireless earbuds. Features active noise cancellation, 24-hour battery life, and IPX5 water resistance. Perfect for workouts, commuting, and everyday use.',
  tags: ['audio', 'wireless', 'premium', 'bluetooth'],
  faqs: [
    { question: 'What is the battery life?', answer: 'Up to 24 hours with the charging case.' },
    { question: 'Is it water resistant?', answer: 'Yes, IPX5 rated for sweat and rain.' },
    { question: 'Does it support noise cancellation?', answer: 'Yes, active noise cancellation with transparency mode.' },
  ],
};

function isDemoMode(): boolean {
  return process.env.DEMO_MODE === 'true';
}

export async function generateCompletion(
  prompt: string,
  options: CompletionOptions = {}
): Promise<string> {
  const {
    model = 'gpt-4o-mini',
    temperature = 0.7,
    maxTokens = 1024,
    systemPrompt,
    fallback,
  } = options;

  const messages: OpenAI.Chat.Completions.ChatCompletionMessageParam[] = [];

  if (systemPrompt) {
    messages.push({ role: 'system', content: systemPrompt });
  }

  messages.push({ role: 'user', content: prompt });

  // Return demo data ONLY when explicitly enabled via DEMO_MODE=true
  if (isDemoMode()) {
    return JSON.stringify(DEMO_LISTING);
  }

  // Real OpenAI call - requires OPENAI_API_KEY
  if (!process.env.OPENAI_API_KEY) {
    throw new Error('Missing OPENAI_API_KEY. Please set it in .env to use real AI generation.');
  }

  try {
    const response = await withRetry(
      () =>
        openai.chat.completions.create({
          model,
          messages,
          temperature,
          max_tokens: maxTokens,
        }),
      {
        maxRetries: 3,
        baseDelayMs: 1000,
        maxDelayMs: 30000,
        backoffFactor: 2,
      }
    );

    return response.choices[0]?.message?.content ?? fallback ?? '';
  } catch (error) {
    if (fallback) {
      return fallback;
    }

    const retryAfter = extractRetryAfter(error);
    if (retryAfter) {
      throw new RateLimitError('openai', retryAfter);
    }

    throw new ExternalServiceError(
      'openai',
      error instanceof Error && 'statusCode' in error ? (error as any).statusCode : 500,
      error instanceof Error ? error.message : 'OpenAI completion failed',
      false,
    );
  }
}

export async function generateStructuredCompletion<T>(
  prompt: string,
  schema: {
    parse: (text: string) => T;
    fallback: T;
  },
  options: CompletionOptions = {}
): Promise<{ data: T; raw: string }> {
  const raw = await generateCompletion(prompt, options);
  
  try {
    const data = schema.parse(raw);
    return { data, raw };
  } catch {
    return { data: schema.fallback, raw };
  }
}
