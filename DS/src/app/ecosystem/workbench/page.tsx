'use client';

import TopBar from '@/components/layout/TopBar';
import AuthGuard from '@/components/layout/AuthGuard';
import { useEffect, useState } from 'react';

interface TaskItem {
  id: string;
  title: string;
  status: 'pending' | 'running' | 'completed';
  priority: 'high' | 'medium' | 'low';
}

interface NoteItem {
  id: string;
  title: string;
  content: string;
  updated_at: string;
}

export default function WorkbenchPage() {
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [notes, setNotes] = useState<NoteItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activePanel, setActivePanel] = useState<'tasks' | 'notes' | 'canvas'>('tasks');
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [newNoteTitle, setNewNoteTitle] = useState('');
  const [newNoteContent, setNewNoteContent] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch tasks from orchestrator
        const taskRes = await fetch('/api/v1/internal/orchestrator/tasks?limit=10', {
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (taskRes.ok) {
          const data = await taskRes.json();
          const taskList = (data.data?.tasks || []).map((t: any) => ({
            id: t.id,
            title: t.requirement?.slice(0, 50) || 'Untitled Task',
            status: t.status || 'pending',
            priority: 'medium' as const,
          }));
          setTasks(taskList.slice(0, 5));
        }

        // Fetch notes from memory
        const noteRes = await fetch('/api/v1/human/memory/search?keyword=&limit=10', {
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (noteRes.ok) {
          const data = await noteRes.json();
          const noteList = (data.data?.results || []).map((r: any) => ({
            id: r.memory_id || r.id,
            title: r.content?.slice(0, 30) || 'Untitled Note',
            content: r.content || '',
            updated_at: r.timestamp || new Date().toISOString(),
          }));
          setNotes(noteList.slice(0, 5));
        }
      } catch (e) {
        console.error('Workbench data fetch error:', e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const addTask = async () => {
    if (!newTaskTitle.trim()) return;
    try {
      const res = await fetch('/api/v1/internal/orchestrator/task/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
        body: JSON.stringify({ requirement: newTaskTitle, mode: 'serial' }),
      });
      if (res.ok) {
        const data = await res.json();
        setTasks((prev) => [...prev, {
          id: data.task_id,
          title: newTaskTitle.slice(0, 50),
          status: 'pending',
          priority: 'medium',
        }]);
        setNewTaskTitle('');
      }
    } catch (e) {
      console.error('Add task error:', e);
    }
  };

  const addNote = async () => {
    if (!newNoteTitle.trim()) return;
    try {
      const res = await fetch('/api/v1/human/memory/store', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
        body: JSON.stringify({
          content: newNoteContent || newNoteTitle,
          category: 'workbench',
          tags: ['workbench-note'],
          source: 'workbench',
        }),
      });
      if (res.ok) {
        setNotes((prev) => [...prev, {
          id: Date.now().toString(),
          title: newNoteTitle.slice(0, 30),
          content: newNoteContent,
          updated_at: new Date().toISOString(),
        }]);
        setNewNoteTitle('');
        setNewNoteContent('');
      }
    } catch (e) {
      console.error('Add note error:', e);
    }
  };

  const statusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'badge-active';
      case 'running': return 'badge-paid';
      default: return 'badge-pending';
    }
  };

  return (
    <AuthGuard>
      <TopBar title="个人工作台" subtitle="你的数字灵魂 · 思维画布 · 任务板 · 笔记" />
      <div className="p-6">
        <div className="max-w-5xl mx-auto">
          {/* 面板切换 */}
          <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
            {[
              { key: 'tasks', label: '任务板', icon: '📋' },
              { key: 'notes', label: '笔记', icon: '📝' },
              { key: 'canvas', label: '思维画布', icon: '🧠' },
            ].map((panel) => (
              <button
                key={panel.key}
                onClick={() => setActivePanel(panel.key as any)}
                style={{
                  padding: '8px 20px',
                  borderRadius: 8,
                  border: '1px solid var(--border-color)',
                  background: activePanel === panel.key ? 'var(--primary-color)' : 'transparent',
                  color: activePanel === panel.key ? '#fff' : 'var(--text-primary)',
                  cursor: 'pointer',
                  fontSize: 13,
                }}
              >
                {panel.icon} {panel.label}
              </button>
            ))}
          </div>

          {/* 任务板 */}
          {activePanel === 'tasks' && (
            <div className="card" style={{ padding: 20 }}>
              <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 12 }}>任务板</div>
              <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
                <input
                  value={newTaskTitle}
                  onChange={(e) => setNewTaskTitle(e.target.value)}
                  placeholder="输入新任务..."
                  style={{
                    flex: 1,
                    padding: '8px 12px',
                    borderRadius: 6,
                    border: '1px solid var(--border-color)',
                    background: 'var(--bg-secondary)',
                    color: 'var(--text-primary)',
                    fontSize: 13,
                  }}
                />
                <button
                  onClick={addTask}
                  disabled={!newTaskTitle.trim()}
                  style={{
                    padding: '8px 16px',
                    borderRadius: 6,
                    border: 'none',
                    background: 'var(--primary-color)',
                    color: '#fff',
                    cursor: 'pointer',
                    fontSize: 13,
                  }}
                >
                  添加
                </button>
              </div>
              {loading ? (
                <p className="text-muted" style={{ fontSize: 13 }}>加载中...</p>
              ) : tasks.length === 0 ? (
                <p className="text-muted" style={{ fontSize: 13 }}>暂无任务，添加一个开始吧</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {tasks.map((task) => (
                    <div key={task.id} style={{
                      padding: '10px 14px',
                      borderRadius: 8,
                      background: 'var(--bg-secondary)',
                      border: '1px solid var(--border)',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}>
                      <span style={{ fontSize: 13, color: 'var(--text-primary)' }}>{task.title}</span>
                      <span className={`badge ${statusColor(task.status)}`}>{task.status}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 笔记 */}
          {activePanel === 'notes' && (
            <div className="card" style={{ padding: 20 }}>
              <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 12 }}>笔记</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 12 }}>
                <input
                  value={newNoteTitle}
                  onChange={(e) => setNewNoteTitle(e.target.value)}
                  placeholder="笔记标题..."
                  style={{
                    padding: '8px 12px',
                    borderRadius: 6,
                    border: '1px solid var(--border-color)',
                    background: 'var(--bg-secondary)',
                    color: 'var(--text-primary)',
                    fontSize: 13,
                  }}
                />
                <textarea
                  value={newNoteContent}
                  onChange={(e) => setNewNoteContent(e.target.value)}
                  placeholder="笔记内容..."
                  rows={3}
                  style={{
                    padding: 12,
                    borderRadius: 6,
                    border: '1px solid var(--border-color)',
                    background: 'var(--bg-secondary)',
                    color: 'var(--text-primary)',
                    fontSize: 13,
                    resize: 'vertical',
                  }}
                />
                <button
                  onClick={addNote}
                  disabled={!newNoteTitle.trim()}
                  style={{
                    padding: '8px 16px',
                    borderRadius: 6,
                    border: 'none',
                    background: 'var(--primary-color)',
                    color: '#fff',
                    cursor: 'pointer',
                    fontSize: 13,
                    alignSelf: 'flex-end',
                  }}
                >
                  保存笔记
                </button>
              </div>
              {loading ? (
                <p className="text-muted" style={{ fontSize: 13 }}>加载中...</p>
              ) : notes.length === 0 ? (
                <p className="text-muted" style={{ fontSize: 13 }}>暂无笔记</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {notes.map((note) => (
                    <div key={note.id} style={{
                      padding: '10px 14px',
                      borderRadius: 8,
                      background: 'var(--bg-secondary)',
                      border: '1px solid var(--border)',
                    }}>
                      <div style={{ fontWeight: 500, fontSize: 13, marginBottom: 4 }}>{note.title}</div>
                      <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{note.content.slice(0, 100)}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 思维画布 */}
          {activePanel === 'canvas' && (
            <div className="card" style={{ padding: 20 }}>
              <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 12 }}>思维画布</div>
              <div style={{
                height: 400,
                borderRadius: 8,
                background: 'var(--bg-secondary)',
                border: '1px dashed var(--border-color)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--text-muted)',
                fontSize: 13,
              }}>
                🧠 思维画布 — 拖拽节点构建知识网络（即将上线）
              </div>
            </div>
          )}
        </div>
      </div>
    </AuthGuard>
  );
}
