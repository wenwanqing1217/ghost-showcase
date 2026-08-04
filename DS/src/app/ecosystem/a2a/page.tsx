'use client';

import TopBar from '@/components/layout/TopBar';
import AuthGuard from '@/components/layout/AuthGuard';
import { useEffect, useState } from 'react';

interface AgentInfo {
  name: string;
  role: string;
  status: string;
  desc: string;
  skills?: string[];
}

export default function A2APage() {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const res = await fetch('/api/v1/agent/a2a/agents');
        if (res.ok) {
          const data = await res.json();
          const agentList = data.data?.agents || data.data || [];
          setAgents(agentList.map((a: any) => ({
            name: a.name || a.agent_id || 'Unknown',
            role: a.role || a.type || 'Agent',
            status: a.status === 'online' ? 'online' : 'offline',
            desc: a.description || a.desc || '',
            skills: a.skills || [],
          })));
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : '加载失败');
      } finally {
        setLoading(false);
      }
    };
    fetchAgents();
  }, []);

  return (
    <AuthGuard>
      <TopBar title="A2A 协议" subtitle="Agent 注册与发现 · 技能市场 · 网络拓扑" />
      <div className="p-6">
        <div className="max-w-5xl mx-auto">
          {/* 网络拓扑概览 */}
          <div className="card mb-6" style={{ padding: 40, textAlign: 'center' }}>
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 16 }}>
              <div style={{
                width: 56, height: 56,
                borderRadius: '50%',
                background: 'radial-gradient(circle at 40% 35%, rgba(139,92,246,0.6) 0%, rgba(56,189,248,0.2) 60%, transparent 100%)',
                filter: 'blur(8px)',
              }} />
            </div>
            <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>A2A 网络拓扑</h2>
            <p className="text-muted" style={{ marginBottom: 24 }}>
              智能体注册 · 发现 · 协作 · 技能市场
            </p>
            <div className="flex gap-2" style={{ justifyContent: 'center', flexWrap: 'wrap' }}>
              <span className="badge badge-active">A2A 协议</span>
              <span className="badge badge-pending">Agent 注册</span>
              <span className="badge badge-paid">技能市场</span>
              <span className="badge badge-fulfilled">PoE 可验证</span>
            </div>
          </div>

          {/* Agent 列表 */}
          <div className="grid md:grid-cols-2 gap-4">
            {loading && (
              <div className="card col-span-full" style={{ padding: 40, textAlign: 'center' }}>
                <p className="text-muted">加载 Agent 列表...</p>
              </div>
            )}
            {error && (
              <div className="card col-span-full" style={{ padding: 40, textAlign: 'center', color: 'var(--danger)' }}>
                {error}
              </div>
            )}
            {!loading && !error && agents.map((agent, i) => (
              <div key={i} className="card" style={{ padding: 16 }}>
                <div className="flex-between">
                  <div className="flex items-center gap-3">
                    <div style={{
                      width: 36, height: 36, borderRadius: 10,
                      background: 'linear-gradient(135deg, var(--nebula), var(--cosmic))',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      color: 'white', fontSize: 14, fontWeight: 700
                    }}>
                      {agent.name[0]}
                    </div>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 14 }}>{agent.name}</div>
                      <div className="text-muted" style={{ fontSize: 11 }}>{agent.role}</div>
                    </div>
                  </div>
                  <span className={`badge ${agent.status === 'online' ? 'badge-active' : 'badge-pending'}`}>
                    {agent.status === 'online' ? '在线' : '离线'}
                  </span>
                </div>
                <p className="text-muted" style={{ fontSize: 12, marginTop: 8 }}>{agent.desc}</p>
                {agent.skills && agent.skills.length > 0 && (
                  <div className="flex gap-1.5 mt-2 flex-wrap">
                    {agent.skills.map((skill, j) => (
                      <span key={j} className="badge badge-pending" style={{ fontSize: 10 }}>{skill}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {!loading && !error && agents.length === 0 && (
              <div className="card col-span-full" style={{ padding: 40, textAlign: 'center' }}>
                <p className="text-muted">暂无注册的 Agent</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}
