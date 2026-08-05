'use client';

import TopBar from '@/components/layout/TopBar';
import AuthGuard from '@/components/layout/AuthGuard';
import { useEffect, useState, useRef, useCallback } from 'react';
import { getApiUrl } from '@/lib/gateway-client';

interface ContentItem {
  id: string;
  contentType: string;
  title: string;
  description?: string;
  status: string;
  videoUrl?: string;
  thumbnailUrl?: string;
  duration?: number;
  aspectRatio?: string;
  gameUrl?: string;
  gameType?: string;
  theme?: string;
  tags: string[];
  createdAt: string;
  updatedAt: string;
}

interface GeneratingItem {
  taskId: string;
  type: 'video' | 'game';
  status: string;
  progress?: number;
  title: string;
  description?: string;
  aspectRatio?: string;
  gameType?: string;
  theme?: string;
  startedAt: string;
}

export default function ContentPage() {
  const [items, setItems] = useState<ContentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [demoMode, setDemoMode] = useState(false);

  // Modal & generation state
  const [showModal, setShowModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'video' | 'game'>('video');
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generatingItems, setGeneratingItems] = useState<GeneratingItem[]>([]);

  // Video form state
  const [videoTopic, setVideoTopic] = useState('');
  const [videoAspect, setVideoAspect] = useState('16:9');
  const [videoLanguage, setVideoLanguage] = useState('zh');
  const [videoConcat, setVideoConcat] = useState('random');

  // Game form state
  const [gameType, setGameType] = useState('space_shooter');
  const [gameTheme, setGameTheme] = useState('cyberpunk');
  const [gameDescription, setGameDescription] = useState('');

  const pollingIntervals = useRef<Map<string, NodeJS.Timeout>>(new Map());

  // ── 发布状态 ──
  const [publishModal, setPublishModal] = useState<{ item: ContentItem } | null>(null);
  const [publishing, setPublishing] = useState(false);
  const [publishPlatforms, setPublishPlatforms] = useState<string[]>(['tiktok']);
  const [publishTitle, setPublishTitle] = useState('');
  const [publishMsg, setPublishMsg] = useState<string | null>(null);

  useEffect(() => {
    loadContent();
    // Cleanup polling on unmount
    return () => {
      pollingIntervals.current.forEach((interval) => clearInterval(interval));
      pollingIntervals.current.clear();
    };
  }, [filter]);

  const loadContent = async () => {
    setLoading(true);
    try {
      const url = new URL(getApiUrl('/api/content'), window.location.origin);
      if (filter !== 'all') url.searchParams.set('type', filter);

      const res = await fetch(url.toString());
      if (!res.ok) throw new Error('unhealthy');
      const data = await res.json();
      setItems(data.items || []);
    } catch {
      setDemoMode(true);
      setItems([
        {
          id: 'demo-1',
          contentType: 'video',
          title: '深海探索',
          description: '探索地球最深处的奥秘',
          status: 'completed',
          videoUrl: 'http://localhost:8080/tasks/demo/final-1.mp4',
          duration: 85,
          aspectRatio: '9:16',
          tags: ['deepseek', 'nature'],
          createdAt: new Date(Date.now() - 86400000).toISOString(),
          updatedAt: new Date(Date.now() - 86400000).toISOString(),
        },
        {
          id: 'demo-2',
          contentType: 'game',
          title: '赛博朋克太空射击',
          description: 'Cyberpunk 风格太空射击游戏',
          status: 'completed',
          gameUrl: 'http://localhost:3000/games/demo/index.html',
          gameType: 'space_shooter',
          theme: 'cyberpunk',
          tags: ['game', 'cyberpunk'],
          createdAt: new Date(Date.now() - 172800000).toISOString(),
          updatedAt: new Date(Date.now() - 172800000).toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // ── 打开发布弹窗 ──
  const openPublishModal = (item: ContentItem) => {
    setPublishModal({ item });
    setPublishTitle(item.title);
    setPublishPlatforms(['tiktok']);
    setPublishMsg(null);
  };

  // ── 执行发布 ──
  const handlePublish = async () => {
    if (!publishModal || !publishTitle.trim()) return;
    setPublishing(true);
    setPublishMsg(null);
    try {
      // 从 videoUrl 提取 task_id（URL 格式: .../tasks/{task_id}/final-1.mp4）
      const url = publishModal.item.videoUrl || '';
      const taskIdMatch = url.match(/\/tasks\/([^\/]+)/);
      const taskId = taskIdMatch ? taskIdMatch[1] : publishModal.item.id;

      const resp = await fetch('/api/content/publish', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_id: taskId,
          title: publishTitle.trim(),
          platforms: publishPlatforms,
        }),
      });
      const data = await resp.json();

      if (resp.ok && (data.data?.published || data.published)) {
        setPublishMsg(`✅ 发布成功！Request ID: ${data.data?.request_id || data.request_id}`);
      } else {
        const err = data.data?.error || data.error || '发布失败';
        setPublishMsg(`❌ ${err}`);
      }
    } catch (err) {
      setPublishMsg(`❌ ${err instanceof Error ? err.message : '发布请求失败'}`);
    } finally {
      setPublishing(false);
    }
  };

  const togglePlatform = (p: string) => {
    setPublishPlatforms(prev =>
      prev.includes(p) ? prev.filter(x => x !== p) : [...prev, p]
    );
  };

  const pollTaskStatus = useCallback(async (taskId: string, type: 'video' | 'game') => {
    try {
      // 游戏状态和视频状态走不同的 DS API 路由
      const statusUrl = type === 'game'
        ? `/api/content/game/status/${encodeURIComponent(taskId)}`
        : `/api/content/generate/status/${encodeURIComponent(taskId)}`;
      const res = await fetch(statusUrl);
      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: '状态查询失败' }));
        throw new Error(err.error || `HTTP ${res.status}`);
      }
      const result = await res.json();

      // Gateway wraps responses in {success, data}
      const data = result.data || result;

      let status = 'generating';
      let progress: number | undefined;

      if (type === 'game') {
        // GameEngine returns synchronous status: "completed" | "not_found" | "generating"
        const gameStatus = data.status;
        if (gameStatus === 'completed' || gameStatus === 'success') {
          status = 'completed';
          progress = 100;
        } else if (gameStatus === 'failed' || gameStatus === 'error') {
          status = 'failed';
        } else if (gameStatus === 'not_found') {
          status = 'failed';
        } else {
          status = 'generating';
          progress = 50;
        }
      } else {
        // MoneyPrinterTurbo video status: state 0=pending, 1=success, 2=failed, 4=processing
        const mpState = data.state;
        if (mpState === 1 || mpState === 'completed') {
          status = 'completed';
          progress = 100;
        } else if (mpState === 2 || mpState === 'failed') {
          status = 'failed';
        } else if (mpState === 0 || mpState === 'pending') {
          status = 'pending';
        } else {
          progress = data.progress;
        }
      }

      setGeneratingItems((prev) => {
        const exists = prev.find((item) => item.taskId === taskId);
        if (!exists) return prev;

        const updated = prev.map((item) =>
          item.taskId === taskId
            ? { ...item, status, progress: progress ?? item.progress }
            : item
        );

        // If completed, save game/video to DB and refresh content list
        if (status === 'completed') {
          if (pollingIntervals.current.has(taskId)) {
            clearInterval(pollingIntervals.current.get(taskId));
            pollingIntervals.current.delete(taskId);
          }

          // 将完成的内容写入数据库（游戏生成是同步返回 game_url，需要前端主动保存）
          if (type === 'game') {
            const completedItem = updated.find((i) => i.taskId === taskId);
            if (completedItem && data.game_url) {
              fetch('/api/content', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  contentType: 'game',
                  title: completedItem.title,
                  description: completedItem.description || '',
                  status: 'completed',
                  taskId: taskId,
                  gameUrl: data.game_url,
                  gameType: completedItem.gameType,
                  theme: completedItem.theme,
                  tags: ['game', completedItem.gameType, completedItem.theme].filter(Boolean),
                }),
              }).catch((err) => console.error('保存游戏到数据库失败:', err));
            }
          }

          loadContent();
          // Remove from generating items after a short delay so user sees the completion
          setTimeout(() => {
            setGeneratingItems((items) => items.filter((i) => i.taskId !== taskId));
          }, 1500);
        }

        // If failed, stop polling
        if (status === 'failed') {
          if (pollingIntervals.current.has(taskId)) {
            clearInterval(pollingIntervals.current.get(taskId));
            pollingIntervals.current.delete(taskId);
          }
        }

        return updated;
      });
    } catch (e) {
      console.error('Polling error:', e);
      // Don't stop polling on transient errors
    }
  }, [loadContent]);

  const startPolling = useCallback((taskId: string, type: 'video' | 'game') => {
    // Clear existing interval for this task if any
    if (pollingIntervals.current.has(taskId)) {
      clearInterval(pollingIntervals.current.get(taskId));
    }

    // Initial poll
    pollTaskStatus(taskId, type);

    const interval = setInterval(() => {
      pollTaskStatus(taskId, type);
    }, 5000);

    pollingIntervals.current.set(taskId, interval);
  }, [pollTaskStatus]);

  const handleGenerateVideo = async () => {
    if (!videoTopic.trim()) {
      setError('请输入视频主题');
      return;
    }

    setGenerating(true);
    setError(null);

    try {
      const res = await fetch('/api/content/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'video',
          video_subject: videoTopic,
          video_aspect: videoAspect,
          video_language: videoLanguage,
          video_concat_mode: videoConcat,
          paragraph_number: 3,
          n_threads: 2,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || data.details?.map((d: any) => d.message).join(', ') || '生成请求失败');
      }

      const taskId = data.task_id || data.taskId;
      if (!taskId) {
        throw new Error('未获取到任务 ID');
      }

      const newItem: GeneratingItem = {
        taskId,
        type: 'video',
        status: 'generating',
        progress: 0,
        title: videoTopic,
        description: `视频生成中 · ${videoAspect} · ${videoLanguage === 'zh' ? '中文' : '英文'}`,
        aspectRatio: videoAspect,
        startedAt: new Date().toISOString(),
      };

      setGeneratingItems((prev) => [newItem, ...prev]);
      setShowModal(false);

      // Reset form
      setVideoTopic('');
      setVideoAspect('16:9');
      setVideoLanguage('zh');
      setVideoConcat('random');

      startPolling(taskId, 'video');
    } catch (e) {
      setError(e instanceof Error ? e.message : '生成失败，请重试');
    } finally {
      setGenerating(false);
    }
  };

  const handleGenerateGame = async () => {
    if (!gameType.trim() || !gameTheme.trim()) {
      setError('请填写游戏类型和主题');
      return;
    }

    setGenerating(true);
    setError(null);

    try {
      const res = await fetch('/api/content/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'game',
          game_type: gameType,
          theme: gameTheme,
          description: gameDescription || undefined,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || data.details?.map((d: any) => d.message).join(', ') || '生成请求失败');
      }

      // Game generation returns game_id (synchronous), not task_id
      const gameId = data.game_id || data.gameId;
      if (!gameId) {
        throw new Error('未获取到游戏 ID');
      }

      const newItem: GeneratingItem = {
        taskId: gameId,
        type: 'game',
        status: 'generating',
        progress: 0,
        title: `${gameType} · ${gameTheme}`,
        description: gameDescription || '游戏生成中',
        gameType,
        theme: gameTheme,
        startedAt: new Date().toISOString(),
      };

      setGeneratingItems((prev) => [newItem, ...prev]);
      setShowModal(false);

      // Reset form
      setGameDescription('');

      // Poll for game status (game generation is synchronous, so should complete quickly)
      startPolling(gameId, 'game');
    } catch (e) {
      setError(e instanceof Error ? e.message : '生成失败，请重试');
    } finally {
      setGenerating(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <span className="badge badge-active">完成</span>;
      case 'generating':
      case 'pending':
        return <span className="badge" style={{ background: 'rgba(245,158,11,0.1)', color: '#fbbf24' }}>生成中</span>;
      case 'failed':
        return <span className="badge" style={{ background: 'rgba(239,68,68,0.1)', color: '#ef4444' }}>失败</span>;
      default:
        return null;
    }
  };

  const getTypeIcon = (type: string) => {
    if (type === 'video') return '🎬';
    if (type === 'game') return '🎮';
    return '📄';
  };

  // Combine items and generating items for display
  const displayItems = [...generatingItems, ...items];

  return (
    <AuthGuard>
      <TopBar title="内容库" subtitle="AI 生成的视频与游戏" />

      <div className="p-6">
        {demoMode && (
          <div className="max-w-5xl mx-auto mb-4">
            <div className="card" style={{ padding: '12px 20px', background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.15)' }}>
              <span className="text-xs" style={{ color: '#fbbf24' }}>演示模式 — 后端服务未连接，展示本地演示数据</span>
            </div>
          </div>
        )}

        {/* Header: filters + create button */}
        <div className="max-w-5xl mx-auto mb-6">
          <div className="flex items-center justify-between gap-4">
            <div className="flex gap-2">
              {[
                { key: 'all', label: '全部' },
                { key: 'video', label: '视频' },
                { key: 'game', label: '游戏' },
              ].map((f) => (
                <button
                  key={f.key}
                  onClick={() => setFilter(f.key)}
                  className="px-4 py-1.5 rounded-lg text-xs font-medium transition-all"
                  style={{
                    background: filter === f.key ? 'rgba(139,92,246,0.15)' : 'var(--bg-hover)',
                    color: filter === f.key ? 'var(--nebula-light)' : 'var(--text-secondary)',
                    border: `1px solid ${filter === f.key ? 'rgba(139,92,246,0.2)' : 'var(--border-color)'}`,
                  }}
                >
                  {f.label}
                </button>
              ))}
            </div>

            <button
              onClick={() => { setShowModal(true); setError(null); }}
              className="px-4 py-2 rounded-lg text-xs font-medium transition-all"
              style={{
                background: 'rgba(139,92,246,0.15)',
                color: 'var(--nebula-light)',
                border: '1px solid rgba(139,92,246,0.3)',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              ✨ 创建内容
            </button>
          </div>
        </div>

        {/* Content Grid */}
        <div className="max-w-5xl mx-auto">
          {loading ? (
            <div style={{ textAlign: 'center', padding: 40 }}>
              <div style={{ fontSize: 24, marginBottom: 12, opacity: 0.4 }}>⏳</div>
              <p className="text-muted">加载中...</p>
            </div>
          ) : displayItems.length === 0 ? (
            <div className="card" style={{ padding: 40, textAlign: 'center' }}>
              <div style={{ fontSize: 32, marginBottom: 12, opacity: 0.3 }}>📭</div>
              <p className="text-muted">暂无内容</p>
              <p className="text-xs text-muted mt-2">点击上方「创建内容」按钮开始生成，或通过飞书 Bot 发送 /video /game 命令</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {displayItems.map((item) => {
                const isGenerating = 'taskId' in item;
                const status = isGenerating ? item.status : item.status;
                const progress = isGenerating ? item.progress : undefined;

                return (
                  <div
                    key={isGenerating ? `gen-${item.taskId}` : item.id}
                    className="card transition-all"
                    style={{ padding: 0, overflow: 'hidden' }}
                  >
                    {/* Thumbnail / Preview */}
                    <div style={{
                      height: 180,
                      background: 'var(--bg-hover)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      borderBottom: '1px solid var(--border-color)',
                      position: 'relative',
                    }}>
                      {isGenerating ? (
                        <div style={{ textAlign: 'center', padding: 20 }}>
                          <div style={{ fontSize: 32, marginBottom: 8, opacity: 0.6 }}>
                            {item.type === 'video' ? '🎬' : '🎮'}
                          </div>
                          <div className="text-xs" style={{ color: 'var(--text-muted)', marginBottom: 8 }}>
                            生成中...
                          </div>
                          {progress !== undefined && (
                            <div style={{
                              width: '60%',
                              height: 4,
                              background: 'var(--bg-active)',
                              borderRadius: 2,
                              margin: '0 auto',
                              overflow: 'hidden',
                            }}>
                              <div style={{
                                width: `${progress}%`,
                                height: '100%',
                                background: 'var(--primary-color)',
                                borderRadius: 2,
                                transition: 'width 0.3s',
                              }} />
                            </div>
                          )}
                        </div>
                      ) : item.contentType === 'video' && item.videoUrl ? (
                        <video
                          src={item.videoUrl}
                          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                          muted
                          onMouseEnter={(e) => e.currentTarget.play()}
                          onMouseLeave={(e) => { e.currentTarget.pause(); e.currentTarget.currentTime = 0; }}
                        />
                      ) : item.contentType === 'game' && item.gameUrl ? (
                        <iframe
                          src={item.gameUrl}
                          style={{ width: '100%', height: '100%', border: 'none' }}
                          title={item.title}
                        />
                      ) : (
                        <div style={{ fontSize: 48, opacity: 0.3 }}>
                          {getTypeIcon(item.contentType)}
                        </div>
                      )}

                      {/* Status badge */}
                      <div style={{ position: 'absolute', top: 8, right: 8 }}>
                        {getStatusBadge(status)}
                      </div>

                      {/* Type badge */}
                      <div style={{ position: 'absolute', top: 8, left: 8 }}>
                        <span className="badge" style={{ background: 'rgba(0,0,0,0.5)', color: '#fff', fontSize: 10 }}>
                          {isGenerating ? (item.type === 'video' ? '🎬 视频' : '🎮 游戏') : (item.contentType === 'video' ? '🎬 视频' : '🎮 游戏')}
                        </span>
                      </div>
                    </div>

                    {/* Info */}
                    <div style={{ padding: '14px 16px' }}>
                      <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
                        {item.title}
                      </div>
                      {item.description && (
                        <div className="text-xs" style={{ color: 'var(--text-muted)', marginBottom: 8, lineHeight: 1.4 }}>
                          {item.description}
                        </div>
                      )}

                      {/* Meta */}
                      <div className="flex items-center gap-2 flex-wrap">
                        {item.aspectRatio && (
                          <span style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: "'JetBrains Mono', monospace" }}>
                            {item.aspectRatio}
                          </span>
                        )}
                        {item.gameType && (
                          <span style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: "'JetBrains Mono', monospace" }}>
                            {item.gameType}
                          </span>
                        )}
                        {item.theme && (
                          <span style={{ fontSize: 10, padding: '2px 6px', borderRadius: 4, background: 'var(--bg-active)', color: 'var(--text-muted)' }}>
                            {item.theme}
                          </span>
                        )}
                      </div>

                      {/* Tags */}
                      {item.tags && item.tags.length > 0 && (
                        <div className="flex gap-1 mt-2">
                          {item.tags.slice(0, 3).map((tag, i) => (
                            <span key={i} style={{
                              fontSize: 10,
                              padding: '2px 8px',
                              borderRadius: 4,
                              background: 'var(--bg-active)',
                              color: 'var(--text-muted)',
                            }}>
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* Timestamp */}
                      <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 8, fontFamily: "'JetBrains Mono', monospace" }}>
                        {new Date(item.createdAt).toLocaleString('zh-CN', {
                          month: 'short', day: 'numeric',
                          hour: '2-digit', minute: '2-digit'
                        })}
                      </div>

                      {/* 发布按钮：仅视频且已完成时显示 */}
                      {item.contentType === 'video' && item.videoUrl && status === 'completed' && (
                        <button
                          onClick={() => openPublishModal(item)}
                          style={{
                            marginTop: 10,
                            width: '100%',
                            padding: '8px 12px',
                            background: 'linear-gradient(135deg, rgba(139,92,246,0.15), rgba(56,189,248,0.1))',
                            color: 'var(--nebula-light)',
                            border: '1px solid rgba(139,92,246,0.25)',
                            borderRadius: 8,
                            fontSize: 12,
                            fontWeight: 500,
                            cursor: 'pointer',
                            transition: 'all 0.2s',
                          }}
                        >
                          📤 发布到 TikTok / YouTube / Instagram
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Publish Modal */}
        {publishModal && (
          <div
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0,0,0,0.6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1000,
            }}
            onClick={() => !publishing && setPublishModal(null)}
          >
            <div
              style={{
                background: 'var(--bg-secondary)',
                borderRadius: 16,
                padding: 28,
                maxWidth: 480,
                width: '90%',
                maxHeight: '90vh',
                overflowY: 'auto',
                border: '1px solid var(--border-color)',
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 6, color: 'var(--text-primary)' }}>
                📤 发布视频到社交平台
              </h3>
              <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 20 }}>
                将视频发布到 TikTok / Instagram / YouTube Shorts
              </p>

              {/* 视频预览 */}
              {publishModal.item.videoUrl && (
                <video
                  src={publishModal.item.videoUrl}
                  style={{
                    width: '100%',
                    maxHeight: 200,
                    borderRadius: 10,
                    marginBottom: 16,
                    background: '#000',
                  }}
                  controls
                  muted
                />
              )}

              {/* 标题输入 */}
              <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
                视频标题
              </label>
              <input
                type="text"
                value={publishTitle}
                onChange={(e) => setPublishTitle(e.target.value)}
                placeholder="输入视频标题..."
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  background: 'var(--bg-primary)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 8,
                  color: 'var(--text-primary)',
                  fontSize: 14,
                  marginBottom: 16,
                  outline: 'none',
                }}
              />

              {/* 平台选择 */}
              <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: 8 }}>
                发布平台
              </label>
              <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
                {[
                  { id: 'tiktok', label: '🎵 TikTok', color: '#000' },
                  { id: 'instagram', label: '📸 Instagram', color: '#E1306C' },
                  { id: 'youtube', label: '▶️ YouTube Shorts', color: '#FF0000' },
                ].map(p => {
                  const selected = publishPlatforms.includes(p.id);
                  return (
                    <button
                      key={p.id}
                      onClick={() => togglePlatform(p.id)}
                      style={{
                        padding: '8px 14px',
                        background: selected ? 'rgba(139,92,246,0.15)' : 'var(--bg-primary)',
                        color: selected ? 'var(--nebula-light)' : 'var(--text-muted)',
                        border: `1px solid ${selected ? 'rgba(139,92,246,0.3)' : 'var(--border-color)'}`,
                        borderRadius: 8,
                        fontSize: 13,
                        cursor: 'pointer',
                        fontWeight: selected ? 600 : 400,
                      }}
                    >
                      {p.label}
                    </button>
                  );
                })}
              </div>

              {/* 发布消息 */}
              {publishMsg && (
                <div style={{
                  padding: '10px 12px',
                  marginBottom: 16,
                  borderRadius: 8,
                  background: publishMsg.startsWith('✅') ? 'rgba(16,185,129,0.08)' : 'rgba(239,68,68,0.08)',
                  color: publishMsg.startsWith('✅') ? 'var(--success)' : 'var(--danger)',
                  fontSize: 12,
                  border: `1px solid ${publishMsg.startsWith('✅') ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)'}`,
                }}>
                  {publishMsg}
                </div>
              )}

              {/* 按钮 */}
              <div style={{ display: 'flex', gap: 10 }}>
                <button
                  onClick={() => setPublishModal(null)}
                  disabled={publishing}
                  style={{
                    flex: 1,
                    padding: '10px',
                    background: 'var(--bg-primary)',
                    color: 'var(--text-muted)',
                    border: '1px solid var(--border-color)',
                    borderRadius: 8,
                    fontSize: 13,
                    cursor: publishing ? 'not-allowed' : 'pointer',
                  }}
                >
                  取消
                </button>
                <button
                  onClick={handlePublish}
                  disabled={publishing || !publishTitle.trim() || publishPlatforms.length === 0}
                  style={{
                    flex: 2,
                    padding: '10px',
                    background: 'linear-gradient(135deg, #8b5cf6, #38bdf8)',
                    color: '#fff',
                    border: 'none',
                    borderRadius: 8,
                    fontSize: 13,
                    fontWeight: 600,
                    cursor: (publishing || !publishTitle.trim() || publishPlatforms.length === 0) ? 'not-allowed' : 'pointer',
                    opacity: (publishing || !publishTitle.trim() || publishPlatforms.length === 0) ? 0.6 : 1,
                  }}
                >
                  {publishing ? '发布中...' : '🚀 立即发布'}
                </button>
              </div>

              {/* 提示 */}
              <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 16, lineHeight: 1.5 }}>
                💡 需要在 Gateway 配置 UPLOAD_POST_API_KEY 和 UPLOAD_POST_USERNAME。
                在 <a href="https://upload-post.com" target="_blank" rel="noopener" style={{ color: 'var(--nebula-light)' }}>upload-post.com</a> 注册获取。
              </p>
            </div>
          </div>
        )}

        {/* Create Content Modal */}
        {showModal && (
          <div
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0,0,0,0.6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1000,
            }}
            onClick={() => !generating && setShowModal(false)}
          >
            <div
              className="card"
              style={{ width: 520, maxWidth: '90vw', padding: 24, maxHeight: '90vh', overflow: 'auto' }}
              onClick={(e) => e.stopPropagation()}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                <h3 style={{ fontSize: 18, fontWeight: 600 }}>创建内容</h3>
                {!generating && (
                  <button
                    onClick={() => setShowModal(false)}
                    style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: 20, lineHeight: 1 }}
                  >
                    ×
                  </button>
                )}
              </div>

              {/* Tabs */}
              <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
                <button
                  onClick={() => { setActiveTab('video'); setError(null); }}
                  style={{
                    padding: '8px 20px',
                    borderRadius: 8,
                    border: '1px solid var(--border-color)',
                    background: activeTab === 'video' ? 'var(--primary-color)' : 'transparent',
                    color: activeTab === 'video' ? '#fff' : 'var(--text-primary)',
                    cursor: 'pointer',
                    fontSize: 13,
                    fontWeight: 500,
                  }}
                >
                  🎬 视频生成
                </button>
                <button
                  onClick={() => { setActiveTab('game'); setError(null); }}
                  style={{
                    padding: '8px 20px',
                    borderRadius: 8,
                    border: '1px solid var(--border-color)',
                    background: activeTab === 'game' ? 'var(--primary-color)' : 'transparent',
                    color: activeTab === 'game' ? '#fff' : 'var(--text-primary)',
                    cursor: 'pointer',
                    fontSize: 13,
                    fontWeight: 500,
                  }}
                >
                  🎮 游戏生成
                </button>
              </div>

              {error && (
                <div
                  style={{
                    padding: '8px 12px',
                    background: 'rgba(239,68,68,0.1)',
                    border: '1px solid rgba(239,68,68,0.3)',
                    borderRadius: 6,
                    color: '#ef4444',
                    fontSize: 13,
                    marginBottom: 16,
                  }}
                >
                  {error}
                </div>
              )}

              {/* Video Generation Form */}
              {activeTab === 'video' && (
                <div>
                  <div style={{ marginBottom: 16 }}>
                    <label style={{ display: 'block', marginBottom: 6, fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500 }}>
                      视频主题 <span style={{ color: '#ef4444' }}>*</span>
                    </label>
                    <input
                      className="input"
                      placeholder="例如：深海探索、城市夜景"
                      value={videoTopic}
                      onChange={(e) => setVideoTopic(e.target.value)}
                      disabled={generating}
                      style={{ width: '100%' }}
                    />
                  </div>

                  <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
                    <div style={{ flex: 1 }}>
                      <label style={{ display: 'block', marginBottom: 6, fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500 }}>
                        画面比例
                      </label>
                      <select
                        value={videoAspect}
                        onChange={(e) => setVideoAspect(e.target.value)}
                        disabled={generating}
                        style={{
                          width: '100%',
                          padding: '8px 12px',
                          borderRadius: 6,
                          border: '1px solid var(--border-color)',
                          background: 'var(--bg-secondary)',
                          color: 'var(--text-primary)',
                          fontSize: 13,
                        }}
                      >
                        <option value="9:16">9:16 (竖屏)</option>
                        <option value="16:9">16:9 (横屏)</option>
                        <option value="1:1">1:1 (方形)</option>
                      </select>
                    </div>
                    <div style={{ flex: 1 }}>
                      <label style={{ display: 'block', marginBottom: 6, fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500 }}>
                        语言
                      </label>
                      <select
                        value={videoLanguage}
                        onChange={(e) => setVideoLanguage(e.target.value)}
                        disabled={generating}
                        style={{
                          width: '100%',
                          padding: '8px 12px',
                          borderRadius: 6,
                          border: '1px solid var(--border-color)',
                          background: 'var(--bg-secondary)',
                          color: 'var(--text-primary)',
                          fontSize: 13,
                        }}
                      >
                        <option value="zh">中文</option>
                        <option value="en">英文</option>
                      </select>
                    </div>
                  </div>

                  <div style={{ marginBottom: 20 }}>
                    <label style={{ display: 'block', marginBottom: 6, fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500 }}>
                      拼接模式
                    </label>
                    <div style={{ display: 'flex', gap: 8 }}>
                      {[
                        { value: 'random', label: '随机' },
                        { value: 'sequential', label: '顺序' },
                      ].map((mode) => (
                        <button
                          key={mode.value}
                          type="button"
                          onClick={() => setVideoConcat(mode.value)}
                          disabled={generating}
                          style={{
                            flex: 1,
                            padding: '8px 12px',
                            borderRadius: 6,
                            border: `1px solid ${videoConcat === mode.value ? 'var(--primary-color)' : 'var(--border-color)'}`,
                            background: videoConcat === mode.value ? 'rgba(139,92,246,0.1)' : 'transparent',
                            color: videoConcat === mode.value ? 'var(--nebula-light)' : 'var(--text-secondary)',
                            cursor: generating ? 'not-allowed' : 'pointer',
                            fontSize: 13,
                          }}
                        >
                          {mode.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                    <button
                      type="button"
                      className="btn btn-sm"
                      onClick={() => setShowModal(false)}
                      disabled={generating}
                    >
                      取消
                    </button>
                    <button
                      type="button"
                      className="btn btn-sm btn-primary"
                      onClick={handleGenerateVideo}
                      disabled={generating}
                    >
                      {generating ? '生成中...' : '生成视频'}
                    </button>
                  </div>
                </div>
              )}

              {/* Game Generation Form */}
              {activeTab === 'game' && (
                <div>
                  <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
                    <div style={{ flex: 1 }}>
                      <label style={{ display: 'block', marginBottom: 6, fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500 }}>
                        游戏类型 <span style={{ color: '#ef4444' }}>*</span>
                      </label>
                      <select
                        value={gameType}
                        onChange={(e) => setGameType(e.target.value)}
                        disabled={generating}
                        style={{
                          width: '100%',
                          padding: '8px 12px',
                          borderRadius: 6,
                          border: '1px solid var(--border-color)',
                          background: 'var(--bg-secondary)',
                          color: 'var(--text-primary)',
                          fontSize: 13,
                        }}
                      >
                        <option value="space_shooter">Space Shooter</option>
                        <option value="platformer">Platformer</option>
                        <option value="puzzle">Puzzle</option>
                        <option value="racing">Racing</option>
                        <option value="rpg">RPG</option>
                      </select>
                    </div>
                    <div style={{ flex: 1 }}>
                      <label style={{ display: 'block', marginBottom: 6, fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500 }}>
                        主题风格 <span style={{ color: '#ef4444' }}>*</span>
                      </label>
                      <select
                        value={gameTheme}
                        onChange={(e) => setGameTheme(e.target.value)}
                        disabled={generating}
                        style={{
                          width: '100%',
                          padding: '8px 12px',
                          borderRadius: 6,
                          border: '1px solid var(--border-color)',
                          background: 'var(--bg-secondary)',
                          color: 'var(--text-primary)',
                          fontSize: 13,
                        }}
                      >
                        <option value="cyberpunk">Cyberpunk</option>
                        <option value="japanese_anime">Japanese Anime</option>
                        <option value="pixel_art">Pixel Art</option>
                        <option value="low_poly">Low Poly</option>
                        <option value="realistic">Realistic</option>
                      </select>
                    </div>
                  </div>

                  <div style={{ marginBottom: 20 }}>
                    <label style={{ display: 'block', marginBottom: 6, fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500 }}>
                      游戏描述
                    </label>
                    <textarea
                      value={gameDescription}
                      onChange={(e) => setGameDescription(e.target.value)}
                      placeholder="描述你想要的游戏玩法、场景等（可选）"
                      disabled={generating}
                      style={{
                        width: '100%',
                        minHeight: 80,
                        padding: 10,
                        borderRadius: 6,
                        border: '1px solid var(--border-color)',
                        background: 'var(--bg-secondary)',
                        color: 'var(--text-primary)',
                        fontSize: 13,
                        resize: 'vertical',
                      }}
                    />
                  </div>

                  <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                    <button
                      type="button"
                      className="btn btn-sm"
                      onClick={() => setShowModal(false)}
                      disabled={generating}
                    >
                      取消
                    </button>
                    <button
                      type="button"
                      className="btn btn-sm btn-primary"
                      onClick={handleGenerateGame}
                      disabled={generating}
                    >
                      {generating ? '生成中...' : '生成游戏'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </AuthGuard>
  );
}
