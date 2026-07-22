'use client';

import { useState } from 'react';
import { ListingDraft } from '@/types/shopify';

export default function ContentAgentPage() {
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('');
  const [keywords, setKeywords] = useState('');
  const [draft, setDraft] = useState<ListingDraft | null>(null);
  const [loading, setLoading] = useState(false);
  const [approvalId, setApprovalId] = useState<string | null>(null);
  const [riskFlags, setRiskFlags] = useState<string[]>([]);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/agents/content/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          category,
          keywords: keywords.split(',').map((k) => k.trim()).filter(Boolean),
          brief: 'High-quality product for modern lifestyle.',
        }),
      });
      const json = await res.json();
      if (json.success) {
        setDraft(json.data);
        setApprovalId(json.approvalId);
        setRiskFlags(json.riskFlags?.map((r: { message: string }) => r.message) ?? []);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleApproval = async (status: 'approved' | 'rejected') => {
    if (!approvalId) return;
    await fetch('/api/agents/content/approve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ approvalId, status }),
    });
    alert(status === 'approved' ? 'Listing approved' : 'Listing rejected');
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Content Agent</h1>

      <div className="bg-slate-900/50 border border-blue-500/20 rounded-2xl p-6">
        <h2 className="text-xl font-semibold mb-4">Generate Listing</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <input
            className="bg-slate-800 border border-slate-700 rounded-lg p-3 text-white"
            placeholder="Product title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <input
            className="bg-slate-800 border border-slate-700 rounded-lg p-3 text-white"
            placeholder="Category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          />
          <input
            className="bg-slate-800 border border-slate-700 rounded-lg p-3 text-white md:col-span-2"
            placeholder="Keywords (comma separated)"
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
          />
        </div>
        <button
          onClick={handleGenerate}
          disabled={loading}
          className="mt-4 px-6 py-3 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium hover:from-blue-500 hover:to-purple-500 transition-all shadow-lg shadow-blue-500/25 disabled:opacity-50"
        >
          {loading ? 'Generating...' : 'Generate Listing'}
        </button>
      </div>

      {riskFlags.length > 0 && (
        <div className="bg-red-900/20 border border-red-500/30 rounded-2xl p-6">
          <h3 className="text-red-400 font-semibold mb-2">Risk Flags</h3>
          <ul className="list-disc list-inside text-red-300">
            {riskFlags.map((flag, i) => (
              <li key={i}>{flag}</li>
            ))}
          </ul>
        </div>
      )}

      {draft && (
        <div className="bg-slate-900/50 border border-blue-500/20 rounded-2xl p-6">
          <h2 className="text-xl font-semibold mb-4">AI Generated Listing</h2>
          <div className="space-y-4">
            <div>
              <p className="text-slate-400 text-sm">Title</p>
              <p className="text-white">{draft.title}</p>
            </div>
            <div>
              <p className="text-slate-400 text-sm">Description</p>
              <p className="text-white whitespace-pre-wrap">{draft.description}</p>
            </div>
            <div>
              <p className="text-slate-400 text-sm">Tags</p>
              <div className="flex flex-wrap gap-2">
                {draft.tags.map((tag) => (
                  <span key={tag} className="px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 text-sm">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          </div>
          <div className="flex gap-4 mt-6">
            <button
              onClick={() => handleApproval('approved')}
              className="px-6 py-3 rounded-full bg-green-600 text-white font-medium hover:bg-green-500 transition-colors"
            >
              Approve
            </button>
            <button
              onClick={() => handleApproval('rejected')}
              className="px-6 py-3 rounded-full bg-red-600 text-white font-medium hover:bg-red-500 transition-colors"
            >
              Reject
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
