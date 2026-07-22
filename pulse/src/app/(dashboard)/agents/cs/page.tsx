'use client';

import { useState, useEffect } from 'react';
import { MessageSquare, AlertTriangle, Clock, CheckCircle } from 'lucide-react';

type Ticket = {
  id: string;
  customer: string;
  email: string;
  subject: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'open' | 'in_progress' | 'resolved' | 'escalated';
  category: 'shipping' | 'returns' | 'product' | 'payment' | 'other';
  assignedTo: string | null;
  createdAt: string;
  responseTime: string;
};

type EscalationRule = {
  id: string;
  name: string;
  trigger: string;
  action: string;
  enabled: boolean;
};

const priorityColors: Record<string, string> = {
  urgent: 'bg-red-400/10 text-red-400',
  high: 'bg-orange-400/10 text-orange-400',
  medium: 'bg-yellow-400/10 text-yellow-400',
  low: 'bg-blue-400/10 text-blue-400',
};

const statusIcons: Record<string, React.ReactNode> = {
  open: <MessageSquare className="h-4 w-4" />,
  in_progress: <Clock className="h-4 w-4" />,
  resolved: <CheckCircle className="h-4 w-4" />,
  escalated: <AlertTriangle className="h-4 w-4" />,
};

export default function CsAgentPage() {
  const [tickets, setTickets] = useState<Ticket[]>([
    {
      id: 'ticket-1',
      customer: 'Alice',
      email: 'alice@example.com',
      subject: 'Order not delivered after 10 days',
      priority: 'high',
      status: 'open',
      category: 'shipping',
      assignedTo: null,
      createdAt: new Date().toISOString(),
      responseTime: '2h',
    },
  ]);
  const [rules, setRules] = useState<EscalationRule[]>([
    {
      id: 'rule-1',
      name: 'Shipping delay > 3 days',
      trigger: 'status=shipping_delayed',
      action: 'escalate_to_logistics',
      enabled: true,
    },
  ]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'open' | 'escalated'>('all');
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);

  useEffect(() => {
    Promise.all([
      fetch('/api/agents/cs/tickets').then((res) => res.json()),
    ]).then(([ticketsData]) => {
      if (ticketsData.success && Array.isArray(ticketsData.data)) {
        setTickets(ticketsData.data);
      } else {
        setTickets((prev) => (prev.length ? prev : [
          {
            id: 'ticket-1',
            customer: 'Alice',
            email: 'alice@example.com',
            subject: 'Order not delivered after 10 days',
            priority: 'high',
            status: 'open',
            category: 'shipping',
            assignedTo: null,
            createdAt: new Date().toISOString(),
            responseTime: '2h',
          },
        ]));
      }
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const filtered = filter === 'all' ? tickets : tickets.filter((t) => t.status === filter);

  const resolveTicket = (id: string) => {
    setTickets((prev) => prev.map((t) => (t.id === id ? { ...t, status: 'resolved' as const } : t)));
    setSelectedTicket(null);
  };

  const escalateTicket = (id: string) => {
    setTickets((prev) => prev.map((t) => (t.id === id ? { ...t, status: 'escalated' as const, assignedTo: 'Human Agent' } : t)));
  };

  const toggleRule = (id: string) => {
    setRules((prev) => prev.map((r) => (r.id === id ? { ...r, enabled: !r.enabled } : r)));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">CS Agent</h1>
          <p className="text-gray-400 mt-1">Automated customer support with smart escalation</p>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KpiCard title="Open Tickets" value={`${tickets.filter((t) => t.status === 'open').length}`} icon={<MessageSquare className="h-5 w-5" />} />
        <KpiCard title="Escalated" value={`${tickets.filter((t) => t.status === 'escalated').length}`} icon={<AlertTriangle className="h-5 w-5" />} />
        <KpiCard title="Avg Response" value="--" icon={<Clock className="h-5 w-5" />} />
        <KpiCard title="Resolved Today" value={`${tickets.filter((t) => t.status === 'resolved').length}`} icon={<CheckCircle className="h-5 w-5" />} />
      </div>

      {tickets.length > 0 && (
        <div className="flex gap-2">
          {(['all', 'open', 'escalated'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${filter === f ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white border border-gray-700'}`}
            >
              {f === 'all' ? 'All Tickets' : f === 'open' ? 'Open' : 'Escalated'}
            </button>
          ))}
        </div>
      )}

      <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Escalation Rules</h2>
        <div className="divide-y divide-gray-700">
          {rules.map((rule) => (
            <div key={rule.id} className="flex items-center justify-between py-3">
              <div>
                <p className="text-white text-sm font-medium">{rule.name}</p>
                <p className="text-gray-400 text-xs">{rule.trigger} → {rule.action}</p>
              </div>
              <button
                onClick={() => toggleRule(rule.id)}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${rule.enabled ? 'bg-green-400/10 text-green-400 hover:bg-green-400/20' : 'bg-gray-700 text-gray-400 hover:text-white'}`}
              >
                {rule.enabled ? 'Enabled' : 'Disabled'}
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Ticket List */}
        <div className="lg:col-span-2 bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-700 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">Ticket Queue</h2>
            <span className="text-sm text-gray-400">{filtered.length} tickets</span>
          </div>
          {loading ? (
            <div className="p-6 text-gray-400">Loading tickets...</div>
          ) : tickets.length === 0 ? (
            <div className="p-6 text-center text-gray-500">No tickets yet. Connect your customer support system to receive real tickets.</div>
          ) : (
            <div className="divide-y divide-gray-700">
              {filtered.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setSelectedTicket(t)}
                  className={`w-full text-left px-6 py-4 hover:bg-gray-700/30 transition-colors ${selectedTicket?.id === t.id ? 'bg-gray-700/40' : ''}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <div className={`mt-1 p-1.5 rounded-md ${priorityColors[t.priority]}`}>{statusIcons[t.status]}</div>
                      <div>
                        <p className="text-white font-medium text-sm">{t.subject}</p>
                        <p className="text-gray-400 text-xs mt-0.5">{t.customer} · {t.email}</p>
                      </div>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-md ${priorityColors[t.priority]}`}>{t.priority}</span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {selectedTicket ? (
            <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
              <h3 className="text-white font-semibold mb-4">Ticket {selectedTicket.id}</h3>
              <div className="space-y-3 text-sm">
                <div>
                  <p className="text-gray-400">Subject</p>
                  <p className="text-white">{selectedTicket.subject}</p>
                </div>
                <div>
                  <p className="text-gray-400">Customer</p>
                  <p className="text-white">{selectedTicket.customer}</p>
                </div>
                <div>
                  <p className="text-gray-400">Category</p>
                  <p className="text-white capitalize">{selectedTicket.category}</p>
                </div>
                <div>
                  <p className="text-gray-400">Assigned To</p>
                  <p className="text-white">{selectedTicket.assignedTo || 'Unassigned'}</p>
                </div>
                <div>
                  <p className="text-gray-400">Priority</p>
                  <span className={`inline-block px-2 py-0.5 rounded text-xs ${priorityColors[selectedTicket.priority]}`}>{selectedTicket.priority}</span>
                </div>
              </div>
              <div className="flex gap-2 mt-6">
                <button
                  onClick={() => resolveTicket(selectedTicket.id)}
                  className="flex-1 flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded-lg text-sm font-medium transition-colors"
                >
                  <CheckCircle className="h-4 w-4" /> Resolve
                </button>
                <button
                  onClick={() => escalateTicket(selectedTicket.id)}
                  disabled={selectedTicket.status === 'escalated'}
                  className="flex-1 flex items-center justify-center gap-2 bg-orange-600 hover:bg-orange-700 disabled:bg-gray-600 text-white px-3 py-2 rounded-lg text-sm font-medium transition-colors"
                >
                  <AlertTriangle className="h-4 w-4" /> Escalate
                </button>
              </div>
            </div>
          ) : (
            <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 text-center">
              <MessageSquare className="h-8 w-8 text-gray-500 mx-auto mb-2" />
              <p className="text-gray-400 text-sm">Select a ticket to view details</p>
            </div>
          )}
        </div>
      </div>
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
