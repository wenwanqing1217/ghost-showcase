'use client';

/**
 * 状态标签组件
 * 根据状态值自动匹配颜色
 */

const STATUS_MAP: Record<string, { label: string; className: string }> = {
  active:    { label: '在售',   className: 'badge-active' },
  draft:     { label: '草稿',   className: 'badge-pending' },
  archived:  { label: '归档',   className: 'badge-refunded' },
  pending:   { label: '待付款', className: 'badge-pending' },
  paid:      { label: '已付款', className: 'badge-paid' },
  fulfilled: { label: '已发货', className: 'badge-fulfilled' },
  refunded:  { label: '已退款', className: 'badge-refunded' },
  cancelled: { label: '已取消', className: 'badge-cancelled' },
};

export default function StatusBadge({ status }: { status: string }) {
  const config = STATUS_MAP[status] || { label: status, className: '' };
  return (
    <span className={`badge ${config.className}`}>
      {config.label}
    </span>
  );
}
