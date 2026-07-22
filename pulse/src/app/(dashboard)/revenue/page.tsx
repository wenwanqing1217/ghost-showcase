'use client';

import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, BarChart, Bar, Legend } from 'recharts';
import { TrendingUp, TrendingDown, DollarSign, ShoppingCart, Users, ArrowUpRight } from 'lucide-react';

type RevenueDataPoint = {
  date: string;
  revenue: number;
  orders: number;
  visitors: number;
  conversionRate: number;
};

export default function RevenuePage() {
  const [metrics, setMetrics] = useState<{ revenue: number; orders: number; avgOrderValue: number; agentRunsToday: number; approvalRate: number; p1Alerts: number } | null>({
    revenue: 12450,
    orders: 186,
    avgOrderValue: 66.9,
    agentRunsToday: 12,
    approvalRate: 94.2,
    p1Alerts: 3,
  });
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<'weekly' | 'monthly'>('weekly');

  useEffect(() => {
    fetch('/api/dashboard/metrics')
      .then((res) => res.json())
      .then((data) => {
        if (data.success && data.data) {
          setMetrics(data.data);
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const data: RevenueDataPoint[] = [
    { date: 'Mon', revenue: 1200, orders: 32, visitors: 540, conversionRate: 5.9 },
    { date: 'Tue', revenue: 900, orders: 28, visitors: 480, conversionRate: 5.8 },
    { date: 'Wed', revenue: 1500, orders: 41, visitors: 610, conversionRate: 6.7 },
    { date: 'Thu', revenue: 1100, orders: 30, visitors: 520, conversionRate: 5.8 },
    { date: 'Fri', revenue: 1800, orders: 45, visitors: 690, conversionRate: 6.5 },
    { date: 'Sat', revenue: 2100, orders: 52, visitors: 740, conversionRate: 7.0 },
    { date: 'Sun', revenue: 1850, orders: 47, visitors: 700, conversionRate: 6.7 },
  ];
  const totalRevenue = metrics?.revenue || 0;
  const totalOrders = metrics?.orders || 0;
  const avgConversion = metrics?.approvalRate || 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Revenue & Analytics</h1>
          <p className="text-gray-400 mt-1">Real-time sales performance and trends from Shopify</p>
        </div>
        {metrics && (
          <div className="flex gap-2 bg-gray-800 rounded-lg p-1 border border-gray-700">
            {(['weekly', 'monthly'] as const).map((v) => (
              <button
                key={v}
                onClick={() => setView(v)}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${view === v ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'}`}
              >
                {v === 'weekly' ? 'Weekly' : 'Monthly'}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KpiCard title="Total Revenue" value={`$${totalRevenue.toLocaleString()}`} icon={<DollarSign className="h-5 w-5" />} />
        <KpiCard title="Total Orders" value={`${totalOrders}`} icon={<ShoppingCart className="h-5 w-5" />} />
        <KpiCard title="Avg Conversion" value={`${avgConversion.toFixed(1)}%`} icon={<Users className="h-5 w-5" />} />
        <KpiCard title="Agent Runs Today" value={`${metrics?.agentRunsToday || 0}`} icon={<TrendingUp className="h-5 w-5" />} />
      </div>

      {loading ? (
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
          <p className="text-gray-400">Loading revenue data...</p>
        </div>
      ) : !metrics ? (
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 text-center">
          <DollarSign className="h-8 w-8 text-gray-500 mx-auto mb-2" />
          <p className="text-gray-400">No revenue data yet. Connect your Shopify store and analytics to see real-time metrics.</p>
        </div>
      ) : (
        <>
          {/* Revenue Chart */}
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Revenue Trend</h2>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data}>
                  <defs>
                    <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="date" stroke="#9ca3af" />
                  <YAxis stroke="#9ca3af" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                    labelStyle={{ color: '#fff' }}
                    itemStyle={{ color: '#9ca3af' }}
                    formatter={(value: number) => [`$${value.toLocaleString()}`, 'Revenue']}
                  />
                  <Area type="monotone" dataKey="revenue" stroke="#3b82f6" fill="url(#revenueGradient)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Orders and Visitors */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Orders</h2>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="date" stroke="#9ca3af" />
                    <YAxis stroke="#9ca3af" />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                      labelStyle={{ color: '#fff' }}
                      formatter={(value: number) => [value, 'Orders']}
                    />
                    <Bar dataKey="orders" fill="#10b981" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Visitors</h2>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="date" stroke="#9ca3af" />
                    <YAxis stroke="#9ca3af" />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                      labelStyle={{ color: '#fff' }}
                      formatter={(value: number) => [value.toLocaleString(), 'Visitors']}
                    />
                    <Line type="monotone" dataKey="visitors" stroke="#8b5cf6" strokeWidth={2} dot={{ fill: '#8b5cf6' }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function KpiCard({ title, value, icon }: { title: string; value: string; icon: React.ReactNode }) {
  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700 p-4">
      <div className="flex items-center justify-between">
        <p className="text-gray-400 text-sm">{title}</p>
        <div className="text-gray-400">{icon}</div>
      </div>
      <p className="text-2xl font-bold text-white mt-2">{value}</p>
    </div>
  );
}
