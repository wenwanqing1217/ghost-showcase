'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import TopBar from '@/components/layout/TopBar';
import AuthGuard from '@/components/layout/AuthGuard';
import GhostSprite from '@/components/shared/GhostSprite';
import { humanApi } from '@/lib/api';

// 骨架屏样式
const SKELETON_STYLE: React.CSSProperties = {
  background: 'linear-gradient(90deg, rgba(255,255,255,0.04) 25%, rgba(255,255,255,0.08) 50%, rgba(255,255,255,0.04) 75%)',
  backgroundSize: '200% 100%',
  animation: 'skeleton-shimmer 1.5s ease-in-out infinite',
  borderRadius: 8,
};

const SKELETON_LINES = [
  { width: '60%', height: 12 },
  { width: '80%', height: 12 },
  { width: '45%', height: 12 },
];

// ── 类型 ──
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

interface Identity {
  success: boolean;
  data?: {
    alpha_id: string;
    did?: string;
    status: string;
  };
}

const SPRITE_STATES = ['●', '◉', '○', '◌'] as const;

export default function ChatPage() {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [gwStatus, setGwStatus] = useState<{ ok: boolean } | null>(null);
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [spriteState, setSpriteState] = useState(0);
  const [demoMode, setDemoMode] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const activeThread = threads.find(t => t.id === activeThreadId);
  const alphaId = identity?.data?.alpha_id || 'Alpha-001';

  // 初始化：创建第一个对话
  useEffect(() => {
    if (threads.length === 0) {
      createThread();
    }
    // 初始化完成，隐藏骨架屏
    const timer = setTimeout(() => setIsInitializing(false), 300);
    return () => clearTimeout(timer);
  }, []);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activeThread?.messages.length]);

  // 获取身份信息
  useEffect(() => {
    humanApi.getIdentity()
      .then(data => setIdentity(data as Identity))
      .catch(() => setIdentity(null));
  }, []);

  // Gateway 状态检查
  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch('/api/health');
        const ok = res.ok;
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

  // 精灵状态循环
  useEffect(() => {
    if (!sending) {
      const timer = setInterval(() => {
        setSpriteState(s => (s + 1) % SPRITE_STATES.length);
      }, 3000);
      return () => clearInterval(timer);
    }
  }, [sending]);

  const createThread = useCallback((title?: string) => {
    const newThread: Thread = {
      id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
      title: title || '新对话',
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
    // setActiveThreadId outside the updater to avoid stale closure
    if (newActiveId) {
      setActiveThreadId(newActiveId);
    } else if (threads.length <= 1) {
      createThread();
    }
  }, [activeThreadId, createThread, threads.length]);

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
    setSpriteState(1);

    // 更新对话标题（首条消息）
    setThreads(prev => prev.map(t =>
      t.id === activeThreadId && t.messages.length === 0
        ? { ...t, title: input.trim().slice(0, 24) + (input.trim().length > 24 ? '...' : ''), messages: [...t.messages, userMsg], updatedAt: Date.now() }
        : t.id === activeThreadId
          ? { ...t, messages: [...t.messages, userMsg], updatedAt: Date.now() }
          : t
    ));

    try {
      if (demoMode) {
        // 离线模式：本地演示回复（更快）
        await new Promise(r => setTimeout(r, 500 + Math.random() * 300));
        const replies = [
          `收到你的消息了。当前处于离线演示模式，Gateway 未连接。\n\n消息已记录到本地会话，待 Gateway 恢复后可同步。`,
          `你好！当前为离线模式。你的消息已保存。\n\n如需完整功能，请检查 Gateway 服务状态。`,
          `离线模式运行中。你的输入已接收。\n\n连接恢复后将自动同步记忆链。`,
        ];
        const reply = replies[Math.floor(Math.random() * replies.length)];
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
        return;
      }
      const data = await humanApi.chat(input.trim(), alphaId);
      const reply = (data as any)?.data?.reply || (data as any)?.reply || (data as any)?.error || '无回复';

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
    } catch (err) {
      const errMsg: ChatMessage = {
        role: 'assistant',
        content: `请求失败: ${err instanceof Error ? err.message : '请检查 Gateway 连接'}`,
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
      setSpriteState(0);
      inputRef.current?.focus();
    }
  };

  const searchMemories = async () => {
    const q = prompt('搜索知识链关键词:');
    if (!q || !activeThreadId) return;

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
      const data = await humanApi.searchMemory(q);
      const results = (data as any)?.data?.results || (data as any)?.results || [];
      const reply = results.length > 0
        ? `找到 ${results.length} 条记忆:\n${results.map((r: any) => `• ${r.title || r.content?.slice(0, 50)}`).join('\n')}`
        : '未找到相关记忆';

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
    <AuthGuard>
      <div className="flex flex-col" style={{ height: 'calc(100vh - 60px)' }}>
        {/* 顶部栏 */}
        <TopBar
          title="对话"
          subtitle="Gateway 统一对话接口 · 双链记忆"
          actions={
            <div className="flex items-center gap-3">
              {identity?.data?.alpha_id && (
                <span className="text-xs" style={{ color: 'var(--nebula-light)' }}>
                  ID: {identity.data.alpha_id}
                </span>
              )}
              <span className="text-xs" style={{ color: gwStatus?.ok ? '#34d399' : '#f87171' }}>
                Gateway: {gwStatus?.ok ? '正常' : '异常'}
              </span>
            </div>
          }
        />

        {/* 离线模式横幅 */}
        {demoMode && (
          <div className="animate-slide-up" style={{
            padding: '10px 16px',
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
            离线演示模式：Gateway 未连接，对话以本地模拟运行。连接恢复后自动切换。
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
            {/* 头部 */}
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

            {/* 对话列表 */}
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
                          ? thread.messages[thread.messages.length - 1].content.slice(0, 30) + (thread.messages[thread.messages.length - 1].content.length > 30 ? '...' : '')
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
                          className="text-xs px-1 rounded transition-colors"
                          style={{ color: 'var(--text-muted)' }}
                          onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--danger)'; }}
                          onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--text-muted)'; }}
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
                    {threads.length} 个对话 · Alpha-ID: {alphaId}
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
                      className="text-lg px-2 py-1 rounded transition-colors"
                      style={{ color: 'var(--text-muted)' }}
                    >
                      {sidebarOpen ? '◁' : '▷'}
                    </button>
                    <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                      {activeThread.title}
                    </span>
                    <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                      {activeThread.messages.length} 条消息
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={searchMemories}
                      className="text-xs px-3 py-1.5 rounded-lg transition-all"
                      style={{
                        background: 'rgba(56,189,248,0.08)',
                        color: 'var(--cosmic-light)',
                        border: '1px solid rgba(56,189,248,0.12)',
                      }}
                    >
                      搜索记忆
                    </button>
                    <span className="text-lg">{SPRITE_STATES[spriteState]}</span>
                    <GhostSprite size={28} />
                  </div>
                </div>

                {/* 消息区 */}
                <div className="flex-1 overflow-y-auto px-6 py-4" style={{ background: 'var(--bg-primary)' }}>
                  {isInitializing ? (
                    /* 骨架屏加载 */
                    <div className="max-w-3xl mx-auto space-y-4">
                      {SKELETON_LINES.map((line, i) => (
                        <div key={i} style={{ ...SKELETON_STYLE, ...line, maxWidth: line.width }} />
                      ))}
                    </div>
                  ) : activeThread.messages.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full animate-fade-in">
                      <GhostSprite size={64} mood="idle" />
                      <div className="mt-6 text-center">
                        <div className="text-lg mb-2" style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
                          开始一段新对话
                        </div>
                        <div className="text-sm" style={{ color: 'var(--text-muted)' }}>
                          小精灵随时待命，问任何问题
                        </div>
                      </div>
                      <div className="flex gap-2 mt-6">
                        {['帮我写一段文案', '解释因果图谱', '分析订单数据'].map((suggestion) => (
                          <button
                            key={suggestion}
                            onClick={() => setInput(suggestion)}
                            className="suggestion-btn px-3 py-1.5 rounded-full text-xs"
                          >
                            {suggestion}
                          </button>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="max-w-3xl mx-auto space-y-4">
                      {activeThread.messages.map((msg) => {
                        const isUser = msg.role === 'user';
                        const avatarBg = isUser ? 'rgba(139,92,246,0.15)' : 'rgba(56,189,248,0.08)';
                        const avatarBorder = isUser ? 'rgba(139,92,246,0.2)' : 'rgba(56,189,248,0.12)';
                        const bubbleBg = isUser ? 'rgba(139,92,246,0.1)' : 'rgba(255,255,255,0.03)';
                        const bubbleBorder = isUser ? 'rgba(139,92,246,0.12)' : 'var(--border-color)';
                        const bubbleAlign = isUser ? 'right' : 'left';

                        return (
                          <div
                            key={msg.id}
                            className="flex gap-3 animate-message-in"
                            style={{ flexDirection: isUser ? 'row-reverse' : 'row' }}
                          >
                            {/* 头像 */}
                            <div
                              className="rounded-full flex-shrink-0 flex items-center justify-center"
                              style={{ width: 32, height: 32, background: avatarBg, border: `1px solid ${avatarBorder}` }}
                            >
                              {isUser ? (
                                <div style={{ width: 20, height: 20, borderRadius: '50%', background: 'rgba(139,92,246,0.4)', border: '1px solid rgba(139,92,246,0.3)' }} />
                              ) : (
                                <GhostSprite size={20} />
                              )}
                            </div>

                            {/* 消息内容 */}
                            <div
                              className="rounded-2xl px-4 py-2.5 max-w-[75%]"
                              style={{ background: bubbleBg, border: `1px solid ${bubbleBorder}` }}
                            >
                              <div className="text-sm leading-relaxed" style={{ color: 'var(--text-primary)', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                                {msg.content}
                              </div>
                              <div className="text-xs mt-1.5" style={{ color: 'var(--text-muted)', textAlign: bubbleAlign }}>
                                {msg.time}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                      {sending && (
                        <div className="flex gap-3">
                          <div className="rounded-full flex-shrink-0 flex items-center justify-center"
                            style={{ width: 32, height: 32, background: 'rgba(56,189,248,0.08)', border: '1px solid rgba(56,189,248,0.12)' }}>
                            <GhostSprite size={20} />
                          </div>
                          <div className="rounded-2xl px-4 py-3"
                            style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)' }}>
                            <div className="flex gap-1">
                              {[0, 1, 2].map(i => (
                                <div key={i} className="rounded-full"
                                  style={{
                                    width: 6, height: 6,
                                    background: 'var(--nebula)',
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

                {/* 底部输入栏 */}
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
                        placeholder="输入消息..."
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
                          e.currentTarget.style.borderColor = 'rgba(139,92,246,0.3)';
                          e.currentTarget.style.boxShadow = '0 0 0 3px rgba(139,92,246,0.05)';
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
                            ? 'rgba(139,92,246,0.15)'
                            : 'rgba(255,255,255,0.04)',
                          color: input.trim() && !sending ? 'var(--nebula-light)' : 'var(--text-muted)',
                          border: `1px solid ${input.trim() && !sending ? 'rgba(139,92,246,0.2)' : 'var(--border-color)'}`,
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
                <div className="text-center">
                  <GhostSprite size={48} mood="idle" />
                  <div className="mt-4 text-sm" style={{ color: 'var(--text-muted)' }}>
                    选择或创建一个对话
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
    </AuthGuard>
  );
}
