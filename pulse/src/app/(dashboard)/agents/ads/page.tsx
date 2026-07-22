'use client';

import { useState, useEffect } from 'react';
import { TrendingUp, DollarSign, Target, Play, Square } from 'lucide-react';

type AdCampaign = {
  id: string;
  name: string;
  status: 'active' | 'paused' | 'draft';
  budget: number;
  spent: number;
  impressions: number;
  clicks: number;
  conversions: number;
  ctr: number;
  roas: number;
  bidStrategy: 'auto' | 'manual';
  maxBid: number;
};

type AdRecommendation = {
  id: string;
  type: 'budget' | 'bid' | 'targeting' | 'creative';
  priority: 'high' | 'medium' | 'low';
  message: string;
  impact: string;
};

export default function AdsAgentPage() {
  const [campaigns, setCampaigns] = useState<AdCampaign[]>([
    {
      id: 'campaign-1',
      name: 'Summer Sale Collection',
      status: 'active',
      budget: 1200,
      spent: 840.5,
      impressions: 124000,
      clicks: 3200,
      conversions: 210,
      ctr: 2.58,
      roas: 3.1,
      bidStrategy: 'auto',
      maxBid: 1.25,
    },
  ]);
  const [recommendations, setRecommendations] = useState<AdRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [isOptimizing, setIsOptimizing] = useState(false);

  useEffect(() => {
    Promise.all([
      fetch('/api/agents/ads/campaigns').then((res) => res.json()),
      fetch('/api/agents/ads/recommend').then((res) => res.json()),
    ]).then(([campaignsData, recommendationsData]) => {
      if (campaignsData.success && Array.isArray(campaignsData.data)) {
        setCampaigns(campaignsData.data);
      } else {
        setCampaigns((prev) => (prev.length ? prev : [
          {
            id: 'campaign-1',
            name: 'Summer Sale Collection',
            status: 'active',
            budget: 1200,
            spent: 840.5,
            impressions: 124000,
            clicks: 3200,
            conversions: 210,
            ctr: 2.58,
            roas: 3.1,
            bidStrategy: 'auto',
            maxBid: 1.25,
          },
        ]));
      }
      if (recommendationsData.success && Array.isArray(recommendationsData.data)) {
        setRecommendations(recommendationsData.data);
      }
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const toggleCampaign = (id: string) => {
    setCampaigns((prev) =>
      prev.map((c) =>
        c.id === id
          ? { ...c, status: c.status === 'active' ? 'paused' : 'active' }
          : c,
      ),
    );
  };

  const runOptimization = async () => {
    setIsOptimizing(true);
    await new Promise((r) => setTimeout(r, 1500));
    setIsOptimizing(false);
  };

  const totalBudget = campaigns.reduce((s, c) => s + c.budget, 0);
  const totalSpent = campaigns.reduce((s, c) => s + c.spent, 0);
  const avgRoas = campaigns.length > 0 ? campaigns.reduce((s, c) => s + c.roas, 0) / campaigns.length : 0;

  const getPriorityColor = (p: string) =>
    p === 'high' ? 'text-red-400 bg-red-400/10' : p === 'medium' ? 'text-yellow-400 bg-yellow-400/10' : 'text-blue-400 bg-blue-400/10';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Ads Agent</h1>
          <p className="text-gray-400 mt-1">AI-powered ad campaign optimization</p>
        </div>
        <button
          onClick={runOptimization}
          disabled={isOptimizing || campaigns.length === 0}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 text-white px-4 py-2 rounded-lg font-medium transition-colors"
        >
          {isOptimizing ? (
            <span className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            <TrendingUp className="h-4 w-4" />
          )}
          {isOptimizing ? 'Optimizing...' : 'Auto-Optimize'}
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KpiCard title="Total Budget" value={`$${totalBudget.toFixed(2)}`} icon={<DollarSign className="h-5 w-5" />} />
        <KpiCard title="Total Spent" value={`$${totalSpent.toFixed(2)}`} icon={<TrendingUp className="h-5 w-5" />} />
        <KpiCard title="Avg ROAS" value={`${avgRoas.toFixed(2)}x`} icon={<Target className="h-5 w-5" />} />
        <KpiCard title="Active Campaigns" value={`${campaigns.filter((c) => c.status === 'active').length}/${campaigns.length}`} icon={<Play className="h-5 w-5" />} />
      </div>

      {loading ? (
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
          <p className="text-gray-400">Loading campaigns...</p>
        </div>
      ) : campaigns.length === 0 ? (
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 text-center">
          <Target className="h-8 w-8 text-gray-500 mx-auto mb-2" />
          <p className="text-gray-400">No campaigns yet. Connect your ad platform to sync real campaign data.</p>
        </div>
      ) : (
        <>
          {/* Campaigns Table */}
          <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-700">
              <h2 className="text-lg font-semibold text-white">Campaigns</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-gray-900/50 text-gray-400">
                  <tr>
                    <th className="px-6 py-3">Campaign</th>
                    <th className="px-6 py-3">Status</th>
                    <th className="px-6 py-3">Budget</th>
                    <th className="px-6 py-3">Spent</th>
                    <th className="px-6 py-3">CTR</th>
                    <th className="px-6 py-3">ROAS</th>
                    <th className="px-6 py-3">Bid</th>
                    <th className="px-6 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {campaigns.map((c) => (
                    <tr key={c.id} className="hover:bg-gray-700/30 transition-colors">
                      <td className="px-6 py-4">
                        <div>
                          <p className="text-white font-medium">{c.name}</p>
                          <p className="text-xs text-gray-400">{c.bidStrategy === 'auto' ? 'Auto bidding' : `Manual max $${c.maxBid}`}</p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${c.status === 'active' ? 'bg-green-400/10 text-green-400' : 'bg-gray-400/10 text-gray-400'}`}>
                          {c.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-gray-300">${c.budget.toFixed(2)}</td>
                      <td className="px-6 py-4 text-gray-300">${c.spent.toFixed(2)}</td>
                      <td className="px-6 py-4 text-gray-300">{c.ctr.toFixed(2)}%</td>
                      <td className="px-6 py-4 text-gray-300">{c.roas.toFixed(2)}x</td>
                      <td className="px-6 py-4 text-gray-300">${c.maxBid.toFixed(2)}</td>
                      <td className="px-6 py-4">
                        <button
                          onClick={() => toggleCampaign(c.id)}
                          className={`flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${c.status === 'active' ? 'bg-red-400/10 text-red-400 hover:bg-red-400/20' : 'bg-green-400/10 text-green-400 hover:bg-green-400/20'}`}
                        >
                          {c.status === 'active' ? <Square className="h-3 w-3" /> : <Play className="h-3 w-3" />}
                          {c.status === 'active' ? 'Pause' : 'Activate'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Recommendations */}
          {recommendations.length > 0 && (
            <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
              <h2 className="text-lg font-semibold text-white mb-4">AI Recommendations</h2>
              <div className="space-y-3">
                {recommendations.map((r) => (
                  <div key={r.id} className="flex items-start gap-4 bg-gray-700/30 rounded-lg p-4 hover:bg-gray-700/50 transition-colors">
                    <span className={`mt-0.5 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getPriorityColor(r.priority)}`}>
                      {r.priority}
                    </span>
                    <div className="flex-1">
                      <p className="text-white text-sm font-medium">{r.message}</p>
                      <p className="text-gray-400 text-xs mt-1">{r.impact}</p>
                    </div>
                    <button className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-md transition-colors">
                      Apply
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
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
