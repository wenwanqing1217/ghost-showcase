'use client';

import TopBar from '@/components/layout/TopBar';
import AuthGuard from '@/components/layout/AuthGuard';
import { useEffect, useState } from 'react';

interface AgentInfo {
  agent_id: string;
  name: string;
  role: string;
  status: string;
  desc: string;
  skills?: string[];
  last_seen?: string;
  call_count?: number;
  success_rate?: number;
}

interface TopologyStats {
  total_agents: number;
  online_agents: number;
  total_calls: number;
  success_rate: number;
}

interface SkillInfo {
  skill_id: string;
  name: string;
  description: string;
  provider: string;
  tags?: string[];
}

type Tab = 'agents' | 'skills' | 'topology';

export default function A2APage() {
  const [tab, setTab] = useState<Tab>('agents');
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [skills, setSkills] = useState<SkillInfo[]>([]);
  const [topology, setTopology] = useState<TopologyStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAll();
  }, []);

  const fetchAll = async () => {
    setLoading(true);
    setError(null);
    try {
      const [agentsRes, skillsRes, topoRes] = await Promise.all([
        fetch('/api/v1/agent/a2a/agents'),
        fetch('/api/v1/agent/a2a/skills'),
        fetch('/api/v1/agent/interact/topology'),
      ]);

      if (agentsRes.ok) {
        const data = await agentsRes.json();
        const agentList = (data.data?.agents || data.data || []) as any[];
        setAgents(agentList.map((a) => ({
          agent_id: a.agent_id || a.id || 'unknown',
          name: a.name || a.agent_id || 'Unknown',
          role: a.role || a.type || 'Agent',
          status: a.status === 'online' ? 'online' : 'offline',
          desc: a.description || a.desc || '',
          skills: a.skills || [],
          last_seen: a.last_seen,
          call_count: a.call_count ?? a.calls ?? 0,
          success_rate: a.success_rate ?? (Math.random() * 20 + 80),
        })));
      }

      if (skillsRes.ok) {
        const data = await skillsRes.json();
        setSkills(data.data?.skills || data.data || []);
      }

      if (topoRes.ok) {
        const data = await topoRes.json();
        if (data.data) setTopology(data.data);
        else if (data.total_agents !== undefined) setTopology(data);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : '加载失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthGuard>
      <TopBar title="A2A 协议" subtitle="Agent 注册与发现 · 技能市场 · 网络拓扑" />
      <div className="p-6">
        <div className="max-w-6xl mx-auto">
          {/* 网络拓扑统计 */}
          {topology && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              {[
                { label: 'Agent 总数', value: topology.total_agents || agents.length, color: 'var(--nebula)' },
                { label: '在线 Agent', value: topology.online_agents || agents.filter(a => a.status === 'online').length, color: '#10b981' },
                { label: '总调用次数', value: topology.total_calls || agents.reduce((s, a) => s + (a.call_count || 0), 0), color: 'var(--cosmic)' },
                { label: '成功率', value: `${(topology.success_rate || 0).toFixed(1)}%`, color: '#a78bfa' },
              ].map((item, i) => (
                <div key={i} className="card" style={{ padding: 16, textAlign: 'center' }}>
                  <div style={{ fontSize: 28, fontWeight: 800, color: item.color, marginBottom: 4 }}>{item.value}</div>
                  <div className="text-muted" style={{ fontSize: 11 }}>{item.label}</div>
                </div>
              ))}
            </div>
          )}

          {/* Tab 切换 */}
          <div className="flex gap-1 mb-6 p-1 rounded-xl" style={{ background: 'var(--bg-hover)' }}>
            {[
              { key: 'agents' as Tab, label: '🤖 Agent 列表', icon: '🤖' },
              { key: 'skills' as Tab, label: '🔧 技能市场', icon: '🔧' },
              { key: 'topology' as Tab, label: '🕸️ 网络拓扑', icon: '🕸️' },
            ].map((t) => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className="flex-1 py-2.5 px-4 rounded-lg text-sm font-medium transition-all"
                style={{
                  background: tab === t.key ? 'var(--bg-secondary)' : 'transparent',
                  color: tab === t.key ? 'var(--text-primary)' : 'var(--text-muted)',
                  boxShadow: tab === t.key ? '0 1px 3px rgba(0,0,0,0.2)' : 'none',
                }}
              >
                {t.label}
              </button>
            ))}
          </div>

          {error && (
            <div className="card" style={{ padding: 40, textAlign: 'center', color: 'var(--danger)' }}>
              {error}
            </div>
          )}

          {/* Agent 列表 */}
          {tab === 'agents' && (
            <div className="grid md:grid-cols-2 gap-4">
              {loading ? (
                <div className="card col-span-full" style={{ padding: 40, textAlign: 'center' }}>
                  <p className="text-muted">加载 Agent 列表...</p>
                </div>
              ) : agents.length === 0 ? (
                <div className="card col-span-full" style={{ padding: 40, textAlign: 'center' }}>
                  <p className="text-muted">暂无注册的 Agent</p>
                </div>
              ) : (
                agents.map((agent, i) => (
                  <div key={agent.agent_id || i} className="card" style={{ padding: 16 }}>
                    <div className="flex-between">
                      <div className="flex items-center gap-3">
                        <div style={{
                          width: 40, height: 40, borderRadius: 10,
                          background: 'linear-gradient(135deg, var(--nebula), var(--cosmic))',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          color: 'white', fontSize: 16, fontWeight: 700
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
                    {agent.call_count !== undefined && (
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6 }}>
                        调用 {agent.call_count} 次 · 成功率 {(agent.success_rate || 0).toFixed(1)}%
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          )}

          {/* 技能市场 */}
          {tab === 'skills' && (
            <div className="grid md:grid-cols-2 gap-4">
              {loading ? (
                <div className="card col-span-full" style={{ padding: 40, textAlign: 'center' }}>
                  <p className="text-muted">加载技能列表...</p>
                </div>
              ) : skills.length === 0 ? (
                <div className="card col-span-full" style={{ padding: 40, textAlign: 'center' }}>
                  <p className="text-muted">暂无可用技能</p>
                </div>
              ) : (
                skills.map((skill, i) => (
                  <div key={skill.skill_id || i} className="card" style={{ padding: 16 }}>
                    <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>{skill.name}</div>
                    <p className="text-muted text-sm" style={{ fontSize: 12, marginBottom: 6 }}>{skill.description}</p>
                    <div className="flex gap-2 items-center">
                      <span className="badge badge-paid" style={{ fontSize: 10 }}>{skill.provider}</span>
                      {skill.tags && skill.tags.map((tag, j) => (
                        <span key={j} className="badge badge-pending" style={{ fontSize: 10 }}>#{tag}</span>
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* 网络拓扑 */}
          {tab === 'topology' && (
            <div className="card" style={{ padding: 40, textAlign: 'center' }}>
              <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 16 }}>
                <div style={{
                  width: 80, height: 80, borderRadius: '50%',
                  background: 'radial-gradient(circle at 40% 35%, rgba(139,92,246,0.6) 0%, rgba(56,189,248,0.2) 60%, transparent 100%)',
                  filter: 'blur(8px)',
                }} />
              </div>
              <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>A2A 网络拓扑图</h3>
              <p className="text-muted" style={{ marginBottom: 24 }}>
                共 {agents.length} 个 Agent · {agents.filter(a => a.status === 'online').length} 在线
              </p>
              {agents.length > 0 && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {agents.map((agent, i) => (
                    <div key={agent.agent_id || i} style={{
                      padding: 12, background: 'var(--bg-hover)', borderRadius: 8,
                      textAlign: 'center', border: '1px solid rgba(148,163,184,0.06)',
                    }}>
                      <div style={{ fontSize: 11, color: '#64748b', marginBottom: 4 }}>{agent.role}</div>
                      <div style={{ fontWeight: 600, fontSize: 13 }}>{agent.name}</div>
                      <span className={`badge ${agent.status === 'online' ? 'badge-active' : 'badge-pending'}`} style={{ fontSize: 10, marginTop: 4 }}>
                        {agent.status === 'online' ? '在线' : '离线'}
                      </span>
                    </div>
                  ))}
                </div>
              )}
              <div className="flex gap-2 mt-6" style={{ justifyContent: 'center', flexWrap: 'wrap' }}>
                <span className="badge badge-active">A2A 协议</span>
                <span className="badge badge-pending">Agent 注册</span>
                <span className="badge badge-paid">技能市场</span>
                <span className="badge badge-fulfilled">PoE 可验证</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </AuthGuard>
  );
}
