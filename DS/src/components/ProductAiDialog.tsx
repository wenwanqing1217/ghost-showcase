'use client';

import { useState } from 'react';

/**
 * 简单 HTML 白名单消毒器 — 只允许安全标签，移除所有属性/事件 handler
 * ⚠️ 生产环境建议使用 DOMPurify (npm i dompurify)
 */
function sanitizeHtml(html: string): string {
  // 只允许这些标签（无属性）
  const allowedTags = new Set(['p', 'strong', 'em', 'br', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div']);
  // 匹配所有 HTML 标签
  return html.replace(/<\/?([a-zA-Z][a-zA-Z0-9]*)[^>]*>/g, (match, tag) => {
    if (allowedTags.has(tag.toLowerCase())) {
      // 只保留标签名，丢弃所有属性
      return match.startsWith('</') ? `</${tag.toLowerCase()}>` : `<${tag.toLowerCase()}>`;
    }
    // 不允许的标签直接移除
    return '';
  });
}

interface Product {
  id: string;
  title: string;
  description: string | null;
  price: number;
  images: string;
}

interface AiResult {
  title: string;
  description: string;
  keywords: string[];
  usage: { prompt_tokens: number; completion_tokens: number };
}

const TONE_OPTIONS = [
  { value: 'professional', label: '专业可信' },
  { value: 'casual', label: '亲切自然' },
  { value: 'luxury', label: '高端奢华' },
  { value: 'fun', label: '活泼有趣' },
];

export default function ProductAiDialog({
  product,
  onClose,
  onSaved,
}: {
  product: Product;
  onClose: () => void;
  onSaved: (title: string, description: string) => void;
}) {
  const [tone, setTone] = useState('professional');
  const [lang, setLang] = useState<'zh' | 'en'>('zh');
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<AiResult | null>(null);
  const [mode, setMode] = useState<'demo' | 'api'>('demo');
  const [error, setError] = useState<string | null>(null);

  const parseImages = (images: string): string[] => {
    try { return JSON.parse(images); } catch { return []; }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch('/api/ai/copy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          productId: product.id,
          title: product.title,
          description: product.description,
          tone,
          lang,
        }),
      });

      const data = await res.json();
      if (data.ok) {
        setResult(data.result);
        setMode(data.mode || 'demo');
      } else {
        setError(data.error || '生成失败');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '网络错误');
    } finally {
      setGenerating(false);
    }
  };

  const handleSave = async () => {
    if (!result) return;
    setGenerating(true);

    try {
      const res = await fetch('/api/ai/copy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          productId: product.id,
          title: result.title,
          description: product.description,
          tone,
          lang,
          save: true,
        }),
      });

      const data = await res.json();
      if (data.ok) {
        onSaved(result.title, result.description);
        onClose();
      } else {
        setError(data.error || '保存失败');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '网络错误');
    } finally {
      setGenerating(false);
    }
  };

  const imgs = parseImages(product.images);

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.7)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 100,
      }}
      onClick={onClose}
    >
      <div
        className="card"
        style={{ width: '100%', maxWidth: 600, maxHeight: '80vh', overflow: 'auto' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* 头部 */}
        <div className="flex-between" style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600 }}>AI 优化文案</h3>
            {mode === 'demo' && (
              <span className="badge" style={{ background: 'rgba(253,203,110,0.15)', color: 'var(--warning)', fontSize: 10 }}>
                Demo 模式
              </span>
            )}
            {mode === 'api' && (
              <span className="badge" style={{ background: 'rgba(0,184,148,0.15)', color: 'var(--success)', fontSize: 10 }}>
                API 模式
              </span>
            )}
          </div>
          <button className="btn btn-sm" onClick={onClose}>✕</button>
        </div>

        {/* 原始信息 */}
        <div style={{ marginBottom: 16 }}>
          <div className="flex gap-3" style={{ alignItems: 'flex-start' }}>
            {imgs[0] && (
              <img
                src={imgs[0]}
                alt={product.title}
                style={{ width: 60, height: 60, objectFit: 'cover', borderRadius: 6 }}
              />
            )}
            <div>
              <div style={{ fontWeight: 500, marginBottom: 4 }}>{product.title}</div>
              <div className="text-muted text-sm">${product.price.toFixed(2)}</div>
            </div>
          </div>
        </div>

        {/* 选项 */}
        <div className="flex gap-3" style={{ marginBottom: 16 }}>
          <div style={{ flex: 1 }}>
            <label className="form-label">文案风格</label>
            <select
              className="input"
              value={tone}
              onChange={(e) => setTone(e.target.value)}
            >
              {TONE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div style={{ flex: 1 }}>
            <label className="form-label">语言</label>
            <select
              className="input"
              value={lang}
              onChange={(e) => setLang(e.target.value as 'zh' | 'en')}
            >
              <option value="zh">中文</option>
              <option value="en">English</option>
            </select>
          </div>
        </div>

        {/* 生成按钮 */}
        <button
          className="btn btn-primary"
          style={{ width: '100%', marginBottom: 8 }}
          onClick={handleGenerate}
          disabled={generating}
        >
          {generating ? '⏳ 生成中...' : '✨ 生成 AI 文案'}
        </button>
        <p className="text-muted text-sm mb-3" style={{ fontSize: 11 }}>
          {mode === 'demo'
            ? '当前为 Demo 模式（本地模板生成，免费）。设置 AI_API_KEY 可启用 Groq 免费额度或 DeepSeek。'
            : '当前为 API 模式（外部 LLM 生成）。'}
        </p>

        {/* 错误 */}
        {error && (
          <div style={{
            padding: '8px 12px',
            background: 'rgba(255,107,107,0.1)',
            color: 'var(--danger)',
            borderRadius: 6,
            fontSize: 13,
            marginBottom: 16,
          }}>
            {error}
          </div>
        )}

        {/* 结果 */}
        {result && (
          <div>
            <div className="form-label">优化后标题</div>
            <div className="input" style={{ marginBottom: 12, background: 'var(--bg-secondary)' }}>
              {result.title}
            </div>

            <div className="form-label">优化后描述</div>
            <div
              className="input-textarea"
              style={{ background: 'var(--bg-secondary)', marginBottom: 12 }}
              dangerouslySetInnerHTML={{ __html: sanitizeHtml(result.description) }}
            />

            {result.keywords.length > 0 && (
              <div className="mb-3">
                <div className="form-label">推荐关键词</div>
                <div className="flex gap-2" style={{ flexWrap: 'wrap' }}>
                  {result.keywords.map((kw, i) => (
                    <span key={i} className="badge" style={{ background: 'rgba(108,92,231,0.15)', color: 'var(--accent)' }}>
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="flex-between">
              <span className="text-muted text-sm">
                Token: {result.usage.prompt_tokens} + {result.usage.completion_tokens}
              </span>
              <button
                className="btn btn-primary btn-sm"
                onClick={handleSave}
                disabled={generating}
              >
                💾 保存并上架
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
