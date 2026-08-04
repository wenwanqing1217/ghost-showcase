'use client';

import Link from 'next/link';
import CosmicBackground from '@/components/marketing/CosmicBackground';
import GlassCard from '@/components/shared/GlassCard';
import Tag from '@/components/shared/Tag';
import GhostSprite from '@/components/shared/GhostSprite';

export default function HomePage() {
  return (
    <div className="relative">
      <CosmicBackground opacity={0.4} />

      <div className="relative z-10">
        {/* ═══════════════════════════════════════════
            HERO — 像截图那样：大视觉 + 标题 + 标签 + 数据
            ═══════════════════════════════════════════ */}
        <section className="pt-20 pb-16 px-6 md:px-12">
          <div className="max-w-4xl mx-auto text-center">
            {/* 小精灵 — 白色幽灵 */}
            <div className="mb-8" style={{ display: 'flex', justifyContent: 'center' }}>
              <GhostSprite size={80} mood="idle" />
            </div>

            {/* 主标题 — 克制、有力 */}
            <h1
              className="mb-4"
              style={{
                fontSize: 'clamp(2.5rem, 6vw, 4.5rem)',
                fontWeight: 800,
                lineHeight: 1.1,
                letterSpacing: '-0.02em',
                color: 'var(--text-primary)',
              }}
            >
              数字灵魂
            </h1>

            {/* 副标题 — 一行说清 */}
            <p
              className="mb-6"
              style={{
                fontSize: 'clamp(1rem, 2vw, 1.25rem)',
                color: 'var(--text-secondary)',
                maxWidth: 560,
                marginLeft: 'auto',
                marginRight: 'auto',
                lineHeight: 1.5,
              }}
            >
              坐在所有 AI 工具之上的身份层。
              <br />
              你的记忆、决策、能力 — 统一在一个数字灵魂里。
            </p>

            {/* 标签 — 精简 */}
            <div className="flex flex-wrap justify-center gap-2 mb-8">
              <Tag>DID 身份</Tag>
              <Tag variant="subtle">因果图谱</Tag>
              <Tag variant="subtle">三层记忆</Tag>
              <Tag variant="subtle">PoE 可验证</Tag>
            </div>

            {/* CTA */}
            <div className="flex items-center justify-center gap-3">
              <Link
                href="/app/chat"
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-medium transition-all"
                style={{
                  background: 'rgba(139,92,246,0.15)',
                  color: 'var(--nebula-light)',
                  border: '1px solid rgba(139,92,246,0.2)',
                }}
              >
                开始使用
                <span style={{ fontSize: 14 }}>→</span>
              </Link>
              <Link
                href="#capabilities"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm transition-all"
                style={{
                  background: 'rgba(255,255,255,0.03)',
                  color: 'var(--text-secondary)',
                  border: '1px solid var(--border-color)',
                }}
              >
                了解更多
              </Link>
            </div>

            {/* 数据条 — 像截图中的统计 */}
            <div
              className="mt-12 flex items-center justify-center gap-8 md:gap-12"
              style={{
                padding: '16px 0',
                borderTop: '1px solid var(--border-color)',
                borderBottom: '1px solid var(--border-color)',
                maxWidth: 560,
                marginLeft: 'auto',
                marginRight: 'auto',
              }}
            >
              {[
                { value: '20+', label: '原子点' },
                { value: '9', label: '能力域' },
                { value: '6', label: '思维框架' },
                { value: '90天', label: 'MVP → v1.0' },
              ].map((stat, i) => (
                <div key={i} style={{ textAlign: 'center' }}>
                  <div
                    style={{
                      fontSize: 'clamp(1.25rem, 3vw, 1.75rem)',
                      fontWeight: 700,
                      color: 'var(--text-primary)',
                      lineHeight: 1.2,
                    }}
                  >
                    {stat.value}
                  </div>
                  <div
                    style={{
                      fontSize: 11,
                      color: 'var(--text-muted)',
                      marginTop: 2,
                      fontFamily: "'JetBrains Mono', monospace",
                      letterSpacing: '0.3px',
                    }}
                  >
                    {stat.label}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ═══════════════════════════════════════════
            能力轨道 — 像播放列表，每项是一个能力
            ═══════════════════════════════════════════ */}
        <section id="capabilities" className="py-20 px-6 md:px-12">
          <div className="max-w-3xl mx-auto">
            {/* 区块标题 */}
            <div className="mb-10">
              <div
                style={{
                  fontSize: 11,
                  fontFamily: "'JetBrains Mono', monospace",
                  color: 'var(--text-muted)',
                  letterSpacing: '1px',
                  textTransform: 'uppercase',
                  marginBottom: 8,
                }}
              >
                CAPABILITIES
              </div>
              <h2
                style={{
                  fontSize: 'clamp(1.5rem, 3vw, 2rem)',
                  fontWeight: 700,
                  color: 'var(--text-primary)',
                  marginBottom: 8,
                }}
              >
                你的数字灵魂，能做什么
              </h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: 14, maxWidth: 480 }}>
                从身份到记忆到决策，六层架构，一套自洽。
              </p>
            </div>

            {/* 能力列表 — 每条独立，有编号 */}
            <div className="space-y-3">
              {[
                {
                  num: '01',
                  title: 'DID 去中心化身份',
                  desc: 'Ed25519 密钥对 · 去中心化标识符 · 私钥本地加密 · 助记词社交恢复',
                  tags: ['Ed25519', 'DID', '本地优先'],
                },
                {
                  num: '02',
                  title: '因果图谱记忆',
                  desc: '20+ 原子点 · 10 种连接关系 · 三层记忆架构 · 多跳推理 + 冲突检测',
                  tags: ['因果推理', '知识图谱'],
                },
                {
                  num: '03',
                  title: '全局回溯决策',
                  desc: '3 分支推演 · 逆向校验 · 置信度评分 · 避免局部最优',
                  tags: ['决策树', '反向验证'],
                },
                {
                  num: '04',
                  title: 'MCP + A2A 桥接',
                  desc: '24 个 MCP 工具 · A2A 协议适配 · Claude/Cursor/Windsurf 直接识别',
                  tags: ['MCP', 'A2A'],
                },
                {
                  num: '05',
                  title: 'PoE 可验证执行',
                  desc: '每次 Skill 执行生成哈希链 · 全程可审计 · 不可篡改',
                  tags: ['PoE', '哈希链'],
                },
                {
                  num: '06',
                  title: '飞书 + 豆包集成',
                  desc: '飞书 WebSocket Bot · 豆包对话自动同步 · Obsidian 双向同步',
                  tags: ['飞书', '豆包', 'Obsidian'],
                },
              ].map((cap, i) => (
                <GlassCard
                  key={i}
                  className="group"
                  style={{
                    padding: '20px 24px',
                    cursor: 'pointer',
                  }}
                >
                  <div className="flex items-start gap-4">
                    {/* 编号 */}
                    <div
                      style={{
                        fontSize: 12,
                        fontFamily: "'JetBrains Mono', monospace",
                        color: 'var(--text-muted)',
                        minWidth: 24,
                        paddingTop: 2,
                      }}
                    >
                      {cap.num}
                    </div>

                    {/* 内容 */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-1.5">
                        <h3
                          className="text-base font-semibold transition-colors"
                          style={{ color: 'var(--text-primary)' }}
                        >
                          {cap.title}
                        </h3>
                        <div className="flex gap-1.5">
                          {cap.tags.map((tag, j) => (
                            <span
                              key={j}
                              style={{
                                fontSize: 10,
                                padding: '2px 8px',
                                borderRadius: 9999,
                                background: 'var(--bg-active)',
                                color: 'var(--text-muted)',
                                border: '1px solid var(--border-color)',
                                fontFamily: "'JetBrains Mono', monospace",
                              }}
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>
                      <p
                        style={{
                          fontSize: 13,
                          color: 'var(--text-secondary)',
                          lineHeight: 1.5,
                        }}
                      >
                        {cap.desc}
                      </p>
                    </div>
                  </div>
                </GlassCard>
              ))}
            </div>
          </div>
        </section>

        {/* ═══════════════════════════════════════════
            架构 — 六层，一排
            ═══════════════════════════════════════════ */}
        <section className="py-16 px-6 md:px-12">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-10">
              <div
                style={{
                  fontSize: 11,
                  fontFamily: "'JetBrains Mono', monospace",
                  color: 'var(--text-muted)',
                  letterSpacing: '1px',
                  textTransform: 'uppercase',
                  marginBottom: 8,
                }}
              >
                ARCHITECTURE
              </div>
              <h2
                style={{
                  fontSize: 'clamp(1.25rem, 2.5vw, 1.75rem)',
                  fontWeight: 700,
                  color: 'var(--text-primary)',
                }}
              >
                六层架构，一套自洽
              </h2>
            </div>

            <div
              className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3"
            >
              {[
                { name: '身份层', tech: 'DID + Ed25519' },
                { name: '记忆层', tech: '因果图谱 + 三层记忆' },
                { name: '决策层', tech: '多跳推理 + 回溯' },
                { name: '桥接层', tech: 'MCP + A2A' },
                { name: '展示层', tech: '悬浮球 + 星链' },
                { name: '通信层', tech: 'AI Mesh' },
              ].map((layer, i) => (
                <GlassCard key={i} className="text-center" style={{ padding: '20px 12px' }}>
                  <div style={{
                    width: 28, height: 28,
                    borderRadius: '50%',
                    background: 'var(--bg-hover)',
                    margin: '0 auto 8px',
                    border: '1px solid var(--border-color)',
                  }} />
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
                    {layer.name}
                  </div>
                  <div
                    style={{
                      fontSize: 10,
                      color: 'var(--text-muted)',
                      fontFamily: "'JetBrains Mono', monospace",
                      lineHeight: 1.4,
                    }}
                  >
                    {layer.tech}
                  </div>
                </GlassCard>
              ))}
            </div>
          </div>
        </section>

        {/* ═══════════════════════════════════════════
            Footer — 克制
            ═══════════════════════════════════════════ */}
        <footer className="py-12 px-6 md:px-12">
          <div className="max-w-3xl mx-auto text-center">
            <div
              style={{
                fontSize: 13,
                color: 'var(--text-muted)',
                fontFamily: "'JetBrains Mono', monospace",
              }}
            >
              Ghost Platform · Web4.0 人机共生基础设施
            </div>
            <div
              style={{
                fontSize: 11,
                color: 'var(--text-muted)',
                marginTop: 4,
                opacity: 0.6,
              }}
            >
              Version 2.0 · 2026-08
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
