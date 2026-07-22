'use client';

import { useEffect, useState } from 'react';
import { DashboardMetrics } from '@/types/shopify';
import { Metadata } from 'next';

export default function DashboardClient() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/dashboard/metrics')
      .then((res) => res.json())
      .then((data) => {
        setMetrics(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Boss Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <MetricCard title="AI Runs Today" value={metrics?.agentRunsToday ?? 0} />
        <MetricCard title="Approval Rate" value={`${metrics?.approvalRate ?? 0}%`} />
        <MetricCard title="P1 Alerts" value={metrics?.p1Alerts ?? 0} alert />
      </div>

      <div className="bg-slate-900/50 border border-blue-500/20 rounded-2xl p-6">
        <h2 className="text-xl font-semibold mb-4">Getting Started</h2>
        <ol className="list-decimal list-inside space-y-2 text-slate-300">
          <li>Connect your Shopify store in Settings</li>
          <li>Add your OpenAI API key</li>
          <li>Go to Content Agent to generate your first AI listing</li>
          <li>Review and approve AI-generated content</li>
        </ol>
      </div>
    </div>
  );
}

function MetricCard({ title, value, alert }: { title: string; value: number | string; alert?: boolean }) {
  return (
    <div className="bg-slate-900/50 border border-blue-500/20 rounded-2xl p-6">
      <p className="text-slate-400 text-sm mb-2">{title}</p>
      <p className={`text-3xl font-bold ${alert && Number(value) > 0 ? 'text-red-400' : 'text-white'}`}>{value}</p>
    </div>
  );
}
