'use client';

import TopBar from '@/components/layout/TopBar';
import AuthGuard from '@/components/layout/AuthGuard';
import { useState } from 'react';

type Platform = 'xianyu' | 'xiaohongshu';

interface ChannelResult {
  platform: Platform;
  title: string;
  body: string;
  tags: string[];
  checklist: string[];
  mode: 'demo' | 'api';
}

export default function ChannelsPage() {
  // 表单
  const [product, setProduct] = useState('');
  const [description, setDescription] = useState('');
  const [price, setPrice] = useState('');
  const [condition, setCondition] = useState('全新未拆');
  const [tone, setTone] = useState<'professional' | 'casual' | 'luxury' | 'fun'>('casual');

  // 结果
  const [results, setResults] = useState<Record<Platform, ChannelResult | null>>({
    xianyu: null,
    xiaohongshu: null,
  });
  const [loading, setLoading] = useState<Platform | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 视频生成
  const [videoGenerating, setVideoGenerating] = useState(false);
  const [videoMsg, setVideoMsg] = useState<string | null>(null);

  // 复制反馈
  const [copied, setCopied] = useState<string | null>(null);

  const generateOne = async (platform: Platform) => {
    if (!product.trim()) {
      setError('请输入商品名/主题');
      return;
    }
    setLoading(platform);
    setError(null);
    try {
      const resp = await fetch('/api/ai/channel-copy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          platform,
          product: product.trim(),
          description: description || undefined,
          price: price || undefined,
          condition: condition || undefined,
          tone,
        }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.error || '生成失败');
      setResults((prev) => ({ ...prev, [platform]: data.result }));
    } catch (e) {
      setError(e instanceof Error ? e.message : '生成失败');
    } finally {
      setLoading(null);
    }
  };

  const generateAll = async () => {
    await Promise.all([generateOne('xianyu'), generateOne('xiaohongshu')]);
  };

  // 生成种草视频（复用 /api/content/generate）
  const generateVideo = async () => {
    if (!product.trim()) {
      setError('请输入商品名/主题');
      return;
    }
    setVideoGenerating(true);
    setVideoMsg(null);
    setError(null);
    try {
      const resp = await fetch('/api/content/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'video',
          video_subject: product.trim(),
          video_aspect: '9:16', // 竖屏，适合小红书/抖音
          video_language: 'zh',
          video_concat_mode: 'random',
          paragraph_number: 2,
          n_threads: 2,
        }),
      });
      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.error || data.details?.map((d: any) => d.message).join(', ') || '生成请求失败');
      }
      const taskId = data.task_id || data.taskId;
      setVideoMsg(`✅ 已提交生成（任务 ID: ${taskId}）。前往「内容库」查看进度，完成后可发布到 TikTok/YouTube。`);
    } catch (e) {
      setVideoMsg(`❌ ${e instanceof Error ? e.message : '生成失败'}`);
    } finally {
      setVideoGenerating(false);
    }
  };

  const copyText = (text: string, key: string) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(key);
      setTimeout(() => setCopied(null), 1500);
    });
  };

  const platformLabel: Record<Platform, { name: string; emoji: string; color: string }> = {
    xianyu: { name: '闲鱼', emoji: '🐟', color: 'rgba(255,165,0,0.15)' },
    xiaohongshu: { name: '小红书', emoji: '📕', color: 'rgba(255,80,80,0.15)' },
  };

  const renderResult = (platform: Platform) => {
    const r = results[platform];
    const meta = platformLabel[platform];
    if (!r) return null;
    return (
      <div
        style={{
          background: 'rgba(255,255,255,0.02)',
          border: '1px solid var(--border-color)',
          borderRadius: 12,
          padding: 18,
        }}
      >
        {/* 头部 */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 20 }}>{meta.emoji}</span>
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{meta.name}文案</span>
            <span
              style={{
                fontSize: 10,
                padding: '2px 6px',
                borderRadius: 4,
                background: r.mode === 'api' ? 'rgba(34,197,94,0.15)' : 'rgba(148,163,184,0.15)',
                color: r.mode === 'api' ? '#4ade80' : '#94a3b8',
              }}
            >
              {r.mode === 'api' ? 'AI' : '模板'}
            </span>
          </div>
          <button
            onClick={() => copyText(`${r.title}\n\n${r.body}\n\n${r.tags.join(' ')}`, `${platform}-all`)}
            style={{
              padding: '4px 10px',
              fontSize: 11,
              background: 'rgba(139,92,246,0.1)',
              color: 'var(--nebula-light)',
              border: '1px solid rgba(139,92,246,0.2)',
              borderRadius: 6,
              cursor: 'pointer',
            }}
          >
            {copied === `${platform}-all` ? '✓ 已复制' : '复制全部'}
          </button>
        </div>

        {/* 标题 */}
        <div style={{ marginBottom: 10 }}>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>标题</div>
          <div
            style={{
              background: meta.color,
              padding: '8px 12px',
              borderRadius: 8,
              fontSize: 14,
              fontWeight: 500,
              color: 'var(--text-primary)',
            }}
          >
            {r.title}
            <button
              onClick={() => copyText(r.title, `${platform}-title`)}
              style={{
                marginLeft: 8,
                fontSize: 10,
                padding: '2px 6px',
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid var(--border-color)',
                borderRadius: 4,
                color: 'var(--text-secondary)',
                cursor: 'pointer',
              }}
            >
              {copied === `${platform}-title` ? '✓' : '复制'}
            </button>
          </div>
        </div>

        {/* 正文 */}
        <div style={{ marginBottom: 10 }}>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>正文</div>
          <pre
            style={{
              background: 'rgba(0,0,0,0.2)',
              padding: 12,
              borderRadius: 8,
              fontSize: 13,
              lineHeight: 1.6,
              color: 'var(--text-primary)',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              margin: 0,
              fontFamily: 'inherit',
            }}
          >
            {r.body}
          </pre>
          <button
            onClick={() => copyText(r.body, `${platform}-body`)}
            style={{
              marginTop: 6,
              fontSize: 10,
              padding: '2px 6px',
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid var(--border-color)',
              borderRadius: 4,
              color: 'var(--text-secondary)',
              cursor: 'pointer',
            }}
          >
            {copied === `${platform}-body` ? '✓ 已复制正文' : '复制正文'}
          </button>
        </div>

        {/* 标签 */}
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>话题标签</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {r.tags.map((t, i) => (
              <span
                key={i}
                style={{
                  fontSize: 11,
                  padding: '2px 8px',
                  background: 'rgba(56,189,248,0.1)',
                  color: '#7dd3fc',
                  borderRadius: 10,
                  border: '1px solid rgba(56,189,248,0.15)',
                }}
              >
                {t}
              </span>
            ))}
          </div>
        </div>

        {/* 发布清单 */}
        <div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>📋 发布清单</div>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.8 }}>
            {r.checklist.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </div>
      </div>
    );
  };

  return (
    <AuthGuard>
      <div className="page-container">
        <TopBar title="渠道助手 · 低成本出海变现" />

        <div style={{ padding: '20px 24px', maxWidth: 1100, margin: '0 auto' }}>
          {/* 说明条 */}
          <div
            style={{
              background: 'linear-gradient(135deg, rgba(139,92,246,0.08), rgba(56,189,248,0.05))',
              border: '1px solid rgba(139,92,246,0.2)',
              borderRadius: 12,
              padding: 14,
              marginBottom: 20,
              fontSize: 13,
              color: 'var(--text-secondary)',
              lineHeight: 1.6,
            }}
          >
            💡 <strong style={{ color: 'var(--nebula-light)' }}>闭环：</strong>
            填商品 → 一键生成闲鱼挂单文案 + 小红书种草笔记 → 生成种草视频 → 小红书引流到闲鱼成交（国内）/ 视频发布到 TikTok 出海。
            <strong style={{ color: 'var(--nebula-light)' }}> 无需开店、无需 API、零成本启动</strong>。
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
              📦 商品信息
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
              <div>
                <label style={labelStyle}>价格（闲鱼用）</label>
                <input
                  style={inputStyle}
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  placeholder="如：59"
                />
              </div>
              <div>
                <label style={labelStyle}>成色（闲鱼用）</label>
                <input
                  style={inputStyle}
                  value={condition}
                  onChange={(e) => setCondition(e.target.value)}
                  placeholder="如：全新未拆 / 95新"
                />
              </div>
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

            {error && (
              <div style={{ color: '#f87171', fontSize: 12, marginBottom: 10 }}>⚠️ {error}</div>
            )}

            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              <button
                onClick={generateAll}
                disabled={loading !== null}
                style={{
                  padding: '10px 20px',
                  fontSize: 13,
                  fontWeight: 600,
                  background: 'linear-gradient(135deg, rgba(139,92,246,0.3), rgba(56,189,248,0.2))',
                  color: 'white',
                  border: '1px solid rgba(139,92,246,0.4)',
                  borderRadius: 8,
                  cursor: loading !== null ? 'wait' : 'pointer',
                  opacity: loading !== null ? 0.6 : 1,
                }}
              >
                {loading ? '⏳ 生成中...' : '✨ 一键生成两套文案'}
              </button>
              <button
                onClick={generateVideo}
                disabled={videoGenerating}
                style={{
                  padding: '10px 20px',
                  fontSize: 13,
                  fontWeight: 600,
                  background: 'rgba(255,255,255,0.05)',
                  color: 'var(--nebula-light)',
                  border: '1px solid rgba(139,92,246,0.25)',
                  borderRadius: 8,
                  cursor: videoGenerating ? 'wait' : 'pointer',
                  opacity: videoGenerating ? 0.6 : 1,
                }}
              >
                {videoGenerating ? '⏳ 提交中...' : '🎬 生成种草视频（竖屏）'}
              </button>
            </div>

            {videoMsg && (
              <div style={{ marginTop: 10, fontSize: 12, color: 'var(--text-secondary)' }}>{videoMsg}</div>
            )}
          </div>

          {/* 结果展示 */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            {renderResult('xianyu')}
            {renderResult('xiaohongshu')}
          </div>

          {/* 操作流程提示 */}
          <div
            style={{
              marginTop: 24,
              background: 'rgba(255,255,255,0.02)',
              border: '1px solid var(--border-color)',
              borderRadius: 12,
              padding: 16,
              fontSize: 12,
              color: 'var(--text-secondary)',
              lineHeight: 1.8,
            }}
          >
            <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>🚀 操作流程</div>
            <div>1. 填商品信息 → 点「一键生成两套文案」</div>
            <div>2. 复制闲鱼文案 → 闲鱼 App 挂商品（拍 3-9 张实拍图）</div>
            <div>3. 复制小红书文案 → 小红书 App 发种草笔记（首图加大字标题）</div>
            <div>4. 点「生成种草视频」→ 去「内容库」查看 → 发布到 TikTok/YouTube 出海</div>
            <div>5. 小红书引流 → 闲鱼成交 → 视频号引流 → TikTok 出海（多渠道并行）</div>
          </div>
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
