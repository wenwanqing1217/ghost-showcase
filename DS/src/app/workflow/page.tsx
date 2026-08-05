'use client';

import TopBar from '@/components/layout/TopBar';
import AuthGuard from '@/components/layout/AuthGuard';
import { useEffect, useState } from 'react';
import { DEMO_EXECUTIONS, WorkflowExecution } from '@/lib/demo-data';

interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  examples: string[];
}

export default function WorkflowPage() {
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([]);
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState(false);
  const [demoMode, setDemoMode] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [result, setResult] = useState<string | null>(null);

  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      const res = await fetch('/api/health');
      if (!res.ok) throw new Error('unhealthy');
    } catch {
      setDemoMode(true);
    }
    loadTemplates();
    loadExecutions();
  };

  const loadTemplates = async () => {
    try {
      // 走 DS 代理路由 → Gateway → Nebula（真实路径：/api/v1/workflow/templates）
      const res = await fetch('/api/v1/workflow/templates');
      const data = await res.json();
      if (data.templates) {
        setTemplates(data.templates);
      } else if (demoMode) {
        setTemplates([
          { id: 'map-navigation', name: '地图导航', description: '智能路线规划与导航指引', examples: ['怎么去中关村', '从国贸到西二旗'] },
          { id: 'douyin-publish', name: '抖音发布', description: '短视频内容生成与发布', examples: ['生成一个霸道总裁剧本', '写一个美食探店脚本'] },
          { id: 'shopify-optimize', name: 'Shopify 优化', description: '店铺数据优化与运营建议', examples: ['优化我的店铺', '提升转化率建议'] },
        ]);
      }
    } catch (err) {
      console.error('[WorkflowPage] loadTemplates error:', err);
      if (demoMode) {
        setTemplates([
          { id: 'map-navigation', name: '地图导航', description: '智能路线规划与导航指引', examples: ['怎么去中关村', '从国贸到西二旗'] },
          { id: 'douyin-publish', name: '抖音发布', description: '短视频内容生成与发布', examples: ['生成一个霸道总裁剧本', '写一个美食探店脚本'] },
          { id: 'shopify-optimize', name: 'Shopify 优化', description: '店铺数据优化与运营建议', examples: ['优化我的店铺', '提升转化率建议'] },
        ]);
      }
    }
  };

  const loadExecutions = async () => {
    // 后端暂无 executions 查询端点，直接使用演示记录（有真实端点后再接入）
    if (demoMode) {
      setExecutions(DEMO_EXECUTIONS);
      setLoading(false);
      return;
    }
    setExecutions(DEMO_EXECUTIONS);
    setLoading(false);
  };

  const executeWorkflow = async () => {
    if (!selectedTemplate || !input.trim()) return;
    setExecuting(true);
    setResult(null);

    try {
      // 走 DS 代理路由 → Gateway → Nebula（真实路径：/api/v1/workflow/execute）
      const res = await fetch('/api/v1/workflow/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ template_id: selectedTemplate, input: input.trim() }),
      });
      const data = await res.json();
      if (data.result || data.output) {
        const execResult = data.result || data.output;
        setResult(execResult);
        const newExec: WorkflowExecution = {
          id: `wf-${Date.now()}`,
          template_id: selectedTemplate,
          status: 'completed',
          input: input.trim(),
          result: execResult,
          started_at: new Date().toISOString(),
          finished_at: new Date().toISOString(),
        };
        if (!demoMode) {
          setExecutions(prev => [newExec, ...prev]);
        }
      } else {
        setResult(data.error || data.detail || '执行失败');
      }
    } catch (err) {
      if (demoMode) {
        setResult('演示模式：模拟执行成功（后端未连接）');
        const newExec: WorkflowExecution = {
          id: `wf-${Date.now()}`,
          template_id: selectedTemplate,
          status: 'completed',
          input: input.trim(),
          result: `[演示] 工作流 "${getTemplateName(selectedTemplate)}" 执行完成`,
          started_at: new Date().toISOString(),
          finished_at: new Date().toISOString(),
        };
        setExecutions(prev => [newExec, ...prev]);
      } else {
        setResult('请求错误: ' + (err instanceof Error ? err.message : '未知错误'));
      }
    } finally {
      setExecuting(false);
    }
  };

  const getTemplateName = (id: string) => templates.find(t => t.id === id)?.name || id;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <span className="badge badge-active">成功</span>;
      case 'running':
        return <span className="badge" style={{ background: 'rgba(245,158,11,0.1)', color: '#fbbf24' }}>执行中</span>;
      case 'failed':
        return <span className="badge" style={{ background: 'rgba(239,68,68,0.1)', color: '#ef4444' }}>失败</span>;
      default:
        return null;
    }
  };

  return (
    <AuthGuard>
      <TopBar title="工作流" subtitle="Agent 工作流编排与执行" />

      <div className="p-6">
        {demoMode && (
          <div className="max-w-5xl mx-auto mb-4">
            <div className="card" style={{ padding: '12px 20px', background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.15)' }}>
              <span className="text-xs" style={{ color: '#fbbf24' }}>演示模式 — 后端服务未连接，展示本地演示数据</span>
            </div>
          </div>
        )}
        <div className="max-w-5xl mx-auto space-y-6">

          {/* Workflow Templates */}
          <div className="card" style={{ padding: 24 }}>
            <div className="card-header" style={{ marginBottom: 16 }}>
              <span className="card-title">工作流模板</span>
              <span className="text-xs text-muted">{templates.length} 个可用模板</span>
            </div>

            {loading ? (
              <div style={{ textAlign: 'center', padding: 40 }}>
                <div style={{ fontSize: 24, marginBottom: 12, opacity: 0.4 }}>⚙</div>
                <p className="text-muted">加载模板中...</p>
              </div>
            ) : templates.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 40 }}>
                <div style={{ fontSize: 32, marginBottom: 12, opacity: 0.3 }}>📭</div>
                <p className="text-muted">暂无可用模板</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {templates.map((template) => (
                  <div
                    key={template.id}
                    className="p-5 rounded-xl cursor-pointer transition-all"
                    style={{
                      background: selectedTemplate === template.id ? 'linear-gradient(135deg, rgba(139,92,246,0.1), rgba(56,189,248,0.05))' : 'var(--bg-hover)',
                      border: selectedTemplate === template.id ? '1px solid rgba(139,92,246,0.25)' : '1px solid var(--border-color)',
                      boxShadow: selectedTemplate === template.id ? '0 0 20px rgba(139,92,246,0.08)' : 'none',
                      transform: selectedTemplate === template.id ? 'translateY(-2px)' : 'none',
                    }}
                    onClick={() => {
                      setSelectedTemplate(template.id);
                      setInput(template.examples[0] || '');
                      setResult(null);
                    }}
                  >
                    <div className="flex items-center gap-2.5 mb-3">
                      <div className="w-2.5 h-2.5 rounded-full" style={{
                        background: selectedTemplate === template.id ? 'var(--nebula)' : 'var(--text-muted)',
                        boxShadow: selectedTemplate === template.id ? '0 0 8px rgba(139,92,246,0.4)' : 'none',
                      }} />
                      <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>
                        {template.name}
                      </div>
                    </div>
                    <div className="text-xs mb-3" style={{ color: 'var(--text-muted)', lineHeight: 1.5 }}>
                      {template.description}
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {template.examples.slice(0, 2).map((ex, i) => (
                        <span key={i} style={{
                          fontSize: 10,
                          padding: '3px 10px',
                          borderRadius: 6,
                          background: 'var(--bg-active)',
                          color: 'var(--text-muted)',
                          border: '1px solid var(--border-color)',
                          fontFamily: "'JetBrains Mono', monospace",
                        }}>
                          {ex}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Execute Workflow */}
          {selectedTemplate && (
            <div className="card" style={{ padding: 24 }}>
              <div className="card-header" style={{ marginBottom: 16 }}>
                <span className="card-title">执行工作流</span>
                <span className="text-xs text-muted">
                  {templates.find(t => t.id === selectedTemplate)?.name}
                </span>
              </div>

              <div className="flex gap-3">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="输入工作流指令..."
                  className="flex-1 rounded-xl px-4 py-2.5 text-sm"
                  style={{
                    background: 'var(--bg-secondary)',
                    color: 'var(--text-primary)',
                    border: '1px solid var(--border-color)',
                  }}
                  onKeyDown={(e) => e.key === 'Enter' && !executing && executeWorkflow()}
                />
                <button
                  onClick={executeWorkflow}
                  disabled={executing || !input.trim()}
                  className="px-6 py-2.5 rounded-xl text-sm font-medium transition-all"
                  style={{
                    background: input.trim() && !executing ? 'rgba(139,92,246,0.15)' : 'var(--bg-hover)',
                    color: input.trim() && !executing ? 'var(--nebula-light)' : 'var(--text-muted)',
                    border: `1px solid ${input.trim() && !executing ? 'rgba(139,92,246,0.2)' : 'var(--border-color)'}`,
                    cursor: (executing || !input.trim()) ? 'not-allowed' : 'pointer',
                  }}
                >
                  {executing ? '执行中...' : '执行'}
                </button>
              </div>

              {result && (
                <div className="mt-4 p-4 rounded-xl text-sm" style={{
                  background: 'rgba(139,92,246,0.06)',
                  border: '1px solid rgba(139,92,246,0.12)',
                  color: 'var(--text-primary)',
                  whiteSpace: 'pre-wrap',
                }}>
                  {result}
                </div>
              )}
            </div>
          )}

          {/* Execution History */}
          <div className="card" style={{ padding: 24 }}>
            <div className="card-header" style={{ marginBottom: 16 }}>
              <span className="card-title">执行历史</span>
              <span className="text-xs text-muted">{executions.length} 条记录</span>
            </div>

            {loading ? (
              <div style={{ textAlign: 'center', padding: 40 }}>
                <div style={{ fontSize: 24, marginBottom: 12, opacity: 0.4 }}>⏳</div>
                <p className="text-muted">加载执行记录...</p>
              </div>
            ) : executions.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 40 }}>
                <div style={{ fontSize: 32, marginBottom: 12, opacity: 0.3 }}>📭</div>
                <p className="text-muted">暂无执行记录</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {executions.map((exec) => (
                  <div
                    key={exec.id}
                    className="p-4 rounded-xl transition-all"
                    style={{
                      background: 'var(--bg-hover)',
                      border: '1px solid var(--border-color)',
                    }}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1.5">
                          <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
                            {getTemplateName(exec.template_id)}
                          </span>
                          {getStatusBadge(exec.status)}
                        </div>
                        <div className="text-xs" style={{ color: 'var(--text-muted)', marginBottom: 4 }}>
                          输入: {exec.input}
                        </div>
                        {exec.result && (
                          <div className="text-xs" style={{ color: 'var(--text-secondary)', background: 'var(--bg-primary)', padding: '6px 10px', borderRadius: 6, border: '1px solid var(--border-color)' }}>
                            {exec.result}
                          </div>
                        )}
                      </div>
                      <div style={{ fontSize: 10, fontFamily: "'JetBrains Mono',monospace", color: 'var(--text-muted)', flexShrink: 0, paddingTop: 2 }}>
                        {new Date(exec.started_at).toLocaleString('zh-CN', {
                          month: 'short', day: 'numeric',
                          hour: '2-digit', minute: '2-digit'
                        })}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>
      </div>
    </AuthGuard>
  );
}
