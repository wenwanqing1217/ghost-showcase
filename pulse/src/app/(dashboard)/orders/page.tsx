'use client';

import { useEffect, useState } from 'react';
import { ShopifyOrder } from '@/types/shopify';

export default function OrdersPage() {
  const [orders, setOrders] = useState<ShopifyOrder[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/shopify/orders')
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          setOrders(data.data);
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Orders</h1>

      {loading ? (
        <div className="bg-slate-900/50 border border-blue-500/20 rounded-2xl p-6">
          <p className="text-slate-400">Loading orders...</p>
        </div>
      ) : orders.length === 0 ? (
        <div className="bg-slate-900/50 border border-blue-500/20 rounded-2xl p-6">
          <p className="text-slate-400">No orders yet. Connect your Shopify store to sync orders.</p>
        </div>
      ) : (
        <div className="bg-slate-900/50 border border-blue-500/20 rounded-2xl overflow-hidden">
          <table className="w-full">
            <thead className="bg-slate-800/50">
              <tr>
                <th className="px-6 py-3 text-left text-sm font-medium text-slate-400">Order</th>
                <th className="px-6 py-3 text-left text-sm font-medium text-slate-400">Customer</th>
                <th className="px-6 py-3 text-left text-sm font-medium text-slate-400">Total</th>
                <th className="px-6 py-3 text-left text-sm font-medium text-slate-400">Status</th>
                <th className="px-6 py-3 text-left text-sm font-medium text-slate-400">Risk</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {orders.map((order) => (
                <tr key={order.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-6 py-4 text-sm text-white">#{order.orderNumber ?? order.id}</td>
                  <td className="px-6 py-4 text-sm text-slate-300">
                    {order.customer?.firstName} {order.customer?.lastName}
                  </td>
                  <td className="px-6 py-4 text-sm text-white">${order.totalPrice}</td>
                  <td className="px-6 py-4">
                    <span
                      className={`px-2 py-1 rounded-full text-xs ${
                        order.fulfillmentStatus === 'fulfilled'
                          ? 'bg-green-500/20 text-green-300'
                          : order.fulfillmentStatus === 'partial'
                          ? 'bg-yellow-500/20 text-yellow-300'
                          : 'bg-slate-500/20 text-slate-300'
                      }`}
                    >
                      {order.fulfillmentStatus || 'pending'}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`px-2 py-1 rounded-full text-xs ${
                        order.riskLevel === 'high'
                          ? 'bg-red-500/20 text-red-300'
                          : order.riskLevel === 'medium'
                          ? 'bg-yellow-500/20 text-yellow-300'
                          : 'bg-green-500/20 text-green-300'
                      }`}
                    >
                      {order.riskLevel || 'low'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
