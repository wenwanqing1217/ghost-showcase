'use client';

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Settings</h1>
      <div className="bg-slate-900/50 border border-blue-500/20 rounded-2xl p-6">
        <h2 className="text-xl font-semibold mb-4">Store Configuration</h2>
        <p className="text-slate-400">Configure your Shopify store credentials and AI settings here.</p>
      </div>
    </div>
  );
}
