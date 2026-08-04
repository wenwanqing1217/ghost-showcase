'use client';

import TopBar from '@/components/layout/TopBar';
import AuthGuard from '@/components/layout/AuthGuard';

export default function WorkbenchPage() {
  return (
    <AuthGuard>
      <TopBar title="个人工作台" subtitle="你的数字灵魂 · 思维画布 · 任务板 · 笔记" />
      <div className="p-6">
        <div className="max-w-5xl mx-auto">
          <div className="grid md:grid-cols-3 gap-4 mb-6">
            {[
              { title: '思维画布', desc: '自由拖拽节点 · 知识图谱可视化', status: '开发中' },
              { title: '任务板', desc: '自动同步 · 优先级排序 · 进度追踪', status: '开发中' },
              { title: '笔记', desc: 'Markdown 编辑 · AI 辅助 · 标签分类', status: '开发中' },
            ].map((item, i) => (
              <div key={i} className="card" style={{ padding: 24 }}>
                <div style={{
                  width: 40, height: 40,
                  borderRadius: 10,
                  background: 'var(--bg-hover)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  marginBottom: 12,
                }}>
                  <div style={{
                    width: 16, height: 16,
                    borderRadius: '50%',
                    background: 'var(--nebula)',
                    opacity: 0.5,
                  }} />
                </div>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 6 }}>{item.title}</h3>
                <p className="text-muted" style={{ fontSize: 13, marginBottom: 12 }}>{item.desc}</p>
                <span className="badge badge-pending">{item.status}</span>
              </div>
            ))}
          </div>

          {/* 人格档案 */}
          <div className="card" style={{ padding: 24 }}>
            <div className="card-header">
              <span className="card-title">人格档案</span>
            </div>
            <p className="text-muted" style={{ fontSize: 13 }}>
              AI 视角下的你 · 性格分析 · 行为模式 · 偏好预测
            </p>
            <div className="flex gap-2" style={{ marginTop: 12 }}>
              <span className="badge badge-active">性格维度</span>
              <span className="badge badge-pending">行为模式</span>
              <span className="badge badge-paid">偏好标签</span>
            </div>
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}
