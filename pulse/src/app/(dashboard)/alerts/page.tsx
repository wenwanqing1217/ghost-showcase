'use client';

import { useState, useEffect } from 'react';
import { AlertTriangle, Info, CheckCircle, XCircle, Bell } from 'lucide-react';

type Alert = {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  source: string;
  timestamp: string;
  read: boolean;
};

const typeConfig = {
  error: { icon: <XCircle className="h-4 w-4" />, color: 'text-red-400 bg-red-400/10 border-red-400/20' },
  warning: { icon: <AlertTriangle className="h-4 w-4" />, color: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20' },
  success: { icon: <CheckCircle className="h-4 w-4" />, color: 'text-green-400 bg-green-400/10 border-green-400/20' },
  info: { icon: <Info className="h-4 w-4" />, color: 'text-blue-400 bg-blue-400/10 border-blue-400/20' },
};

const DEFAULT_ALERTS: Alert[] = [
  {
    id: 'alert-1',
    type: 'error',
    title: 'Inventory Critical',
    message: 'SKU-1024 stock dropped below safety threshold.',
    source: 'Warehouse',
    timestamp: new Date().toISOString(),
    read: false,
  },
  {
    id: 'alert-2',
    type: 'warning',
    title: 'Shipping Delay',
    message: 'Courier SLA breached for 3 orders.',
    source: 'Logistics',
    timestamp: new Date().toISOString(),
    read: false,
  },
];

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  useEffect(() => {
    fetch('/api/dashboard/alerts')
      .then((res) => res.json())
      .then((data) => {
        if (data.success && Array.isArray(data.data)) {
          setAlerts(data.data);
        } else {
          setAlerts((prev) => (prev.length ? prev : DEFAULT_ALERTS));
        }
        setLoading(false);
      })
      .catch(() => {
        setAlerts((prev) => (prev.length ? prev : DEFAULT_ALERTS));
        setLoading(false);
      });
  }, []);

  const markAsRead = (id: string) => {
    setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, read: true } : a)));
  };

  const markAllAsRead = () => {
    setAlerts((prev) => prev.map((a) => ({ ...a, read: true })));
  };

  const filtered = filter === 'all' ? alerts : alerts.filter((a) => !a.read);
  const unreadCount = alerts.filter((a) => !a.read).length;

  const formatTime = (iso: string) => {
    const d = new Date(iso);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    if (hours < 1) return 'Just now';
    if (hours < 24) return `${hours}h ago`;
    return d.toLocaleDateString();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Alerts</h1>
          <p className="text-gray-400 mt-1">System notifications and agent alerts</p>
        </div>
        {alerts.length > 0 && (
          <button
            onClick={markAllAsRead}
            disabled={unreadCount === 0}
            className="flex items-center gap-2 bg-gray-800 hover:bg-gray-700 disabled:bg-gray-800 disabled:text-gray-500 text-white px-4 py-2 rounded-lg text-sm font-medium border border-gray-700 transition-colors"
          >
            <Bell className="h-4 w-4" />
            Mark all read
          </button>
        )}
      </div>

      {unreadCount > 0 && (
        <div className="bg-blue-600/10 border border-blue-600/20 rounded-lg px-4 py-3 flex items-center gap-3">
          <Bell className="h-5 w-5 text-blue-400" />
          <p className="text-blue-300 text-sm">You have {unreadCount} unread alert{unreadCount > 1 ? 's' : ''}</p>
        </div>
      )}

      {alerts.length > 0 && (
        <div className="flex gap-2">
          {(['all', 'unread'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${filter === f ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white border border-gray-700'}`}
            >
              {f === 'all' ? 'All Alerts' : 'Unread'}
            </button>
          ))}
        </div>
      )}

      {loading ? (
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
          <p className="text-gray-400">Loading alerts...</p>
        </div>
      ) : alerts.length === 0 ? (
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 text-center">
          <Bell className="h-8 w-8 text-gray-500 mx-auto mb-2" />
          <p className="text-gray-400">No alerts yet. Connect your agents and systems to receive real-time notifications.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((a) => {
            const config = typeConfig[a.type];
            return (
              <div
                key={a.id}
                className={`bg-gray-800 rounded-xl border p-4 hover:bg-gray-700/30 transition-colors ${!a.read ? 'border-l-4' : 'border-gray-700'}`}
                style={!a.read ? { borderLeftColor: a.type === 'error' ? '#f87171' : a.type === 'warning' ? '#fbbf24' : a.type === 'success' ? '#34d399' : '#60a5fa' } : {}}
              >
                <div className="flex items-start gap-4">
                  <div className={`mt-0.5 p-2 rounded-lg ${config.color}`}>{config.icon}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="text-white font-medium text-sm truncate">{a.title}</h3>
                      <span className="text-gray-500 text-xs whitespace-nowrap">{formatTime(a.timestamp)}</span>
                    </div>
                    <p className="text-gray-400 text-sm mt-1">{a.message}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-xs text-gray-500">{a.source}</span>
                      {!a.read && (
                        <button onClick={() => markAsRead(a.id)} className="text-xs text-blue-400 hover:text-blue-300 transition-colors">
                          Mark as read
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
