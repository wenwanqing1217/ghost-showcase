'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import GhostSprite from '@/components/shared/GhostSprite';

interface Thread {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  time: string;
  id: string;
}

export default function DoubaoBridgePage() {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [searching, setSearching] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [gwStatus, setGwStatus] = useState<{ ok: boolean } | null>(null);
  const [demoMode, setDemoMode] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const activeThread = threads.find(t => t.id === activeThreadId);

  useEffect(() => {
    if (threads.length === 0) createThread();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activeThread?.messages.length]);

  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch('/api/doubao');
        const data = await res.json();
        const ok = data.ok;
        setGwStatus({ ok });
        setDemoMode(!ok);
      } catch {
        setGwStatus({ ok: false });
        setDemoMode(true);
      }
    };
    check();
    const interval = setInterval(check, 30000);
    return () => clearInterval(interval);
  }, []);

  const createThread = useCallback((title?: string) => {
    const newThread: Thread = {
      id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
      title: title || '记忆桥对话',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };
    setThreads(prev => [newThread, ...prev]);
    setActiveThreadId(newThread.id);
  }, []);

  const deleteThread = useCallback((id: string) => {
    let newActiveId: string | null = null;
    setThreads(prev => {
      const filtered = prev.filter(t => t.id !== id);
      if (filtered.length === 0) {
        newActiveId = null;
        return filtered;
      }
      if (activeThreadId === id) {
        newActiveId = filtered[0].id;
      }
      return filtered;
    });
    if (newActiveId) {
      setActiveThreadId(newActiveId);
    } else {
      createThread();
    }
  }, [activeThreadId, createThread]);

  const sendMessage = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || sending || !activeThreadId) return;

    const userMsg: ChatMessage = {
      role: 'user',
      content: input.trim(),
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      id: Date.now().toString(36),
    };

    setInput('');
    setSending(true);

    setThreads(prev => prev.map(t =>
      t.id === activeThreadId && t.messages.length === 0
        ? { ...t, title: input.trim().slice(0, 24) + (input.trim().length > 24 ? '...' : ''), messages: [...t.messages, userMsg], updatedAt: Date.now() }
        : t.id === activeThreadId
          ? { ...t, messages: [...t.messages, userMsg], updatedAt: Date.now() }
          : t
    ));

    try {
      if (demoMode) {
        await new Promise(r => setTimeout(r, 600 + Math.random() * 400));
        const replies = [
          '离线模式：Gateway 未连接，本地模拟回复。连接恢复后将使用完整记忆链。',
          '当前处于离线演示模式。消息已记录，待 Gateway 恢复后同步。',
        ];
        const reply = replies[Math.floor(Math.random() * replies.length)];
        const assistantMsg: ChatMessage = {
          role: 'assistant', content: reply,
          time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
          id: Date.now().toString(36),
        };
        setThreads(prev => prev.map(t => t.id === activeThreadId ? { ...t, messages: [...t.messages, assistantMsg] } : t));
        return;
      }
      const res = await fetch('/api/doubao', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ alpha_id: 'Alpha-001', message: userMsg.content }),
      });
      const data = await res.json();
      const reply = data?.data?.reply || data?.reply || data?.error || '无回复';

      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: reply,
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
        id: Date.now().toString(36),
      };

      setThreads(prev => prev.map(t =>
        t.id === activeThreadId
          ? { ...t, messages: [...t.messages, assistantMsg], updatedAt: Date.now() }
          : t
      ));
    } catch {
      const errMsg: ChatMessage = {
        role: 'assistant',
        content: '请求失败，请检查 Gateway 连接',
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
        id: Date.now().toString(36),
      };
      setThreads(prev => prev.map(t =>
        t.id === activeThreadId
          ? { ...t, messages: [...t.messages, errMsg], updatedAt: Date.now() }
          : t
      ));
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  };

  const searchMemories = async () => {
    const q = prompt('搜索知识链关键词:');
    if (!q || !activeThreadId) return;

    setSearching(true);
    const searchMsg: ChatMessage = {
      role: 'user',
      content: `搜索: ${q}`,
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      id: Date.now().toString(36),
    };

    setThreads(prev => prev.map(t =>
      t.id === activeThreadId
        ? { ...t, messages: [...t.messages, searchMsg], updatedAt: Date.now() }
        : t
    ));

    try {
      const res = await fetch('/api/doubao', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ alpha_id: 'Alpha-001', message: `搜索知识链: ${q}` }),
      });
      const data = await res.json();
      const reply = data?.data?.reply || data?.reply || '无结果';

      const resultMsg: ChatMessage = {
        role: 'assistant',
        content: reply,
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
        id: Date.now().toString(36),
      };

      setThreads(prev => prev.map(t =>
        t.id === activeThreadId
          ? { ...t, messages: [...t.messages, resultMsg], updatedAt: Date.now() }
          : t
      ));
    } catch {
      const errMsg: ChatMessage = {
        role: 'assistant',
        content: '搜索失败',
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
        id: Date.now().toString(36),
      };
      setThreads(prev => prev.map(t =>
        t.id === activeThreadId
          ? { ...t, messages: [...t.messages, errMsg], updatedAt: Date.now() }
          : t
      ));
    } finally {
      setSearching(false);
    }
  };

  const formatTime = (ts: number) => {
    const d = new Date(ts);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    if (diff < 60000) return '刚刚';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
    return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
  };

  return (
    <div className="flex flex-col" style={{ height: 'calc(100vh - 60px)' }}>
      {/* 离线模式横幅 */}
      {demoMode && (
        <div className="animate-slide-up" style={{
          padding: '8px 16px',
          background: 'rgba(245,158,11,0.06)',
          borderBottom: '1px solid rgba(245,158,11,0.12)',
          color: 'var(--warning)',
          fontSize: 12,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}>
          <span style={{
            width: 6, height: 6,
            borderRadius: '50%',
            background: 'var(--warning)',
            opacity: 0.7,
          }} />
          离线演示模式：Gateway 未连接，消息以本地模拟运行。
        </div>
      )}

      <div className="flex flex-1 min-h-0">
        {/* ── 左侧对话列表 ── */}
      <div
        className="flex flex-col border-r"
        style={{
          width: sidebarOpen ? 260 : 0,
          minWidth: sidebarOpen ? 260 : 0,
          background: 'var(--bg-secondary)',
          borderColor: 'var(--border-color)',
          overflow: 'hidden',
          transition: 'width 0.3s ease, min-width 0.3s ease',
        }}
      >
        <div className="p-3" style={{ borderBottom: '1px solid var(--border-color)' }}>
          <button
            onClick={() => createThread()}
            className="w-full flex items-center justify-center gap-2 py-2 rounded-lg text-sm transition-all"
            style={{
              background: 'rgba(139,92,246,0.1)',
              color: 'var(--nebula-light)',
              border: '1px solid rgba(139,92,246,0.15)',
            }}
          >
            <span style={{ fontSize: 16 }}>+</span>
            <span>新对话</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto py-1">
          {threads.map(thread => (
            <div
              key={thread.id}
              className="mx-2 mb-0.5 rounded-lg cursor-pointer transition-all"
              style={{
                padding: '10px 12px',
                background: thread.id === activeThreadId ? 'rgba(139,92,246,0.08)' : 'transparent',
                border: thread.id === activeThreadId ? '1px solid rgba(139,92,246,0.12)' : '1px solid transparent',
              }}
              onClick={() => setActiveThreadId(thread.id)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div
                    className="text-sm truncate"
                    style={{
                      color: thread.id === activeThreadId ? 'var(--text-primary)' : 'var(--text-secondary)',
                      fontWeight: thread.id === activeThreadId ? 500 : 400,
                    }}
                  >
                    {thread.title}
                  </div>
                  <div className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
                    {thread.messages.length > 0
                      ? thread.messages[thread.messages.length - 1].content.slice(0, 30) + '...'
                      : '空对话'}
                  </div>
                </div>
                <div className="flex items-center gap-1 ml-2">
                  <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                    {formatTime(thread.updatedAt)}
                  </span>
                  {threads.length > 1 && (
                    <button
                      onClick={(e) => { e.stopPropagation(); deleteThread(thread.id); }}
                      className="text-xs px-1 rounded"
                      style={{ color: 'var(--text-muted)' }}
                    >
                      ×
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* 底部状态 */}
        <div className="p-3" style={{ borderTop: '1px solid var(--border-color)' }}>
          <div className="flex items-center gap-2">
            <GhostSprite size={24} />
            <div>
              <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                Gateway: {gwStatus?.ok ? '正常' : '异常'}
              </div>
              <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
                {threads.length} 个对话
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── 右侧对话区 ── */}
      <div className="flex-1 flex flex-col min-w-0">
        {activeThread ? (
          <>
            {/* 顶部栏 */}
            <div
              className="flex items-center justify-between px-4"
              style={{
                height: 48,
                borderBottom: '1px solid var(--border-color)',
                background: 'rgba(12,12,24,0.6)',
              }}
            >
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setSidebarOpen(!sidebarOpen)}
                  className="px-2 py-1 rounded transition-colors"
                  style={{ color: 'var(--text-muted)', fontSize: 14 }}
                >
                  {sidebarOpen ? '◁' : '▷'}
                </button>
                <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                  {activeThread.title}
                </span>
                <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                  {activeThread.messages.length} 条
                </span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={searchMemories}
                  disabled={searching}
                  className="px-3 py-1.5 rounded-lg text-xs transition-all"
                  style={{
                    background: 'rgba(255,255,255,0.04)',
                    color: 'var(--text-secondary)',
                    border: '1px solid var(--border-color)',
                  }}
                >
                  {searching ? '搜索中...' : '搜索知识链'}
                </button>
                <a
                  href="https://www.doubao.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-3 py-1.5 rounded-lg text-xs transition-all"
                  style={{
                    background: 'rgba(139,92,246,0.1)',
                    color: 'var(--nebula-light)',
                    border: '1px solid rgba(139,92,246,0.15)',
                  }}
                >
                  打开豆包
                </a>
              </div>
            </div>

            {/* 消息区 */}
            <div className="flex-1 overflow-y-auto px-6 py-4" style={{ background: 'var(--bg-primary)' }}>
              {activeThread.messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full">
                  <GhostSprite size={64} mood="idle" />
                  <div className="mt-6 text-center">
                    <div className="text-lg mb-2" style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
                      记忆桥已连接
                    </div>
                    <div className="text-sm" style={{ color: 'var(--text-muted)' }}>
                      与豆包对话，知识链自动同步
                    </div>
                  </div>
                  <div className="flex gap-2 mt-6">
                    {['今天的会议记录', '产品需求变更', '客户反馈汇总'].map((suggestion) => (
                      <button
                        key={suggestion}
                        onClick={() => setInput(suggestion)}
                        className="px-3 py-1.5 rounded-full text-xs transition-all"
                        style={{
                          background: 'rgba(255,255,255,0.04)',
                          color: 'var(--text-secondary)',
                          border: '1px solid var(--border-color)',
                        }}
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="max-w-3xl mx-auto space-y-4">
                  {activeThread.messages.map((msg) => (
                    <div
                      key={msg.id}
                      className="flex gap-3 animate-message-in"
                      style={{ flexDirection: msg.role === 'user' ? 'row-reverse' : 'row' }}
                    >
                      <div
                        className="rounded-full flex-shrink-0 flex items-center justify-center"
                        style={{
                          width: 32,
                          height: 32,
                          background: msg.role === 'user'
                            ? 'rgba(139,92,246,0.15)'
                            : 'rgba(56,189,248,0.08)',
                          border: msg.role === 'user'
                            ? '1px solid rgba(139,92,246,0.2)'
                            : '1px solid rgba(56,189,248,0.12)',
                        }}
                      >
                        {msg.role === 'user' ? (
                          <div style={{
                            width: 16, height: 16,
                            borderRadius: '50%',
                            background: 'rgba(139,92,246,0.4)',
                            border: '1px solid rgba(139,92,246,0.3)',
                          }} />
                        ) : (
                          <div style={{
                            width: 16, height: 16,
                            borderRadius: '50%',
                            background: 'rgba(56,189,248,0.3)',
                            border: '1px solid rgba(56,189,248,0.2)',
                          }} />
                        )}
                      </div>

                      <div
                        className="rounded-2xl px-4 py-2.5 max-w-[75%]"
                        style={{
                          background: msg.role === 'user'
                            ? 'rgba(139,92,246,0.1)'
                            : 'rgba(255,255,255,0.03)',
                          border: msg.role === 'user'
                            ? '1px solid rgba(139,92,246,0.12)'
                            : '1px solid var(--border-color)',
                        }}
                      >
                        <div
                          className="text-sm leading-relaxed"
                          style={{
                            color: 'var(--text-primary)',
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-word',
                          }}
                        >
                          {msg.content}
                        </div>
                        <div
                          className="text-xs mt-1.5"
                          style={{
                            color: 'var(--text-muted)',
                            textAlign: msg.role === 'user' ? 'right' : 'left',
                          }}
                        >
                          {msg.time}
                        </div>
                      </div>
                    </div>
                  ))}
                  {sending && (
                    <div className="flex gap-3">
                      <div className="rounded-full flex-shrink-0 flex items-center justify-center"
                        style={{ width: 32, height: 32, background: 'rgba(56,189,248,0.08)', border: '1px solid rgba(56,189,248,0.12)' }}>
                        <div style={{
                          width: 12, height: 12,
                          borderRadius: '50%',
                          background: 'rgba(56,189,248,0.5)',
                          border: '1px solid rgba(56,189,248,0.3)',
                        }} />
                      </div>
                      <div className="rounded-2xl px-4 py-3"
                        style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)' }}>
                        <div className="flex gap-1">
                          {[0, 1, 2].map(i => (
                            <div key={i} className="rounded-full"
                              style={{
                                width: 6, height: 6,
                                background: 'var(--cosmic)',
                                animation: `sprite-loading 1.2s ease-in-out infinite`,
                                animationDelay: `${i * 0.2}s`,
                              }} />
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>

            {/* 输入栏 */}
            <div
              className="px-4 py-3"
              style={{
                borderTop: '1px solid var(--border-color)',
                background: 'rgba(12,12,24,0.8)',
              }}
            >
              <form onSubmit={sendMessage} className="max-w-3xl mx-auto">
                <div className="flex gap-2">
                  <input
                    ref={inputRef}
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="输入消息，或搜索知识链..."
                    disabled={sending}
                    className="flex-1 rounded-xl px-4 py-2.5 text-sm transition-all"
                    style={{
                      background: 'rgba(255,255,255,0.04)',
                      color: 'var(--text-primary)',
                      border: '1px solid var(--border-color)',
                      outline: 'none',
                      transition: 'all 0.2s ease',
                    }}
                    onFocus={(e) => {
                      e.currentTarget.style.borderColor = 'rgba(56,189,248,0.3)';
                      e.currentTarget.style.boxShadow = '0 0 0 3px rgba(56,189,248,0.05)';
                    }}
                    onBlur={(e) => {
                      e.currentTarget.style.borderColor = 'var(--border-color)';
                      e.currentTarget.style.boxShadow = 'none';
                    }}
                  />
                  <button
                    type="submit"
                    disabled={sending || !input.trim()}
                    className="px-4 py-2.5 rounded-xl text-sm font-medium transition-all"
                    style={{
                      background: input.trim() && !sending
                        ? 'rgba(56,189,248,0.12)'
                        : 'rgba(255,255,255,0.04)',
                      color: input.trim() && !sending ? 'var(--cosmic-light)' : 'var(--text-muted)',
                      border: `1px solid ${input.trim() && !sending ? 'rgba(56,189,248,0.2)' : 'var(--border-color)'}`,
                      cursor: input.trim() && !sending ? 'pointer' : 'not-allowed',
                    }}
                  >
                    发送
                  </button>
                </div>
              </form>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center animate-fade-in">
              <GhostSprite size={48} mood="idle" />
              <div className="mt-4 text-sm" style={{ color: 'var(--text-muted)' }}>
                选择或创建对话
              </div>
            </div>
          </div>
        )}
      </div>
      </div>

      <style jsx>{`
        @keyframes sprite-loading {
          0%, 100% { opacity: 0.3; transform: scale(0.8); }
          50% { opacity: 1; transform: scale(1); }
        }
      `}</style>
    </div>
  );
}
