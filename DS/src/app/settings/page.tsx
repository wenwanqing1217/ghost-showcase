'use client';

import { useEffect, useState } from 'react';

interface ShopInfo {
  id: string;
  name: string;
  domain: string;
}

export default function SettingsPage() {
  const [shop, setShop] = useState<ShopInfo | null>(null);
  const [domain, setDomain] = useState('');
  const [accessToken, setAccessToken] = useState('');
  const [name, setName] = useState('');
  const [saving, setSaving] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; message: string } | null>(null);

  useEffect(() => {
    fetch('/api/shop')
      .then((r) => r.json())
      .then((data) => {
        if (data.shop) {
          setShop(data.shop);
          setDomain(data.shop.domain);
          setName(data.shop.name);
        }
      })
      .catch(() => {});
  }, []);

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setResult(null);

    try {
      const res = await fetch('/api/shop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain, accessToken, name }),
      });
      const data = await res.json();

      if (data.ok) {
        setResult({ ok: true, message: `连接成功！店铺: ${data.shop.name}` });
        setShop(data.shop);
      } else {
        setResult({ ok: false, message: data.error || '连接失败' });
      }
    } catch (err) {
      setResult({ ok: false, message: `请求错误: ${err instanceof Error ? err.message : '未知错误'}` });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 20 }}>店铺设置</h2>

      {/* 当前连接状态 */}
      {shop && (
        <div className="card mb-3" style={{ borderColor: 'var(--success)' }}>
          <div className="flex-between">
            <div>
              <div className="text-muted text-sm mb-3">当前已连接</div>
              <div style={{ fontWeight: 600 }}>{shop.name}</div>
              <div className="text-muted text-sm">{shop.domain}</div>
            </div>
            <span className="badge badge-active">已连接</span>
          </div>
        </div>
      )}

      {/* 连接表单 */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">{shop ? '重新连接' : '连接 Shoplazza 店铺'}</span>
        </div>

        <form onSubmit={handleConnect}>
          <div className="form-group">
            <label className="form-label">店铺域名</label>
            <input
              className="input"
              placeholder="your-store.myshopazza.com"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              required
            />
            <p className="text-muted text-sm mt-3">
              Shoplazza 店铺域名，格式：xxx.myshopazza.com
            </p>
          </div>

          <div className="form-group">
            <label className="form-label">Access Token</label>
            <input
              className="input"
              type="password"
              placeholder="输入你的 API Access Token"
              value={accessToken}
              onChange={(e) => setAccessToken(e.target.value)}
              required
            />
            <p className="text-muted text-sm mt-3">
              在 Shoplazza 后台 → 设置 → API 访问令牌 中生成
            </p>
          </div>

          <div className="form-group">
            <label className="form-label">店铺名称（可选）</label>
            <input
              className="input"
              placeholder="用于在看板中显示"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? '验证中...' : shop ? '更新连接' : '连接店铺'}
          </button>
        </form>

        {result && (
          <div
            className="mt-3"
            style={{
              padding: '10px 16px',
              borderRadius: 8,
              background: result.ok ? 'rgba(0,184,148,0.1)' : 'rgba(255,107,107,0.1)',
              color: result.ok ? 'var(--success)' : 'var(--danger)',
              fontSize: 13,
            }}
          >
            {result.message}
          </div>
        )}
      </div>

      {/* Demo 模式说明 */}
      <div className="card mt-3">
        <div className="card-header">
          <span className="card-title">Demo 模式</span>
        </div>
        <p className="text-muted text-sm">
          开启 Demo 模式后（环境变量 <code style={{ background: 'var(--bg-primary)', padding: '2px 6px', borderRadius: 4 }}>DEMO_MODE=true</code>），
          无需连接真实店铺即可查看模拟数据，适合演示和开发调试。
        </p>
      </div>
    </div>
  );
}
