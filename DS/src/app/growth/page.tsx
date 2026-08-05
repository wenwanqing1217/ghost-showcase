'use client';

import TopBar from '@/components/layout/TopBar';
import AuthGuard from '@/components/layout/AuthGuard';
import { useEffect, useState } from 'react';

interface Stage {
  name: string;
  min_exp: number;
  emoji: string;
}

interface GrowthStats {
  total_exp: number;
  total_tasks: number;
  tool_counts: Record<string, number>;
  stage_index: number;
  stage_name: string;
  stage_emoji: string;
  last_task_time: number;
  last_task_tool: string;
  last_task_desc: string;
}

interface StageInfo {
  current: Stage;
  next: Stage | null;
  exp_to_next: number;
  progress: number;
}

interface GrowthData {
  success: boolean;
  alpha_id: string;
  demo?: boolean;
  stats: GrowthStats;
  stage_info: StageInfo;
  stages: Stage[];
}

// ── 工具中文名映射 ──
const TOOL_LABELS: Record<string, { name: string; emoji: string; color: string }> = {
  channel_copy: { name: '渠道文案', emoji: '📝', color: 'rgba(255,165,0,0.2)' },
  video_generate: { name: '视频生成', emoji: '🎬', color: 'rgba(139,92,246,0.2)' },
  video_publish: { name: '视频发布', emoji: '📤', color: 'rgba(56,189,248,0.2)' },
  douyin: { name: '抖音发布', emoji: '🎵', color: 'rgba(255,80,80,0.2)' },
  shortdramas: { name: '短剧预审', emoji: '🎭', color: 'rgba(34,197,94,0.2)' },
  map: { name: '地图查询', emoji: '🗺️', color: 'rgba(148,163,184,0.2)' },
  shopify: { name: '店铺优化', emoji: '🛒', color: 'rgba(168,85,247,0.2)' },
};

export default function GrowthPage() {
  const [data, setData] = useState<GrowthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [alphaId, setAlphaId] = useState('feishu_user');

  useEffect(() => {
    loadGrowth();
  }, [alphaId]);

  const loadGrowth = async () => {
    setLoading(true);
    try {
      const resp = await fetch(`/api/growth/stats?alpha_id=${encodeURIComponent(alphaId)}`);
      const d = await resp.json();
      if (resp.ok && d.success) {
        setData(d);
      } else {
        setData(null);
      }
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <AuthGuard>
        <div className="page-container">
          <TopBar title="成长地图" />
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
            加载中...
          </div>
        </div>
      </AuthGuard>
    );
  }

  const stats = data?.stats;
  const stageInfo = data?.stage_info;
  const stages = data?.stages || [];

  return (
    <AuthGuard>
      <div className="page-container">
        <TopBar title="成长地图 · 精灵进化" />

        <div style={{ padding: '20px 24px', maxWidth: 1100, margin: '0 auto' }}>
          {/* Alpha-ID 输入 */}
          <div style={{ marginBottom: 16, display: 'flex', gap: 10, alignItems: 'center' }}>
            <input
              style={{
                padding: '6px 12px',
                fontSize: 12,
                background: 'rgba(0,0,0,0.2)',
                border: '1px solid var(--border-color)',
                borderRadius: 6,
                color: 'var(--text-primary)',
                width: 200,
              }}
              value={alphaId}
              onChange={(e) => setAlphaId(e.target.value)}
              placeholder="Alpha-ID"
            />
            <button
              onClick={loadGrowth}
              style={{
                padding: '6px 14px',
                fontSize: 12,
                background: 'rgba(139,92,246,0.15)',
                color: 'var(--nebula-light)',
                border: '1px solid rgba(139,92,246,0.25)',
                borderRadius: 6,
                cursor: 'pointer',
              }}
            >
              刷新
            </button>
            {data?.demo && (
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                （演示模式 — 飞书发指令后会显示真实数据）
              </span>
            )}
          </div>

          {/* 精灵形态卡片 */}
          {stats && stageInfo && (
            <div
              style={{
                background: 'linear-gradient(135deg, rgba(139,92,246,0.08), rgba(56,189,248,0.05))',
                border: '1px solid rgba(139,92,246,0.2)',
                borderRadius: 16,
                padding: 28,
                marginBottom: 20,
                textAlign: 'center',
              }}
            >
              {/* 精灵 emoji */}
              <div style={{ fontSize: 72, marginBottom: 8 }}>
                {stageInfo.current.emoji}
              </div>
              <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>
                {stageInfo.current.name}
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 20 }}>
                经验值：{stats.total_exp} · 完成任务：{stats.total_tasks}
              </div>

              {/* 进度条 */}
              {stageInfo.next && (
                <div style={{ maxWidth: 400, margin: '0 auto' }}>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      fontSize: 11,
                      color: 'var(--text-muted)',
                      marginBottom: 6,
                    }}
                  >
                    <span>{stageInfo.current.name}</span>
                    <span>还需 {stageInfo.exp_to_next} 经验进化到 {stageInfo.next.name}</span>
                  </div>
                  <div
                    style={{
                      height: 8,
                      background: 'rgba(0,0,0,0.3)',
                      borderRadius: 4,
                      overflow: 'hidden',
                    }}
                  >
                    <div
                      style={{
                        height: '100%',
                        width: `${Math.min(stageInfo.progress * 100, 100)}%`,
                        background: 'linear-gradient(90deg, rgba(139,92,246,0.6), rgba(56,189,248,0.6))',
                        borderRadius: 4,
                        transition: 'width 0.5s',
                      }}
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 进化路径 */}
          <div
            style={{
              background: 'rgba(255,255,255,0.02)',
              border: '1px solid var(--border-color)',
              borderRadius: 12,
              padding: 18,
              marginBottom: 20,
            }}
          >
            <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 14, color: 'var(--text-primary)' }}>
              🗺️ 进化路径
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 4 }}>
              {stages.map((stage, i) => {
                const current = stats?.stage_index === i;
                const passed = (stats?.stage_index ?? 0) > i;
                return (
                  <div key={i} style={{ flex: 1, textAlign: 'center', position: 'relative' }}>
                    {i > 0 && (
                      <div
                        style={{
                          position: 'absolute',
                          right: '50%',
                          top: 18,
                          width: '100%',
                          height: 2,
                          background: passed ? 'rgba(139,92,246,0.4)' : 'rgba(255,255,255,0.08)',
                        }}
                      />
                    )}
                    <div
                      style={{
                        width: 36,
                        height: 36,
                        borderRadius: '50%',
                        margin: '0 auto 6px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 18,
                        background: current
                          ? 'rgba(139,92,246,0.2)'
                          : passed
                          ? 'rgba(34,197,94,0.15)'
                          : 'rgba(255,255,255,0.03)',
                        border: current
                          ? '2px solid rgba(139,92,246,0.5)'
                          : passed
                          ? '1px solid rgba(34,197,94,0.3)'
                          : '1px solid var(--border-color)',
                        position: 'relative',
                        zIndex: 1,
                      }}
                    >
                      {stage.emoji}
                    </div>
                    <div
                      style={{
                        fontSize: 10,
                        color: current
                          ? 'var(--nebula-light)'
                          : passed
                          ? '#4ade80'
                          : 'var(--text-muted)',
                        fontWeight: current ? 600 : 400,
                      }}
                    >
                      {stage.name}
                    </div>
                    <div style={{ fontSize: 9, color: 'var(--text-muted)' }}>
                      {stage.min_exp}+
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 技能分布 */}
          {stats && Object.keys(stats.tool_counts).length > 0 && (
            <div
              style={{
                background: 'rgba(255,255,255,0.02)',
                border: '1px solid var(--border-color)',
                borderRadius: 12,
                padding: 18,
                marginBottom: 20,
              }}
            >
              <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 14, color: 'var(--text-primary)' }}>
                🎯 技能分布
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 10 }}>
                {Object.entries(stats.tool_counts).map(([tool, count]) => {
                  const meta = TOOL_LABELS[tool] || { name: tool, emoji: '🔧', color: 'rgba(148,163,184,0.15)' };
                  return (
                    <div
                      key={tool}
                      style={{
                        background: meta.color,
                        border: '1px solid var(--border-color)',
                        borderRadius: 10,
                        padding: 12,
                        textAlign: 'center',
                      }}
                    >
                      <div style={{ fontSize: 24, marginBottom: 4 }}>{meta.emoji}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 2 }}>{meta.name}</div>
                      <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)' }}>{count}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* 最近任务 */}
          {stats && stats.last_task_tool && (
            <div
              style={{
                background: 'rgba(255,255,255,0.02)',
                border: '1px solid var(--border-color)',
                borderRadius: 12,
                padding: 18,
                marginBottom: 20,
              }}
            >
              <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 10, color: 'var(--text-primary)' }}>
                🕐 最近任务
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.8 }}>
                <div>
                  工具：<strong>{TOOL_LABELS[stats.last_task_tool]?.name || stats.last_task_tool}</strong>
                </div>
                {stats.last_task_desc && <div>描述：{stats.last_task_desc}</div>}
                {stats.last_task_time > 0 && (
                  <div>
                    时间：{new Date(stats.last_task_time * 1000).toLocaleString('zh-CN')}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 飞书指令引导 */}
          <div
            style={{
              background: 'linear-gradient(135deg, rgba(139,92,246,0.08), rgba(56,189,248,0.05))',
              border: '1px solid rgba(139,92,246,0.2)',
              borderRadius: 12,
              padding: 16,
              fontSize: 12,
              color: 'var(--text-secondary)',
              lineHeight: 1.8,
            }}
          >
            <div style={{ fontWeight: 600, color: 'var(--nebula-light)', marginBottom: 8 }}>
              💡 如何获得成长值？
            </div>
            <div>在飞书跟总助对话，每完成一个任务都会获得经验：</div>
            <div>📝 "帮我写个闲鱼文案卖香薰" → +2 经验</div>
            <div>🎬 "做个香薰种草视频" → +3 经验</div>
            <div>📤 "把视频发到 TikTok" → +5 经验</div>
            <div>🎵 "发个短剧《霸总爱上我》" → +4 经验</div>
            <div>🗺️ "查一下附近的咖啡厅" → +1 经验</div>
            <div style={{ marginTop: 8 }}>经验累计会触发精灵进化：🌱 种子 → 🥚 幼生体 → 🌿 成长期 → 🌳 成熟体 → ✨ 完全体 → 🔮 超越体</div>
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}
