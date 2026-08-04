'use client';

import TopBar from '@/components/layout/TopBar';
import AuthGuard from '@/components/layout/AuthGuard';

export default function EcosystemPage() {
  return (
    <AuthGuard>
      <TopBar title="Agent 网络" subtitle="A2A 协议 · Agent 注册与发现 · 技能市场" />
      <div className="p-6">
        <div className="max-w-5xl mx-auto">
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
            {[
              { name: 'Ghost 中枢', role: '路由器', status: 'online', desc: '意图解析 → 技能路由 → 决策树' },
              { name: 'Alpha-ID', role: '身份层', status: 'online', desc: 'DID 生成 + Ed25519 签名 + 三层记忆' },
              { name: 'Nebula', role: '工作流', status: 'online', desc: 'DAG 编排 + 多跳推理 + 回溯' },
              { name: 'Flow', role: '引擎', status: 'online', desc: 'Fastify 工作流执行引擎' },
              { name: 'Gateway', role: '网关', status: 'online', desc: '统一 API 网关 · 请求路由' },
              { name: 'Net-Agent', role: '网络', status: 'online', desc: '网络操作 · 数据采集' },
            ].map((agent, i) => (
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
              </div>
            ))}
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}
