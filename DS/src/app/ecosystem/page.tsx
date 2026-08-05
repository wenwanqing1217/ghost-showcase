'use client';

import { useEffect, useState } from 'react';
import TopBar from '@/components/layout/TopBar';
import AuthGuard from '@/components/layout/AuthGuard';
import { getApiUrl } from '@/lib/gateway-client';
import { DEMO_AGENTS } from '@/lib/demo-data';

interface Agent {
  name: string;
  role: string;
  status: string;
  desc: string;
}

export default function EcosystemPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [isDemo, setIsDemo] = useState(false);

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      // 真实 Agent 网络端点（A2A 注册表）
      const res = await fetch('/api/v1/agent/a2a/agents');
      const data = await res.json();
      const agentList = (data.data?.agents || data.data || data.agents || []) as any[];
      if (agentList.length > 0) {
        setAgents(agentList.map((a) => ({
          name: a.name || a.agent_id || 'Unknown',
          role: a.role || a.type || 'Agent',
          status: a.status === 'online' ? 'online' : 'offline',
          desc: a.description || a.desc || '',
        })));
        setIsDemo(false);
      } else {
        throw new Error('empty');
      }
    } catch {
      setIsDemo(true);
      setAgents(DEMO_AGENTS.map(a => ({ name: a.name, role: a.skills.join(', '), status: a.status, desc: `${a.skills.slice(0, 2).join(' + ')} 能力` })));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthGuard>
      <TopBar title="Agent 网络" subtitle="A2A 协议 · Agent 注册与发现 · 技能市场" />
      <div className="p-6">
        <div className="max-w-5xl mx-auto">
          {/* 演示模式横幅 */}
          {isDemo && (
            <div className="p-3 rounded-xl mb-4 animate-slide-up" style={{
              background: 'rgba(245,158,11,0.08)',
              border: '1px solid rgba(245,158,11,0.15)',
              color: '#fbbf24',
              fontSize: 13,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#fbbf24', opacity: 0.7 }} />
              演示模式 — 未连接到 Agent 网络，显示示例智能体数据
            </div>
          )}

          {/* 快速导航 */}
          <div className="grid md:grid-cols-3 gap-4 mb-6">
            <a href="/ecosystem/a2a" className="card" style={{ padding: 20, textDecoration: 'none', color: 'inherit' }}>
              <div style={{ fontWeight: 600, marginBottom: 4 }}>A2A 协议</div>
              <p className="text-muted text-sm">Agent 注册 · 发现 · 协作 · 技能市场</p>
            </a>
            <a href="/ecosystem/obsidian" className="card" style={{ padding: 20, textDecoration: 'none', color: 'inherit' }}>
              <div style={{ fontWeight: 600, marginBottom: 4 }}>知识图谱</div>
              <p className="text-muted text-sm">Obsidian 知识库 · 策略笔记 · 供应商画像</p>
            </a>
            <a href="/demo" className="card" style={{ padding: 20, textDecoration: 'none', color: 'inherit' }}>
              <div style={{ fontWeight: 600, marginBottom: 4 }}>演示</div>
              <p className="text-muted text-sm">DID 生成演示 · 数字身份诞生过程</p>
            </a>
          </div>

          {/* Agent 网络拓扑 */}
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
            {agents.map((agent, i) => (
              <div key={i} className="card" style={{ padding: 20, transition: 'all 0.2s ease' }}
                onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 4px 20px rgba(0,0,0,0.15)'; }}
                onMouseLeave={(e) => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.boxShadow = 'none'; }}
              >
                <div className="flex-between">
                  <div className="flex items-center gap-3">
                    <div style={{
                      width: 40, height: 40, borderRadius: 12,
                      background: 'linear-gradient(135deg, var(--nebula), var(--cosmic))',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      color: 'white', fontSize: 16, fontWeight: 700,
                      boxShadow: '0 2px 8px rgba(139,92,246,0.25)',
                    }}>
                      {agent.name[0]}
                    </div>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 15, color: 'var(--text-primary)' }}>{agent.name}</div>
                      <div className="text-muted" style={{ fontSize: 12 }}>{agent.role}</div>
                    </div>
                  </div>
                  <span className={`badge ${agent.status === 'online' ? 'badge-active' : 'badge-pending'}`} style={{ fontSize: 11 }}>
                    {agent.status === 'online' ? '● 在线' : '○ 离线'}
                  </span>
                </div>
                <p className="text-muted" style={{ fontSize: 13, marginTop: 12, lineHeight: 1.5 }}>{agent.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}
