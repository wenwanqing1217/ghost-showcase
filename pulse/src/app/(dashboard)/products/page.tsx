'use client';

import { useEffect, useState } from 'react';
import { ShopifyProduct } from '@/types/shopify';

export default function ProductsPage() {
  const [products, setProducts] = useState<ShopifyProduct[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/shopify/products')
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          setProducts(data.data);
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Products</h1>
      </div>

      {loading ? (
        <div className="bg-slate-900/50 border border-blue-500/20 rounded-2xl p-6">
          <p className="text-slate-400">Loading products...</p>
        </div>
      ) : products.length === 0 ? (
        <div className="bg-slate-900/50 border border-blue-500/20 rounded-2xl p-6">
          <p className="text-slate-400">No products yet. Connect your Shopify store to sync products.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {products.map((product) => (
            <div
              key={product.id}
              className="bg-slate-900/50 border border-blue-500/20 rounded-2xl p-6 hover:border-blue-500/40 transition-colors"
            >
              <div className="flex items-start justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">{product.title}</h3>
                <span
                  className={`px-2 py-1 rounded-full text-xs ${
                    product.status === 'active'
                      ? 'bg-green-500/20 text-green-300'
                      : 'bg-yellow-500/20 text-yellow-300'
                  }`}
                >
                  {product.status}
                </span>
              </div>
              <p className="text-slate-400 text-sm mb-4 line-clamp-2">{product.bodyHtml}</p>
              <div className="flex flex-wrap gap-2">
                {product.tags?.split(',').map((tag) => (
                  <span key={tag.trim()} className="px-2 py-1 rounded-full bg-blue-500/10 text-blue-300 text-xs">
                    {tag.trim()}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
