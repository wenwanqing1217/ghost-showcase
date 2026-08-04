'use client';

import TopBar from '@/components/layout/TopBar';
import AuthGuard from '@/components/layout/AuthGuard';
import { useEffect, useState } from 'react';

export default function ToolsPage() {
  const [activeTab, setActiveTab] = useState<'generate' | 'optimize'>('generate');
  const [requirement, setRequirement] = useState('');
  const [language, setLanguage] = useState('python');
  const [code, setCode] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateCode = async () => {
    if (!requirement.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch('/api/v1/tools/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requirement, task_id: `gen-${Date.now()}`, language }),
      });
      const data = await res.json();
      if (data.success) {
        setResult(data.data);
        setCode(data.data.code || '');
      } else {
        setError(data.error || data.data?._error || '生成失败');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : '请求失败');
    } finally {
      setLoading(false);
    }
  };

  const optimizeCode = async () => {
    if (!code.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch('/api/v1/tools/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          requirement,
          task_id: `opt-${Date.now()}`,
          tool_a_result: { code, status: 'generated' },
        }),
      });
      const data = await res.json();
      if (data.success) {
        setResult(data.data);
      } else {
        setError(data.error || data.data?._error || '优化失败');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : '请求失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthGuard>
      <TopBar title="AI 工具" subtitle="ToolA 代码生成 · ToolB 代码优化" />
      <div className="p-6">
        <div className="max-w-5xl mx-auto">
          {/* 服务状态 */}
          <div className="card mb-6" style={{ padding: 20 }}>
            <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 8 }}>服务状态</div>
            <div style={{ display: 'flex', gap: 24, fontSize: 13, color: 'var(--text-secondary)' }}>
              <span>ToolA (代码生成): <strong style={{ color: 'var(--text-primary)' }}>8081</strong></span>
              <span>ToolB (代码优化): <strong style={{ color: 'var(--text-primary)' }}>8082</strong></span>
            </div>
          </div>

          {/* 标签切换 */}
          <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
            <button
              onClick={() => { setActiveTab('generate'); setResult(null); setError(null); }}
              style={{
                padding: '8px 20px',
                borderRadius: 8,
                border: '1px solid var(--border-color)',
                background: activeTab === 'generate' ? 'var(--primary-color)' : 'transparent',
                color: activeTab === 'generate' ? '#fff' : 'var(--text-primary)',
                cursor: 'pointer',
                fontSize: 13,
              }}
            >
              代码生成
            </button>
            <button
              onClick={() => { setActiveTab('optimize'); setResult(null); setError(null); }}
              style={{
                padding: '8px 20px',
                borderRadius: 8,
                border: '1px solid var(--border-color)',
                background: activeTab === 'optimize' ? 'var(--primary-color)' : 'transparent',
                color: activeTab === 'optimize' ? '#fff' : 'var(--text-primary)',
                cursor: 'pointer',
                fontSize: 13,
              }}
            >
              代码优化
            </button>
          </div>

          {/* 代码生成面板 */}
          {activeTab === 'generate' && (
            <div className="card" style={{ padding: 20 }}>
              <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 12 }}>需求描述</div>
              <textarea
                value={requirement}
                onChange={(e) => setRequirement(e.target.value)}
                placeholder="描述你想要生成的代码，例如：Create a Python FastAPI hello world endpoint"
                style={{
                  width: '100%',
                  minHeight: 100,
                  padding: 12,
                  borderRadius: 8,
                  border: '1px solid var(--border-color)',
                  background: 'var(--bg-secondary)',
                  color: 'var(--text-primary)',
                  fontSize: 13,
                  fontFamily: 'monospace',
                  resize: 'vertical',
                }}
              />
              <div style={{ display: 'flex', gap: 12, marginTop: 12, alignItems: 'center' }}>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  style={{
                    padding: '6px 12px',
                    borderRadius: 6,
                    border: '1px solid var(--border-color)',
                    background: 'var(--bg-secondary)',
                    color: 'var(--text-primary)',
                    fontSize: 13,
                  }}
                >
                  <option value="python">Python</option>
                  <option value="javascript">JavaScript</option>
                  <option value="typescript">TypeScript</option>
                  <option value="go">Go</option>
                  <option value="rust">Rust</option>
                </select>
                <button
                  onClick={generateCode}
                  disabled={loading || !requirement.trim()}
                  style={{
                    padding: '8px 24px',
                    borderRadius: 8,
                    border: 'none',
                    background: loading ? 'var(--text-muted)' : 'var(--primary-color)',
                    color: '#fff',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    fontSize: 13,
                    fontWeight: 500,
                  }}
                >
                  {loading ? '生成中...' : '生成代码'}
                </button>
              </div>
            </div>
          )}

          {/* 代码优化面板 */}
          {activeTab === 'optimize' && (
            <div className="card" style={{ padding: 20 }}>
              <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 12 }}>原始代码</div>
              <textarea
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="粘贴需要优化的代码..."
                style={{
                  width: '100%',
                  minHeight: 200,
                  padding: 12,
                  borderRadius: 8,
                  border: '1px solid var(--border-color)',
                  background: 'var(--bg-secondary)',
                  color: 'var(--text-primary)',
                  fontSize: 13,
                  fontFamily: 'monospace',
                  resize: 'vertical',
                }}
              />
              <div style={{ marginTop: 12 }}>
                <button
                  onClick={optimizeCode}
                  disabled={loading || !code.trim()}
                  style={{
                    padding: '8px 24px',
                    borderRadius: 8,
                    border: 'none',
                    background: loading ? 'var(--text-muted)' : 'var(--primary-color)',
                    color: '#fff',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    fontSize: 13,
                    fontWeight: 500,
                  }}
                >
                  {loading ? '优化中...' : '优化代码'}
                </button>
              </div>
            </div>
          )}

          {/* 结果展示 */}
          {result && (
            <div className="card mt-4" style={{ padding: 20 }}>
              <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 12 }}>
                结果 <span style={{ color: 'var(--text-muted)', fontSize: 12, marginLeft: 8 }}>
                  status: {result.status || 'ok'}
                </span>
              </div>
              {result.code && (
                <pre style={{
                  padding: 16,
                  borderRadius: 8,
                  background: 'var(--bg-secondary)',
                  color: 'var(--text-primary)',
                  fontSize: 12,
                  fontFamily: 'monospace',
                  overflow: 'auto',
                  maxHeight: 400,
                  whiteSpace: 'pre-wrap',
                }}>
                  {result.code}
                </pre>
              )}
              {result.optimized_code && result.optimized_code !== result.original_code && (
                <>
                  <div style={{ fontWeight: 600, fontSize: 13, marginTop: 16, marginBottom: 8 }}>优化后代码</div>
                  <pre style={{
                    padding: 16,
                    borderRadius: 8,
                    background: 'var(--bg-secondary)',
                    color: 'var(--text-primary)',
                    fontSize: 12,
                    fontFamily: 'monospace',
                    overflow: 'auto',
                    maxHeight: 400,
                    whiteSpace: 'pre-wrap',
                  }}>
                    {result.optimized_code}
                  </pre>
                </>
              )}
              {result.suggestions && result.suggestions.length > 0 && (
                <div style={{ marginTop: 12 }}>
                  <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8 }}>建议</div>
                  <ul style={{ paddingLeft: 20, fontSize: 13, color: 'var(--text-secondary)' }}>
                    {result.suggestions.map((s: string, i: number) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* 错误展示 */}
          {error && (
            <div className="card mt-4" style={{ padding: 20, borderColor: '#ef4444' }}>
              <div style={{ color: '#ef4444', fontSize: 13 }}>{error}</div>
            </div>
          )}
        </div>
      </div>
    </AuthGuard>
  );
}
