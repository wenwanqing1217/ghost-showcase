'use client';

import { useState } from 'react';

interface FulfillModalProps {
  orderId: string;
  orderNo: string;
  onClose: () => void;
  onSuccess: () => void;
}

export default function FulfillModal({ orderId, orderNo, onClose, onSuccess }: FulfillModalProps) {
  const [trackingNumber, setTrackingNumber] = useState('');
  const [trackingCompany, setTrackingCompany] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`/api/orders/${orderId}/fulfill`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ trackingNumber, trackingCompany }),
      });
      const data = await res.json();
      if (data.ok) {
        onSuccess();
      } else {
        setError(data.error || '发货失败');
      }
    } catch {
      setError('网络错误，请重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.6)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
      }}
      onClick={onClose}
    >
      <div
        className="card"
        style={{ width: 420, maxWidth: '90vw', padding: 24 }}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>
          标记发货 — {orderNo}
        </h3>

        {error && (
          <div
            style={{
              padding: '8px 12px',
              background: 'rgba(255,107,107,0.1)',
              border: '1px solid rgba(255,107,107,0.3)',
              borderRadius: 6,
              color: 'var(--danger)',
              fontSize: 13,
              marginBottom: 12,
            }}
          >
            ⚠ {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <label style={{ display: 'block', marginBottom: 8, fontSize: 13, color: 'var(--text-muted)' }}>
            物流公司
          </label>
          <input
            className="input"
            placeholder="如：顺丰、DHL、UPS"
            value={trackingCompany}
            onChange={(e) => setTrackingCompany(e.target.value)}
            style={{ marginBottom: 16 }}
          />

          <label style={{ display: 'block', marginBottom: 8, fontSize: 13, color: 'var(--text-muted)' }}>
            运单号
          </label>
          <input
            className="input"
            placeholder="运单号（可为空）"
            value={trackingNumber}
            onChange={(e) => setTrackingNumber(e.target.value)}
            style={{ marginBottom: 20 }}
          />

          <div className="flex gap-2" style={{ justifyContent: 'flex-end' }}>
            <button type="button" className="btn btn-sm" onClick={onClose}>
              取消
            </button>
            <button
              type="submit"
              className="btn btn-sm btn-primary"
              disabled={loading}
            >
              {loading ? '处理中...' : '确认发货'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
