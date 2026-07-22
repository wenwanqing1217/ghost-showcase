import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Product Detail | DS',
};

export default function ProductDetailPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Product Detail</h1>
      <div className="bg-slate-900/50 border border-blue-500/20 rounded-2xl p-6">
        <p className="text-slate-400">Product details will appear here when connected to Shopify.</p>
      </div>
    </div>
  );
}
