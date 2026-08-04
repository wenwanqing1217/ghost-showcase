'use client';

import { useEffect, useState } from 'react';
import TopBar from '@/components/layout/TopBar';
import AuthGuard from '@/components/layout/AuthGuard';
import { getApiUrl } from '@/lib/gateway-client';

interface ShopInfo {
  id: string;
  name: string;
  domain: string;
  platform: string;
  storeMode: string;
  settings: Record<string, unknown>;
}

interface GatewayStatus {
  ok: boolean;
}

type StoreMode = 'marketplace' | 'independent' | 'both';

const STORE_MODE_OPTIONS: { value: StoreMode; label: string; desc: string }[] = [
  { value: 'marketplace', label: '集市店铺', desc: '依托平台流量，标准化商品展示' },
  { value: 'independent', label: '独立站', desc: '自定义域名、自主装修、品牌露出' },
  { value: 'both', label: '双模运营', desc: '同一货源同时运营集市 + 独立站' },
];

export default function SettingsPage() {
  const [shop, setShop] = useState<ShopInfo | null>(null);
  const [apiKey, setApiKey] = useState('');
  const [name, setName] = useState('');
  const [storeMode, setStoreMode] = useState<StoreMode>('marketplace');
  const [saving, setSaving] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; message: string } | null>(null);
  const [gwStatus, setGwStatus] = useState<GatewayStatus | null>(null);
  const [aiAvailable, setAiAvailable] = useState(false);

  useEffect(() => {
    fetch(getApiUrl('/api/shop'))
      .then((r) => r.json())
      .then((data) => {
        if (data.shop) {
          setShop(data.shop);
          setName(data.shop.name);
          setStoreMode(data.shop.storeMode as StoreMode || 'marketplace');
        }
      })
      .catch((err) => console.error('[SettingsPage] shop fetch error:', err));

    // Gateway 状态
    fetch(getApiUrl('/api/health'))
      .then((r) => setGwStatus({ ok: r.ok }))
      .catch((err) => { console.error('[SettingsPage] health fetch error:', err); setGwStatus({ ok: false }); });

    // AI 状态
    fetch(getApiUrl('/api/ai/status'))
      .then((r) => r.json())
      .then((d) => setAiAvailable(d.available))
      .catch((err) => { console.error('[SettingsPage] ai status error:', err); setAiAvailable(false); });
  }, []);

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setResult(null);

    try {
      const res = await fetch(getApiUrl('/api/shop'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ apiKey, name, storeMode }),
      });
      const data = await res.json();

      if (data.ok) {
        setResult({ ok: true, message: `连接成功！货源: ${data.shop.name}` });
        setShop(data.shop);
        setApiKey('');
      } else {
        setResult({ ok: false, message: data.error || '连接失败' });
      }
    } catch (err) {
      setResult({ ok: false, message: `请求错误: ${err instanceof Error ? err.message : '未知错误'}` });
    } finally {
      setSaving(false);
    }
  };

  const handleModeChange = async (mode: StoreMode) => {
    setStoreMode(mode);
    try {
      const res = await fetch('/api/shop/mode', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ storeMode: mode }),
      });
      const data = await res.json();
      if (data.ok) {
        setResult({ ok: true, message: `店铺模式已切换为: ${STORE_MODE_OPTIONS.find(o => o.value === mode)?.label}` });
        setShop(data.shop);
      } else {
        setResult({ ok: false, message: data.error || '切换失败' });
      }
    } catch {
      setResult({ ok: false, message: '请求错误' });
    }
    setTimeout(() => setResult(null), 3000);
  };

  const handleDisconnect = async () => {
    try {
      await fetch(getApiUrl('/api/shop'), { method: 'DELETE' });
      setShop(null);
      setApiKey('');
      setName('');
      setStoreMode('marketplace');
      setResult({ ok: true, message: '已断开连接' });
    } catch {
      setResult({ ok: false, message: '断开失败' });
    }
    setTimeout(() => setResult(null), 3000);
  };

  return (
    <AuthGuard>
      <TopBar title="设置" subtitle="店铺连接 · 运营模式 · 系统状态" />

      <div className="p-6">
        <div className="max-w-3xl mx-auto space-y-4">

          {/* 系统状态卡片 */}
          <div className="card" style={{ padding: 20 }}>
            <div className="card-header" style={{ marginBottom: 16 }}>
              <span className="card-title">系统状态</span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: 'Gateway', ok: gwStatus?.ok, online: '正常', offline: '异常' },
                { label: 'AI 服务', ok: aiAvailable, online: '可用', offline: '不可用' },
                { label: '店铺', ok: !!shop, online: '已连接', offline: '未连接' },
                { label: '运营模式', ok: !!shop, online: shop?.storeMode || '—', offline: '—' },
              ].map((item, i) => (
                <div key={i} className="text-center" style={{ padding: 12, background: 'var(--bg-hover)', borderRadius: 8 }}>
                  <div style={{
                    width: 8, height: 8,
                    borderRadius: '50%',
                    background: item.ok ? 'var(--success)' : 'var(--danger)',
                    margin: '0 auto 8px',
                    opacity: item.ok ? 0.8 : 0.5,
                  }} />
                  <div className="text-xs" style={{ color: 'var(--text-muted)' }}>{item.label}</div>
                  <div className="text-sm font-medium" style={{ color: item.ok ? 'var(--success)' : 'var(--danger)' }}>
                    {item.ok ? item.online : item.offline}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 店铺连接 */}
          <div className="card" style={{ padding: 20 }}>
            <div className="card-header" style={{ marginBottom: 16 }}>
              <span className="card-title">{shop ? '货源连接' : '连接 OneBound 货源'}</span>
            </div>

            {shop && (
              <div style={{
                padding: 14,
                background: 'rgba(16,185,129,0.06)',
                border: '1px solid rgba(16,185,129,0.12)',
                borderRadius: 8,
                marginBottom: 16,
              }}>
                <div className="flex-between">
                  <div>
                    <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{shop.name}</div>
                    <div className="text-sm" style={{ color: 'var(--text-muted)' }}>{shop.domain} · {shop.platform}</div>
                  </div>
                  <span className="badge badge-active">货源已连接</span>
                </div>

                {/* 运营模式切换 */}
                <div style={{ marginTop: 16 }}>
                  <div className="text-sm" style={{ color: 'var(--text-muted)', marginBottom: 8 }}>运营模式</div>
                  <div className="flex gap-2" style={{ flexWrap: 'wrap' }}>
                    {STORE_MODE_OPTIONS.map((opt) => (
                      <button
                        key={opt.value}
                        className={`btn btn-sm${storeMode === opt.value ? ' btn-primary' : ''}`}
                        onClick={() => handleModeChange(opt.value)}
                        title={opt.desc}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                  <div className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>
                    {STORE_MODE_OPTIONS.find(o => o.value === storeMode)?.desc}
                  </div>
                </div>

                <button
                  onClick={handleDisconnect}
                  className="btn btn-sm"
                  style={{ marginTop: 12, color: 'var(--danger)' }}
                >
                  断开连接
                </button>
              </div>
            )}

            <form onSubmit={handleConnect}>
              <div className="form-group">
                <label className="form-label">OneBound API Key</label>
                <input
                  className="input"
                  type="password"
                  placeholder="输入你的 OneBound API Key"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  required
                />
                <p className="text-muted text-sm mt-3">在 OneBound 控制台获取 API Key</p>
              </div>

              <div className="form-group">
                <label className="form-label">货源名称（可选）</label>
                <input
                  className="input"
                  placeholder="用于在看板中显示"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">运营模式</label>
                <div className="flex gap-2" style={{ flexWrap: 'wrap' }}>
                  {STORE_MODE_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      className={`btn btn-sm${storeMode === opt.value ? ' btn-primary' : ''}`}
                      onClick={() => setStoreMode(opt.value)}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
                <p className="text-muted text-sm mt-3">
                  {STORE_MODE_OPTIONS.find(o => o.value === storeMode)?.desc}
                </p>
              </div>

              <button type="submit" className="btn btn-primary" disabled={saving}>
                {saving ? '验证中...' : shop ? '更新连接' : '连接货源'}
              </button>
            </form>

            {result && (
              <div
                className="mt-3"
                style={{
                  padding: '10px 16px',
                  borderRadius: 8,
                  background: result.ok ? 'rgba(16,185,129,0.08)' : 'rgba(239,68,68,0.08)',
                  color: result.ok ? 'var(--success)' : 'var(--danger)',
                  fontSize: 13,
                  border: `1px solid ${result.ok ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)'}`,
                }}
              >
                {result.message}
              </div>
            )}
          </div>

          {/* Demo 模式 */}
          <div className="card" style={{ padding: 20 }}>
            <div className="card-header" style={{ marginBottom: 12 }}>
              <span className="card-title">Demo 模式</span>
            </div>
            <p className="text-muted text-sm">
              开启 Demo 模式后（环境变量 <code style={{ background: 'var(--bg-primary)', padding: '2px 6px', borderRadius: 4, fontSize: 12 }}>DEMO_MODE=true</code>），
              无需连接真实店铺即可查看模拟数据，适合演示和开发调试。
            </p>
          </div>

        </div>
      </div>
    </AuthGuard>
  );
}
