'use client';

/**
 * NavIcon — 侧边栏导航图标
 * 纯 CSS 实现，最小化设计，避免廉价 emoji
 * 每种图标用不同的 CSS 形状组合
 */
type IconType =
  | 'overview'
  | 'chat'
  | 'memory'
  | 'workflow'
  | 'bridge'
  | 'dashboard'
  | 'network'
  | 'workbench'
  | 'products'
  | 'orders'
  | 'settings'
  | 'social'
  | 'brain'
  | 'voice';

interface NavIconProps {
  type: IconType;
  active?: boolean;
  size?: number;
}

export default function NavIcon({ type, active = false, size = 18 }: NavIconProps) {
  const color = active ? 'var(--nebula-light)' : 'var(--text-muted)';
  const stroke = 1.5;

  const icons: Record<IconType, React.ReactNode> = {
    overview: (
      <svg width={size} height={size} viewBox="0 0 18 18" fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="2" width="6" height="6" rx="1" />
        <rect x="10" y="2" width="6" height="6" rx="1" />
        <rect x="2" y="10" width="6" height="6" rx="1" />
        <rect x="10" y="10" width="6" height="6" rx="1" />
      </svg>
    ),
    chat: (
      <svg width={size} height={size} viewBox="0 0 18 18" fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 5h12v7H7l-4 3V5z" />
        <circle cx="7" cy="9" r="0.8" fill={color} />
        <circle cx="11" cy="9" r="0.8" fill={color} />
        <line x1="9.5" y1="9" x2="8.5" y2="9" />
      </svg>
    ),
    memory: (
      <svg width={size} height={size} viewBox="0 0 18 18" fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round">
        <circle cx="6" cy="5" r="1.8" />
        <circle cx="12" cy="5" r="1.8" />
        <circle cx="9" cy="13" r="1.8" />
        <line x1="6.9" y1="6.4" x2="8" y2="11.5" />
        <line x1="11.1" y1="6.4" x2="10" y2="11.5" />
        <line x1="7.5" y1="5" x2="10.5" y2="5" />
      </svg>
    ),
    workflow: (
      <svg width={size} height={size} viewBox="0 0 18 18" fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round">
        <polyline points="2,8 6,4 10,10 14,6 16,7" />
        <circle cx="6" cy="4" r="1.2" fill={color} stroke="none" />
        <circle cx="10" cy="10" r="1.2" fill={color} stroke="none" />
        <circle cx="14" cy="6" r="1.2" fill={color} stroke="none" />
      </svg>
    ),
    bridge: (
      <svg width={size} height={size} viewBox="0 0 18 18" fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round">
        <line x1="2" y1="8" x2="16" y2="8" />
        <line x1="5" y1="8" x2="5" y2="14" />
        <line x1="13" y1="8" x2="13" y2="14" />
        <line x1="3" y1="14" x2="15" y2="14" />
        <line x1="5" y1="10" x2="13" y2="10" strokeDasharray="2 2" />
      </svg>
    ),
    dashboard: (
      <svg width={size} height={size} viewBox="0 0 18 18" fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round">
        <line x1="3" y1="14" x2="3" y2="10" />
        <line x1="7" y1="14" x2="7" y2="6" />
        <line x1="11" y1="14" x2="11" y2="8" />
        <line x1="15" y1="14" x2="15" y2="4" />
      </svg>
    ),
    network: (
      <svg width={size} height={size} viewBox="0 0 18 18" fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round">
        <circle cx="9" cy="3" r="1.5" fill={color} stroke="none" />
        <circle cx="3" cy="14" r="1.5" fill={color} stroke="none" />
        <circle cx="15" cy="14" r="1.5" fill={color} stroke="none" />
        <line x1="9" y1="4.5" x2="3" y2="12.5" />
        <line x1="9" y1="4.5" x2="15" y2="12.5" />
        <line x1="5.5" y1="14" x2="12.5" y2="14" />
      </svg>
    ),
    workbench: (
      <svg width={size} height={size} viewBox="0 0 18 18" fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="2" width="14" height="14" rx="1.5" />
        <line x1="8" y1="2" x2="8" y2="16" />
        <line x1="2" y1="8" x2="16" y2="8" />
      </svg>
    ),
    products: (
      <svg width={size} height={size} viewBox="0 0 18 18" fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="6" width="12" height="10" rx="1.5" />
        <line x1="3" y1="10" x2="15" y2="10" />
        <line x1="7" y1="3" x2="7" y2="6" />
        <line x1="11" y1="3" x2="11" y2="6" />
        <line x1="7" y1="3" x2="11" y2="3" />
      </svg>
    ),
    orders: (
      <svg width={size} height={size} viewBox="0 0 18 18" fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round">
        <line x1="4" y1="4" x2="14" y2="4" />
        <line x1="4" y1="9" x2="14" y2="9" />
        <line x1="4" y1="14" x2="10" y2="14" />
        <circle cx="15" cy="4" r="1" fill={color} stroke="none" />
        <circle cx="15" cy="9" r="1" fill={color} stroke="none" />
        <circle cx="12" cy="14" r="1" fill={color} stroke="none" />
      </svg>
    ),
    settings: (
      <svg width={size} height={size} viewBox="0 0 18 18" fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round">
        <circle cx="9" cy="9" r="2.5" />
        <path d="M9 1v2M9 15v2M1 9h2M15 9h2M3.5 3.5l1.4 1.4M13.1 13.1l1.4 1.4M3.5 14.5l1.4-1.4M13.1 4.9l1.4-1.4" />
      </svg>
    ),
    social: (
      <svg width={size} height={size} viewBox="0 0 18 18" fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round">
        <circle cx="6" cy="6" r="2.5" />
        <circle cx="13" cy="4" r="2.5" />
        <circle cx="11" cy="12" r="2.5" />
        <path d="M8.2 7.3L11.5 5.8M8 7.5L10 11" />
      </svg>
    ),
    brain: (
      <svg width={size} height={size} viewBox="0 0 18 18" fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round">
        <path d="M9 2C5.5 2 3 4.5 3 7.5c0 2 .8 3.8 2 5v2.5l1.5-1c.5.2 1 .3 1.5.3 3.5 0 6-2.5 6-5.5S12.5 2 9 2z" />
        <path d="M9 6v6M7 9h4" />
      </svg>
    ),
    voice: (
      <svg width={size} height={size} viewBox="0 0 18 18" fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round">
        <rect x="5" y="2" width="4" height="9" rx="2" />
        <path d="M2 9h3M13 9h3M9 9v5" />
        <path d="M7 14c-1 1-2 2.5-2 4h8c0-1.5-1-3-2-4" />
      </svg>
    ),
  };

  return (
    <span className="inline-flex items-center justify-center" style={{ width: size, height: size, flexShrink: 0 }}>
      {icons[type]}
    </span>
  );
}
