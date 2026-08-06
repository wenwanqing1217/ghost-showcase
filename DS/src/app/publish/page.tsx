'use client';

import TopBar from '@/components/layout/TopBar';
import AuthGuard from '@/components/layout/AuthGuard';
import { useState } from 'react';

type Platform = 'xianyu' | 'xiaohongshu';

interface PublishResult {
  platform: Platform;
  title: string;
  body: string;
  tags: string[];
  checklist: string[];
  mode: 'demo' | 'api';
}

/** 小红书选题变体：3 个种草向标题（人工可改） */
function xhsTitleVariants(product: string, tone: string): string[] {
  const core = product.trim();
  const casual = `被问爆的${core}！真心推荐给大家`;
  const fun = `救命！这个${core}也太绝了吧 ✨`;
  const pro = `${core}深度测评｜入手前必看`;
  if (tone === 'professional') return [pro, casual, fun];
  if (tone === 'fun') return [fun, casual, pro];
  if (tone === 'luxury') return [`高质感${core}｜提升幸福感的好物`, pro, casual];
  return [casual, fun, pro];
}

/** 闲鱼标题变体：3 个含成色/价格的前缀标题（人工可改） */
function xianyuTitleVariants(product: string, condition: string, price: string, tone: string): string[] {
  const core = product.trim();
  const c = condition || '全新';
  const p = price ? `¥${price}` : '低价出';
  const base = `${c} · ${core} ${p}`;
  const prefix = ['全新', '自用', '清仓'];
  const extra = [c === '全新' ? '支持验货' : '诚心出', '可小刀', '包邮'];
  return [
    base.slice(0, 50),
    `【${prefix[0]}】${core} ${p} ${extra[0]}`.slice(0, 50),
    `${c}${core}，${extra[1]}，${extra[2]}`.slice(0, 50),
  ];
}

/** 小红书配图提示词（复制到任意生图工具 / 小红书自带 AI 配图） */
function xhsImagePrompt(product: string, title: string): string {
  const core = product.trim();
  return `小红书种草笔记封面，3:4 竖图，${core}为主体的高质感产品摄影，柔光，浅色奶油背景，ins 风构图，画面留白，可叠加文字标题：${title}，温暖治愈色调，清晰锐利，商业广告级`;
}

/** 组装平台发布格式（复制到剪贴板的内容） */
function assembleCopy(platform: Platform, title: string, body: string, tags: string[]): string {
  const tagLine = tags.filter(Boolean).map((t) => (t.startsWith('#') ? t : `#${t}`)).join(' ');
  if (platform === 'xiaohongshu') {
    return `${title}\n\n${body}\n\n${tagLine}`;
  }
  return `【标题】${title}\n\n${body}\n\n${tagLine}`;
}

const SCHEMES: Record<Platform, string> = {
  xiaohongshu: 'xhsdiscover://', // 小红书 URL Scheme（手机端生效）
  xianyu: 'fleamarket://', // 闲鱼 URL Scheme（手机端生效）
};

const WEB_HINTS: Record<Platform, { name: string; url: string; tip: string }> = {
  xiaohongshu: {
    name: '小红书创作中心（网页版）',
    url: 'https://creator.xiaohongshu.com/publish/publish?source=official',
    tip: '手机端：已复制内容 → 打开小红书 App → 发笔记 → 长按粘贴，手动确认发布。',
  },
  xianyu: {
    name: '闲鱼 App',
    url: 'https://www.goofish.com/',
    tip: '手机端：已复制内容 → 打开闲鱼 App → 发布闲置 → 长按粘贴，手动确认上架。',
  },
};

export default function PublishPage() {
  // 当前平台 tab
  const [platform, setPlatform] = useState<Platform>('xiaohongshu');

  // 商品表单
  const [product, setProduct] = useState('');
  const [description, setDescription] = useState('');
  const [price, setPrice] = useState('');
  const [condition, setCondition] = useState('全新未拆');
  const [tone, setTone] = useState<'professional' | 'casual' | 'luxury' | 'fun'>('casual');

  // 生成结果（原始）
  const [result, setResult] = useState<PublishResult | null>(null);

  // 可编辑状态
  const [selectedTitle, setSelectedTitle] = useState('');
  const [bodyText, setBodyText] = useState('');
  const [tagsText, setTagsText] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<string | null>(null);

  // 选题变体 + 配图提示词（前端模板生成，人工可改）
  const titleVariants = platform === 'xiaohongshu'
    ? xhsTitleVariants(product || '好物', tone)
    : xianyuTitleVariants(product || '好物', condition, price, tone);

  const imagePrompts = (platform === 'xiaohongshu' && product.trim())
    ? titleVariants.map((t) => xhsImagePrompt(product, t))
    : [];

  const generate = async () => {
    if (!product.trim()) {
      setError('请输入商品名/主题');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch('/api/ai/channel-copy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          platform,
          product: product.trim(),
          description: description || undefined,
          price: platform === 'xianyu' ? price || undefined : undefined,
          condition: platform === 'xianyu' ? condition || undefined : undefined,
          tone,
        }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.error || '生成失败');
      const r = data.result as PublishResult;
      setResult(r);
      setSelectedTitle(r.title);
      setBodyText(r.body);
      setTagsText(r.tags.join(' '));
    } catch (e) {
      setError(e instanceof Error ? e.message : '生成失败');
    } finally {
      setLoading(false);
    }
  };

  const copyText = (text: string, key: string) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(key);
      setTimeout(() => setCopied(null), 1800);
    });
  };

  /** 一键复制 + 唤起 APP（合规模式：只复制+唤起，发布由用户手动确认） */
  const copyAndOpen = () => {
    const title = selectedTitle || titleVariants[0];
    const tags = tagsText.split(/[\s,，#]+/).filter(Boolean);
    const text = assembleCopy(platform, title, bodyText, tags);
    copyText(text, 'all');
    try {
      window.location.href = SCHEMES[platform];
    } catch {
      /* PC 端 scheme 无效，忽略 */
    }
  };

  const tagsArray = tagsText.split(/[\s,，#]+/).filter(Boolean);

  const tabStyle = (p: Platform): React.CSSProperties => ({
    flex: 1,
    padding: '10px 0',
    fontSize: 14,
    fontWeight: 600,
    textAlign: 'center' as const,
    cursor: 'pointer',
    background: platform === p ? (p === 'xianyu' ? 'rgba(255,165,0,0.15)' : 'rgba(255,80,80,0.15)') : 'transparent',
    color: platform === p ? (p === 'xianyu' ? '#fbbf24' : '#fb7185') : 'var(--text-secondary)',
    borderBottom: platform === p ? `2px solid ${p === 'xianyu' ? '#fbbf24' : '#fb7185'}` : '2px solid transparent',
  });

  const meta = platform === 'xianyu'
    ? { emoji: '🐟', name: '闲鱼上架', color: 'rgba(255,165,0,0.12)' }
    : { emoji: '📕', name: '小红书种草', color: 'rgba(255,80,80,0.12)' };

  return (
    <AuthGuard>
      <div className="page-container">
        <TopBar title="发布台 · 合规上架" />

        <div style={{ padding: '20px 24px', maxWidth: 1100, margin: '0 auto' }}>
          {/* 合规说明条 */}
          <div
            style={{
              background: 'linear-gradient(135deg, rgba(34,197,94,0.08), rgba(56,189,248,0.05))',
              border: '1px solid rgba(34,197,94,0.2)',
              borderRadius: 12,
              padding: 14,
              marginBottom: 20,
              fontSize: 13,
              color: 'var(--text-secondary)',
              lineHeight: 1.7,
            }}
          >
            ✅ <strong style={{ color: '#4ade80' }}>合规模式：</strong>
            AI 生成选题/文案/配图提示词 → 你在这里<b>修改审核</b> → 「一键复制」自动填好内容 →
            拉起 APP 后<b>手动粘贴确认发布</b>。工具只辅助不代发，全程人工把关。
          </div>

          {/* 平台 tab */}
          <div
            style={{
              display: 'flex',
              background: 'rgba(255,255,255,0.02)',
              border: '1px solid var(--border-color)',
              borderRadius: 12,
              overflow: 'hidden',
              marginBottom: 16,
            }}
          >
            <div style={tabStyle('xiaohongshu')}>📕 小红书种草</div>
            <div style={tabStyle('xianyu')}>🐟 闲鱼上架</div>
          </div>

          {/* 商品表单 */}
          <div
            style={{
              background: 'rgba(255,255,255,0.02)',
              border: '1px solid var(--border-color)',
              borderRadius: 12,
              padding: 18,
              marginBottom: 20,
            }}
          >
            <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 14, color: 'var(--text-primary)' }}>
              {meta.emoji} {meta.name} — 商品信息
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
              <div>
                <label style={labelStyle}>商品名/主题 *</label>
                <input
                  style={inputStyle}
                  value={product}
                  onChange={(e) => setProduct(e.target.value)}
                  placeholder="如：北欧风香薰蜡烛 / 韩系针织围巾"
                />
              </div>
              <div>
                <label style={labelStyle}>卖点描述</label>
                <input
                  style={inputStyle}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="如：大豆蜡、留香 8 小时、礼盒装"
                />
              </div>
              {platform === 'xianyu' && (
                <>
                  <div>
                    <label style={labelStyle}>价格</label>
                    <input
                      style={inputStyle}
                      value={price}
                      onChange={(e) => setPrice(e.target.value)}
                      placeholder="如：59"
                    />
                  </div>
                  <div>
                    <label style={labelStyle}>成色</label>
                    <input
                      style={inputStyle}
                      value={condition}
                      onChange={(e) => setCondition(e.target.value)}
                      placeholder="如：全新未拆 / 95新"
                    />
                  </div>
                </>
              )}
            </div>

            <div style={{ marginBottom: 14 }}>
              <label style={labelStyle}>语气风格</label>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {(['casual', 'fun', 'professional', 'luxury'] as const).map((t) => (
                  <button
                    key={t}
                    onClick={() => setTone(t)}
                    style={{
                      padding: '6px 14px',
                      fontSize: 12,
                      borderRadius: 16,
                      cursor: 'pointer',
                      background: tone === t ? 'rgba(139,92,246,0.2)' : 'rgba(255,255,255,0.03)',
                      color: tone === t ? 'var(--nebula-light)' : 'var(--text-secondary)',
                      border: tone === t ? '1px solid rgba(139,92,246,0.4)' : '1px solid var(--border-color)',
                    }}
                  >
                    {t === 'casual' ? '亲切' : t === 'fun' ? '活泼' : t === 'professional' ? '专业' : '高端'}
                  </button>
                ))}
              </div>
            </div>

            {error && <div style={{ color: '#f87171', fontSize: 12, marginBottom: 10 }}>⚠️ {error}</div>}

            <button
              onClick={generate}
              disabled={loading}
              style={{
                padding: '10px 20px',
                fontSize: 13,
                fontWeight: 600,
                background: 'linear-gradient(135deg, rgba(139,92,246,0.3), rgba(56,189,248,0.2))',
                color: 'white',
                border: '1px solid rgba(139,92,246,0.4)',
                borderRadius: 8,
                cursor: loading ? 'wait' : 'pointer',
                opacity: loading ? 0.6 : 1,
              }}
            >
              {loading ? '⏳ 生成中...' : '✨ AI 生成文案'}
            </button>
          </div>

          {/* 结果区 */}
          {(result || product.trim()) && (
            <div
              style={{
                background: 'rgba(255,255,255,0.02)',
                border: '1px solid var(--border-color)',
                borderRadius: 12,
                padding: 18,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
                <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                  {meta.emoji} {meta.name} — 审核编辑区
                </div>
                {result && (
                  <span
                    style={{
                      fontSize: 10,
                      padding: '2px 6px',
                      borderRadius: 4,
                      background: result.mode === 'api' ? 'rgba(34,197,94,0.15)' : 'rgba(148,163,184,0.15)',
                      color: result.mode === 'api' ? '#4ade80' : '#94a3b8',
                    }}
                  >
                    {result.mode === 'api' ? 'AI' : '模板'}
                  </span>
                )}
              </div>

              {/* 标题选择（选题变体） */}
              <div style={{ marginBottom: 14 }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>
                  {platform === 'xiaohongshu' ? '📝 选题标题（点选使用，可直接改）' : '📝 标题（点选使用，可直接改）'}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {titleVariants.map((t, i) => (
                    <button
                      key={i}
                      onClick={() => setSelectedTitle(t)}
                      style={{
                        textAlign: 'left',
                        padding: '8px 12px',
                        fontSize: 13,
                        borderRadius: 8,
                        cursor: 'pointer',
                        background: selectedTitle === t ? meta.color : 'rgba(0,0,0,0.2)',
                        color: selectedTitle === t ? 'var(--text-primary)' : 'var(--text-secondary)',
                        border: selectedTitle === t ? '1px solid var(--border-color)' : '1px solid var(--border-color)',
                      }}
                    >
                      {selectedTitle === t ? '● ' : '○ '}
                      {t}
                    </button>
                  ))}
                </div>
              </div>

              {/* 配图提示词（小红书） */}
              {platform === 'xiaohongshu' && imagePrompts.length > 0 && (
                <div style={{ marginBottom: 14 }}>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>
                    🎨 配图提示词（复制到生图工具 / 小红书自带 AI 配图）
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {imagePrompts.map((p, i) => (
                      <div
                        key={i}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 8,
                          background: 'rgba(0,0,0,0.2)',
                          padding: '8px 12px',
                          borderRadius: 8,
                          fontSize: 12,
                          color: 'var(--text-secondary)',
                        }}
                      >
                        <span style={{ flex: 1, lineHeight: 1.6 }}>{p}</span>
                        <button
                          onClick={() => copyText(p, `img-${i}`)}
                          style={{
                            flexShrink: 0,
                            fontSize: 10,
                            padding: '4px 8px',
                            background: 'rgba(255,255,255,0.05)',
                            border: '1px solid var(--border-color)',
                            borderRadius: 4,
                            color: 'var(--text-secondary)',
                            cursor: 'pointer',
                          }}
                        >
                          {copied === `img-${i}` ? '✓ 已复制' : '复制'}
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 正文编辑 */}
              <div style={{ marginBottom: 14 }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>📄 正文（可直接修改）</div>
                <textarea
                  style={{ ...inputStyle, minHeight: 180, lineHeight: 1.7, resize: 'vertical', fontFamily: 'inherit' }}
                  value={bodyText}
                  onChange={(e) => setBodyText(e.target.value)}
                  placeholder="AI 生成的正文，可在此修改审核..."
                />
              </div>

              {/* 标签编辑 */}
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>
                  🏷️ 话题标签（空格或逗号分隔）
                </div>
                <input
                  style={inputStyle}
                  value={tagsText}
                  onChange={(e) => setTagsText(e.target.value)}
                  placeholder="好物分享 种草 平价"
                />
              </div>

              {/* 操作按钮：合规发布（只复制+唤起，手动发布） */}
              <div
                style={{
                  display: 'flex',
                  gap: 10,
                  flexWrap: 'wrap',
                  alignItems: 'center',
                  borderTop: '1px solid var(--border-color)',
                  paddingTop: 14,
                }}
              >
                <button
                  onClick={copyAndOpen}
                  disabled={!product.trim()}
                  style={{
                    padding: '10px 20px',
                    fontSize: 13,
                    fontWeight: 600,
                    background: 'linear-gradient(135deg, rgba(34,197,94,0.25), rgba(56,189,248,0.2))',
                    color: 'white',
                    border: '1px solid rgba(34,197,94,0.4)',
                    borderRadius: 8,
                    cursor: product.trim() ? 'pointer' : 'not-allowed',
                    opacity: product.trim() ? 1 : 0.5,
                  }}
                >
                  {copied === 'all' ? '✓ 已复制，请到 APP 粘贴' : '🚀 一键复制并打开 APP'}
                </button>
                <button
                  onClick={() => copyText(assembleCopy(platform, selectedTitle || titleVariants[0], bodyText, tagsArray), 'all')}
                  disabled={!product.trim()}
                  style={{
                    padding: '10px 16px',
                    fontSize: 12,
                    background: 'rgba(255,255,255,0.05)',
                    color: 'var(--text-secondary)',
                    border: '1px solid var(--border-color)',
                    borderRadius: 8,
                    cursor: product.trim() ? 'pointer' : 'not-allowed',
                    opacity: product.trim() ? 1 : 0.5,
                  }}
                >
                  仅复制
                </button>
                <a
                  href={WEB_HINTS[platform].url}
                  target="_blank"
                  rel="noreferrer"
                  style={{
                    padding: '10px 16px',
                    fontSize: 12,
                    background: 'rgba(255,255,255,0.03)',
                    color: 'var(--nebula-light)',
                    border: '1px solid rgba(139,92,246,0.25)',
                    borderRadius: 8,
                    textDecoration: 'none',
                  }}
                >
                  打开{WEB_HINTS[platform].name} ↗
                </a>
              </div>

              <div
                style={{
                  marginTop: 12,
                  fontSize: 12,
                  color: 'var(--text-secondary)',
                  background: 'rgba(34,197,94,0.06)',
                  border: '1px solid rgba(34,197,94,0.15)',
                  borderRadius: 8,
                  padding: 10,
                  lineHeight: 1.7,
                }}
              >
                📌 {WEB_HINTS[platform].tip}
                {' '}发布前请人工核对：商品信息真实、价格合理、图片无版权风险。
              </div>

              {/* 发布清单 */}
              {result && result.checklist.length > 0 && (
                <div style={{ marginTop: 14 }}>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>📋 发布提醒</div>
                  <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.9 }}>
                    {result.checklist.map((c, i) => (
                      <li key={i}>{c}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </AuthGuard>
  );
}

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: 11,
  color: 'var(--text-muted)',
  marginBottom: 4,
};

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '8px 12px',
  fontSize: 13,
  background: 'rgba(0,0,0,0.2)',
  border: '1px solid var(--border-color)',
  borderRadius: 8,
  color: 'var(--text-primary)',
  outline: 'none',
};
