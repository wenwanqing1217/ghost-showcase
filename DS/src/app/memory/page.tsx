'use client';

import { useState, useEffect } from 'react';
import TopBar from '@/components/layout/TopBar';
import AuthGuard from '@/components/layout/AuthGuard';
import { humanApi } from '@/lib/api';
import { DEMO_MEMORY_NODES } from '@/lib/demo-data';

interface MemoryNode {
  id: string;
  type: 'atom' | 'relation' | 'memory' | 'context';
  label: string;
  content?: string;
  timestamp?: string;
  connections: string[];
  source?: 'graph' | 'search';
}

interface MemoryGraph {
  nodes: MemoryNode[];
  edges?: unknown[];
  stats: {
    totalAtoms: number;
    totalRelations: number;
    totalMemories: number;
    layers: number;
  };
}

export default function MemoryPage() {
  const [graph, setGraph] = useState<MemoryGraph | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [selectedNode, setSelectedNode] = useState<MemoryNode | null>(null);
  const [identity, setIdentity] = useState<any>(null);
  const [isDemo, setIsDemo] = useState(false);

  useEffect(() => {
    loadMemoryGraph();
    humanApi.getIdentity().then(data => setIdentity(data)).catch((err) => console.warn('[MemoryPage] getIdentity error:', err));
  }, []);

  const loadMemoryGraph = async () => {
    setLoading(true);
    setIsDemo(false);
    try {
      const response = await humanApi.getMemoryGraph();
      const data = (response as any).data || response;
      const normalized: MemoryGraph = {
        nodes: data.nodes || [],
        edges: data.edges || [],
        stats: {
          totalAtoms: data.stats?.totalAtoms ?? data.stats?.atoms ?? 0,
          totalRelations: data.stats?.totalRelations ?? data.stats?.connections ?? 0,
          totalMemories: data.stats?.totalMemories ?? data.stats?.memories ?? 0,
          layers: data.stats?.layers ?? 1,
        },
      };
      setGraph(normalized);
    } catch (err) {
      console.warn('[MemoryPage] loadMemoryGraph fallback to demo data:', err);
      setIsDemo(true);
      setGraph({
        nodes: DEMO_MEMORY_NODES.map(n => ({ ...n, source: 'graph' as const })) as MemoryNode[],
        stats: {
          totalAtoms: DEMO_MEMORY_NODES.filter(n => n.type === 'atom').length,
          totalRelations: DEMO_MEMORY_NODES.filter(n => n.type === 'relation').length,
          totalMemories: DEMO_MEMORY_NODES.filter(n => n.type === 'memory').length,
          layers: 3,
        },
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const data = await humanApi.searchMemory(searchQuery);
      setSearchResults(((data as any)?.results || []) as any[]);
    } catch (err) {
      console.warn('[MemoryPage] searchMemory error:', err);
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'atom': return 'var(--nebula)';
      case 'relation': return 'var(--cosmic)';
      case 'memory': return '#a78bfa';
      case 'context': return 'var(--success)';
      default: return 'var(--text-muted)';
    }
  };

  const getNodeIcon = (type: string) => {
    switch (type) {
      case 'atom': return '○';
      case 'relation': return '◇';
      case 'memory': return '▽';
      case 'context': return '□';
      default: return '·';
    }
  };

  return (
    <AuthGuard>
      <TopBar title="记忆图谱" subtitle="因果图谱 + 三层记忆架构可视化" />
      <div className="p-6">
        <div className="max-w-6xl mx-auto">
          {/* 搜索栏 */}
          <div className="flex gap-2 mb-6">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="搜索知识链..."
              className="flex-1 rounded-xl px-4 py-2.5 text-sm"
              style={{
                background: 'var(--bg-secondary)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-color)',
              }}
            />
            <button
              onClick={handleSearch}
              disabled={searching || !searchQuery.trim()}
              className="px-4 py-2.5 rounded-xl text-sm font-medium transition-all"
              style={{
                background: searchQuery.trim() && !searching ? 'rgba(139,92,246,0.15)' : 'var(--bg-hover)',
                color: searchQuery.trim() && !searching ? 'var(--nebula-light)' : 'var(--text-muted)',
                border: `1px solid ${searchQuery.trim() && !searching ? 'rgba(139,92,246,0.2)' : 'var(--border-color)'}`,
                cursor: searchQuery.trim() && !searching ? 'pointer' : 'not-allowed',
              }}
            >
              {searching ? '搜索中...' : '搜索'}
            </button>
          </div>

          {/* 统计卡片 */}
          {isDemo && (
            <div className="p-3 rounded-xl mb-4" style={{
              background: 'rgba(245,158,11,0.08)',
              border: '1px solid rgba(245,158,11,0.15)',
            }}>
              <div className="text-xs" style={{ color: '#fbbf24' }}>
                ⚠ 当前为演示模式 — 记忆图谱服务未连接，显示的是示例数据
              </div>
            </div>
          )}
          {graph && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              {[
                { label: '原子点', value: graph.stats.totalAtoms, color: 'var(--nebula)' },
                { label: '连接关系', value: graph.stats.totalRelations, color: 'var(--cosmic)' },
                { label: '记忆条目', value: graph.stats.totalMemories, color: '#a78bfa' },
                { label: '记忆层数', value: graph.stats.layers, color: 'var(--success)' },
              ].map((stat, i) => (
                <div key={i} className="card" style={{ padding: 16, textAlign: 'center' }}>
                  <div style={{ fontSize: 28, fontWeight: 800, color: stat.color, marginBottom: 4 }}>
                    {stat.value}
                  </div>
                  <div className="text-muted" style={{ fontSize: 12 }}>{stat.label}</div>
                </div>
              ))}
            </div>
          )}

          {/* 搜索结果 */}
          {searchResults.length > 0 && (
            <div className="card mb-6">
              <div className="card-header">
                <span className="card-title">搜索结果 ({searchResults.length})</span>
              </div>
              <div style={{ padding: 16 }}>
                {searchResults.map((result, i) => (
                  <div
                    key={i}
                    className="mb-3 last:mb-0 p-3 rounded-lg cursor-pointer transition-all"
                    style={{
                      background: 'var(--bg-hover)',
                      border: '1px solid var(--border-color)',
                    }}
                    onClick={() => setSelectedNode({
                      id: `search-${i}-${Date.now()}`,
                      type: 'memory',
                      label: result.title || result.content?.slice(0, 50) || '记忆条目',
                      content: result.content || result.preview,
                      timestamp: result.modified || result.date,
                      connections: [],
                      source: 'search',
                    })}
                  >
                    <div className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                      {result.title || '未命名记忆'}
                    </div>
                    <div className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                      {(result.content || result.preview || '').slice(0, 150)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 记忆图谱可视化 */}
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <div className="card-header" style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-color)' }}>
              <span className="card-title">记忆图谱</span>
              <div className="flex items-center gap-2">
                {isDemo && (
                  <span className="text-xs px-2.5 py-1 rounded-lg" style={{
                    background: 'rgba(245,158,11,0.1)',
                    color: '#fbbf24',
                    border: '1px solid rgba(245,158,11,0.2)',
                  }}>
                    演示模式
                  </span>
                )}
                <button
                  onClick={loadMemoryGraph}
                  disabled={loading}
                  className="text-xs px-3 py-1.5 rounded-lg transition-all"
                  style={{
                    background: 'var(--bg-hover)',
                    color: loading ? 'var(--text-muted)' : 'var(--text-secondary)',
                    border: '1px solid var(--border-color)',
                    cursor: loading ? 'not-allowed' : 'pointer',
                  }}
                >
                  {loading ? '加载中...' : '刷新'}
                </button>
              </div>
            </div>
            <div style={{ padding: 20 }}>
              {loading ? (
                <div style={{ textAlign: 'center', padding: 40 }}>
                  <div style={{ fontSize: 24, marginBottom: 12, opacity: 0.4 }}>🔗</div>
                  <div className="text-muted">加载记忆图谱...</div>
                </div>
              ) : graph ? (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {graph.nodes.map((node) => (
                    <div
                      key={node.id}
                      className="p-4 rounded-xl cursor-pointer transition-all"
                      style={{
                        background: selectedNode?.id === node.id ? 'rgba(139,92,246,0.06)' : 'var(--bg-hover)',
                        border: `1px solid ${selectedNode?.id === node.id ? getNodeColor(node.type) : 'var(--border-color)'}`,
                        boxShadow: selectedNode?.id === node.id ? `0 0 16px ${getNodeColor(node.type)}22` : 'none',
                        transform: selectedNode?.id === node.id ? 'translateY(-1px)' : 'none',
                      }}
                      onClick={() => setSelectedNode({ ...node, source: 'graph' })}
                    >
                      <div className="text-2xl mb-2">{getNodeIcon(node.type)}</div>
                      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 3 }}>
                        {node.label}
                      </div>
                      <div className="text-xs" style={{ color: 'var(--text-muted)', lineHeight: 1.4 }}>
                        {node.content?.slice(0, 60)}{node.content?.length && node.content.length > 60 ? '...' : ''}
                      </div>
                      <div className="flex items-center gap-2 mt-3">
                        <span className="badge" style={{ fontSize: 10, background: `${getNodeColor(node.type)}15`, color: getNodeColor(node.type), border: `1px solid ${getNodeColor(node.type)}25` }}>
                          {node.type}
                        </span>
                        <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                          {node.connections.length} 连接
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: 40 }}>
                  <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 16 }}>
                    <div style={{
                      width: 56, height: 56,
                      borderRadius: '50%',
                      background: 'radial-gradient(circle at 40% 35%, rgba(139,92,246,0.6) 0%, rgba(56,189,248,0.2) 60%, transparent 100%)',
                      filter: 'blur(8px)',
                    }} />
                  </div>
                  <div className="text-muted">暂无记忆数据</div>
                </div>
              )}
            </div>
          </div>

          {/* 节点详情 — 搜索 vs 图谱来源清晰区分 */}
          {selectedNode && (
            <div className="card mt-6">
              <div className="card-header">
                <span className="card-title">
                  {selectedNode.source === 'search' ? '搜索结果详情' : '图谱节点详情'}
                </span>
                <button
                  onClick={() => setSelectedNode(null)}
                  className="text-xs px-3 py-1.5 rounded-lg"
                  style={{
                    background: 'var(--bg-hover)',
                    color: 'var(--text-muted)',
                    border: '1px solid var(--border-color)',
                  }}
                >
                  关闭
                </button>
              </div>
              <div style={{ padding: 20 }}>
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-muted" style={{ minWidth: 60 }}>ID</span>
                    <span className="text-sm font-mono" style={{ color: 'var(--text-primary)' }}>{selectedNode.id}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-muted" style={{ minWidth: 60 }}>类型</span>
                    <span className="badge" style={{
                      background: selectedNode.source === 'search'
                        ? 'rgba(245,158,11,0.12)'
                        : undefined,
                      color: selectedNode.source === 'search' ? '#fbbf24' : undefined,
                    }}>
                      {selectedNode.type}
                      {selectedNode.source === 'search' && ' (搜索)'}
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-muted" style={{ minWidth: 60 }}>标签</span>
                    <span className="text-sm" style={{ color: 'var(--text-primary)' }}>{selectedNode.label}</span>
                  </div>
                  {selectedNode.source === 'search' ? (
                    <div>
                      <span className="text-xs text-muted block mb-1">摘要</span>
                      <div className="text-sm p-3 rounded-lg" style={{ background: 'var(--bg-hover)', color: 'var(--text-primary)' }}>
                        {selectedNode.content}
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-muted" style={{ minWidth: 60 }}>连接数</span>
                        <span className="text-sm" style={{ color: 'var(--text-primary)' }}>{selectedNode.connections.length}</span>
                      </div>
                      {selectedNode.content && (
                        <div>
                          <span className="text-xs text-muted block mb-1">内容</span>
                          <div className="text-sm p-3 rounded-lg" style={{ background: 'var(--bg-hover)', color: 'var(--text-primary)' }}>
                            {selectedNode.content}
                          </div>
                        </div>
                      )}
                    </>
                  )}
                  {selectedNode.timestamp && (
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-muted" style={{ minWidth: 60 }}>时间</span>
                      <span className="text-sm" style={{ color: 'var(--text-muted)' }}>
                        {new Date(selectedNode.timestamp).toLocaleString('zh-CN')}
                      </span>
                    </div>
                  )}
                  {selectedNode.source === 'graph' && selectedNode.connections.length > 0 && (
                    <div>
                      <span className="text-xs text-muted block mb-2">关联节点</span>
                      <div className="flex flex-wrap gap-2">
                        {selectedNode.connections.map((conn, ci) => (
                          <span key={ci} className="text-xs px-2 py-1 rounded-md" style={{
                            background: 'var(--bg-hover)',
                            color: 'var(--text-muted)',
                            border: '1px solid var(--border-color)',
                          }}>
                            {conn}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </AuthGuard>
  );
}
