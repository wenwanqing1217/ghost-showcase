'use client';

import { useEffect, useState } from 'react';
import TopBar from '@/components/layout/TopBar';
import AuthGuard from '@/components/layout/AuthGuard';

interface Friend {
  alpha_id: string;
  name: string;
  status: string;
  created_at: string;
}

interface FriendRequest {
  request_id: string;
  from_alpha_id: string;
  to_alpha_id: string;
  message: string;
  status: string;
  created_at: string;
}

interface Message {
  message_id: string;
  from_alpha_id: string;
  to_alpha_id: string;
  content: string;
  created_at: string;
}

type Tab = 'friends' | 'requests' | 'messages';

export default function SocialPage() {
  const [tab, setTab] = useState<Tab>('friends');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Friends
  const [friends, setFriends] = useState<Friend[]>([]);
  const [friendAlphaId, setFriendAlphaId] = useState('');
  const [sendingRequest, setSendingRequest] = useState(false);

  // Requests
  const [requests, setRequests] = useState<FriendRequest[]>([]);
  const [respondingId, setRespondingId] = useState<string | null>(null);

  // Messages
  const [messages, setMessages] = useState<Message[]>([]);
  const [msgTarget, setMsgTarget] = useState('');
  const [msgContent, setMsgContent] = useState('');
  const [sendingMsg, setSendingMsg] = useState(false);
  const [myAlphaId, setMyAlphaId] = useState('Alpha-001');

  useEffect(() => {
    loadIdentity();
  }, []);

  useEffect(() => {
    if (tab === 'friends') loadFriends();
    else if (tab === 'requests') loadRequests();
    else if (tab === 'messages') loadMessages();
  }, [tab]);

  async function loadIdentity() {
    try {
      const res = await fetch('/api/v1/human/identity');
      if (res.ok) {
        const data = await res.json();
        setMyAlphaId(data.data?.alpha_id || data.data?.did || 'Alpha-001');
      }
    } catch { /* ignore */ }
  }

  async function loadFriends() {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`/api/v1/human/social/${encodeURIComponent(myAlphaId)}/friends`);
      if (res.ok) {
        const data = await res.json();
        setFriends(data.friends || data.data || []);
      } else {
        setError(`加载好友列表失败 (${res.status})`);
      }
    } catch (e) {
      setError('加载好友列表失败');
    } finally {
      setLoading(false);
    }
  }

  async function loadRequests() {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`/api/v1/human/social/${encodeURIComponent(myAlphaId)}/requests`);
      if (res.ok) {
        const data = await res.json();
        setRequests(data.requests || data.data || []);
      } else {
        setError(`加载好友请求失败 (${res.status})`);
      }
    } catch {
      setError('加载好友请求失败');
    } finally {
      setLoading(false);
    }
  }

  async function loadMessages() {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`/api/v1/human/social/${encodeURIComponent(myAlphaId)}/messages?limit=50`);
      if (res.ok) {
        const data = await res.json();
        setMessages(data.messages || data.data || []);
      } else {
        setError(`加载消息失败 (${res.status})`);
      }
    } catch {
      setError('加载消息失败');
    } finally {
      setLoading(false);
    }
  }

  async function sendFriendRequest() {
    if (!friendAlphaId.trim()) return;
    setSendingRequest(true);
    setError('');
    try {
      const res = await fetch('/api/v1/human/social/friend-request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ to_alpha_id: friendAlphaId.trim(), message: '你好，我想加你为好友' }),
      });
      const data = await res.json();
      if (res.ok && (data.success || data.ok)) {
        setFriendAlphaId('');
        alert('好友请求已发送');
      } else {
        setError(data.error || data.message || '发送失败');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : '请求失败');
    } finally {
      setSendingRequest(false);
    }
  }

  async function sendMessage() {
    if (!msgTarget.trim() || !msgContent.trim()) return;
    setSendingMsg(true);
    setError('');
    try {
      const res = await fetch('/api/v1/human/social/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ to_alpha_id: msgTarget.trim(), content: msgContent.trim() }),
      });
      const data = await res.json();
      if (res.ok && (data.success || data.ok)) {
        setMsgContent('');
        loadMessages();
      } else {
        setError(data.error || data.message || '发送失败');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : '请求失败');
    } finally {
      setSendingMsg(false);
    }
  }

  async function respondRequest(request_id: string, action: 'accept' | 'reject') {
    setRespondingId(request_id);
    setError('');
    try {
      const res = await fetch(`/api/v1/human/social/friend-request/${encodeURIComponent(request_id)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action }),
      });
      const data = await res.json();
      if (res.ok && (data.success || data.ok)) {
        // Remove from local list
        setRequests((prev) => prev.filter((r) => r.request_id !== request_id));
        alert(action === 'accept' ? '已接受好友请求' : '已拒绝好友请求');
      } else {
        setError(data.error || data.message || (action === 'accept' ? '接受失败' : '拒绝失败'));
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : '请求失败');
    } finally {
      setRespondingId(null);
    }
  }

  return (
    <AuthGuard>
      <TopBar title="社交" subtitle="好友与消息" />
      <div className="p-6">
        <div className="max-w-3xl mx-auto">
          {/* Tab 切换 */}
          <div className="flex gap-1 mb-6 p-1 rounded-xl" style={{ background: 'var(--bg-hover)' }}>
            {[
              { key: 'friends' as Tab, label: '好友列表', icon: '👥' },
              { key: 'requests' as Tab, label: '好友请求', icon: '📨' },
              { key: 'messages' as Tab, label: '消息', icon: '💬' },
            ].map((t) => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className="flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-all"
                style={{
                  background: tab === t.key ? 'var(--bg-secondary)' : 'transparent',
                  color: tab === t.key ? 'var(--text-primary)' : 'var(--text-muted)',
                  boxShadow: tab === t.key ? '0 1px 3px rgba(0,0,0,0.2)' : 'none',
                }}
              >
                <span className="mr-1.5">{t.icon}</span>
                {t.label}
              </button>
            ))}
          </div>

          {/* 错误提示 */}
          {error && (
            <div
              className="mb-4 p-3 rounded-lg text-sm"
              style={{
                background: 'rgba(239,68,68,0.1)',
                color: 'var(--danger)',
                border: '1px solid rgba(239,68,68,0.2)',
              }}
            >
              {error}
            </div>
          )}

          {/* 好友列表 */}
          {tab === 'friends' && (
            <div className="card" style={{ padding: 24 }}>
              <div className="flex gap-2 mb-4">
                <input
                  type="text"
                  value={friendAlphaId}
                  onChange={(e) => setFriendAlphaId(e.target.value)}
                  placeholder="输入对方 Alpha-ID"
                  className="flex-1 rounded-xl px-4 py-2.5 text-sm"
                  style={{
                    background: 'var(--bg-secondary)',
                    color: 'var(--text-primary)',
                    border: '1px solid var(--border-color)',
                  }}
                />
                <button
                  onClick={sendFriendRequest}
                  disabled={sendingRequest}
                  className="px-4 py-2.5 rounded-xl text-sm font-medium"
                  style={{
                    background: 'rgba(139,92,246,0.15)',
                    color: 'var(--nebula-light)',
                    border: '1px solid rgba(139,92,246,0.2)',
                    cursor: sendingRequest ? 'not-allowed' : 'pointer',
                    opacity: sendingRequest ? 0.6 : 1,
                  }}
                >
                  {sendingRequest ? '发送中...' : '加好友'}
                </button>
              </div>

              {loading ? (
                <div className="text-center text-text-muted py-8">加载中...</div>
              ) : friends.length === 0 ? (
                <div className="text-center text-text-muted py-8">暂无好友，输入 Alpha-ID 添加</div>
              ) : (
                <div className="space-y-2">
                  {friends.map((f) => (
                    <div
                      key={f.alpha_id}
                      className="flex items-center justify-between p-3 rounded-lg"
                      style={{ background: 'var(--bg-hover)' }}
                    >
                      <div>
                        <div className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                          {f.name || f.alpha_id}
                        </div>
                        <div className="text-xs font-mono" style={{ color: 'var(--text-muted)' }}>
                          {f.alpha_id}
                        </div>
                      </div>
                      <span
                        className="text-xs px-2 py-1 rounded-full"
                        style={{
                          background: f.status === 'active' ? 'rgba(16,185,129,0.1)' : 'rgba(107,114,128,0.1)',
                          color: f.status === 'active' ? '#10b981' : '#6b7280',
                        }}
                      >
                        {f.status === 'active' ? '已连接' : f.status}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 好友请求 */}
          {tab === 'requests' && (
            <div className="card" style={{ padding: 24 }}>
              {loading ? (
                <div className="text-center text-text-muted py-8">加载中...</div>
              ) : requests.length === 0 ? (
                <div className="text-center text-text-muted py-8">暂无好友请求</div>
              ) : (
                <div className="space-y-2">
                  {requests.map((r) => (
                    <div
                      key={r.request_id}
                      className="flex items-center justify-between p-3 rounded-lg"
                      style={{ background: 'var(--bg-hover)' }}
                    >
                      <div>
                        <div className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                          {r.from_alpha_id}
                        </div>
                        <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
                          {r.message || '好友请求'}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => respondRequest(r.request_id, 'accept')}
                          disabled={respondingId === r.request_id}
                          className="text-xs px-3 py-1.5 rounded-lg"
                          style={{
                            background: 'rgba(16,185,129,0.1)',
                            color: '#10b981',
                            border: '1px solid rgba(16,185,129,0.2)',
                            cursor: respondingId === r.request_id ? 'not-allowed' : 'pointer',
                            opacity: respondingId === r.request_id ? 0.6 : 1,
                          }}
                        >
                          {respondingId === r.request_id ? '处理中...' : '接受'}
                        </button>
                        <button
                          onClick={() => respondRequest(r.request_id, 'reject')}
                          disabled={respondingId === r.request_id}
                          className="text-xs px-3 py-1.5 rounded-lg"
                          style={{
                            background: 'rgba(239,68,68,0.1)',
                            color: '#ef4444',
                            border: '1px solid rgba(239,68,68,0.2)',
                            cursor: respondingId === r.request_id ? 'not-allowed' : 'pointer',
                            opacity: respondingId === r.request_id ? 0.6 : 1,
                          }}
                        >
                          {respondingId === r.request_id ? '处理中...' : '拒绝'}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 消息 */}
          {tab === 'messages' && (
            <div className="card" style={{ padding: 24 }}>
              {/* 发送消息 */}
              <div className="flex gap-2 mb-4">
                <input
                  type="text"
                  value={msgTarget}
                  onChange={(e) => setMsgTarget(e.target.value)}
                  placeholder="对方 Alpha-ID"
                  className="w-40 rounded-xl px-3 py-2.5 text-sm"
                  style={{
                    background: 'var(--bg-secondary)',
                    color: 'var(--text-primary)',
                    border: '1px solid var(--border-color)',
                  }}
                />
                <input
                  type="text"
                  value={msgContent}
                  onChange={(e) => setMsgContent(e.target.value)}
                  placeholder="输入消息..."
                  className="flex-1 rounded-xl px-4 py-2.5 text-sm"
                  style={{
                    background: 'var(--bg-secondary)',
                    color: 'var(--text-primary)',
                    border: '1px solid var(--border-color)',
                  }}
                  onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                />
                <button
                  onClick={sendMessage}
                  disabled={sendingMsg}
                  className="px-4 py-2.5 rounded-xl text-sm font-medium"
                  style={{
                    background: 'rgba(139,92,246,0.15)',
                    color: 'var(--nebula-light)',
                    border: '1px solid rgba(139,92,246,0.2)',
                    cursor: sendingMsg ? 'not-allowed' : 'pointer',
                    opacity: sendingMsg ? 0.6 : 1,
                  }}
                >
                  发送
                </button>
              </div>

              {loading ? (
                <div className="text-center text-text-muted py-8">加载中...</div>
              ) : messages.length === 0 ? (
                <div className="text-center text-text-muted py-8">暂无消息</div>
              ) : (
                <div className="space-y-2 max-h-[400px] overflow-y-auto">
                  {messages.map((m) => (
                    <div
                      key={m.message_id}
                      className={`p-3 rounded-lg max-w-[80%] ${
                        m.from_alpha_id === myAlphaId ? 'ml-auto' : 'mr-auto'
                      }`}
                      style={{
                        background: m.from_alpha_id === myAlphaId
                          ? 'rgba(139,92,246,0.15)'
                          : 'var(--bg-hover)',
                      }}
                    >
                      <div className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>
                        {m.from_alpha_id === myAlphaId ? '我' : m.from_alpha_id}
                        <span className="ml-2 font-mono">{new Date(m.created_at).toLocaleTimeString()}</span>
                      </div>
                      <div className="text-sm" style={{ color: 'var(--text-primary)' }}>
                        {m.content}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </AuthGuard>
  );
}
