'use client';

interface DailyRevenue {
  date: string;
  amount: number;
}

interface RevenueChartProps {
  data: DailyRevenue[];
  currency?: string;
}

export default function RevenueChart({ data, currency = 'USD' }: RevenueChartProps) {
  if (!data || data.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)', fontSize: 13 }}>
        暂无收入数据
      </div>
    );
  }

  const maxAmount = Math.max(...data.map((d) => d.amount), 1);
  const chartHeight = 160;
  const barWidth = Math.max(20, Math.min(60, 400 / data.length - 8));

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    return `${d.getMonth() + 1}/${d.getDate()}`;
  };

  const formatAmount = (amount: number) => {
    if (amount >= 1000) return `$${(amount / 1000).toFixed(1)}k`;
    return `$${amount.toFixed(0)}`;
  };

  // 计算总计
  const total = data.reduce((sum, d) => sum + d.amount, 0);

  return (
    <div>
      {/* 汇总 */}
      <div className="flex-between mb-2">
        <span className="text-sm text-muted">
          共 {data.length} 天 · 总计 ${total.toFixed(2)} {currency}
        </span>
      </div>

      {/* 图表 */}
      <div style={{ overflowX: 'auto' }}>
        <svg
          width={Math.max(400, data.length * (barWidth + 8) + 40)}
          height={chartHeight + 40}
          style={{ display: 'block', margin: '0 auto' }}
        >
          {/* Y 轴参考线 */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
            const y = chartHeight - ratio * chartHeight + 10;
            return (
              <g key={ratio}>
                <line
                  x1={30}
                  y1={y}
                  x2={data.length * (barWidth + 8) + 20}
                  y2={y}
                  stroke="rgba(255,255,255,0.06)"
                  strokeWidth={1}
                />
                <text
                  x={25}
                  y={y + 4}
                  fill="var(--text-muted)"
                  fontSize={10}
                  textAnchor="end"
                >
                  {formatAmount(maxAmount * ratio)}
                </text>
              </g>
            );
          })}

          {/* 柱状图 */}
          {data.map((d, i) => {
            const barHeight = (d.amount / maxAmount) * chartHeight;
            const x = 40 + i * (barWidth + 8);
            const y = chartHeight - barHeight + 10;

            return (
              <g key={d.date}>
                {/* 柱子 */}
                <rect
                  x={x}
                  y={y}
                  width={barWidth}
                  height={barHeight}
                  rx={4}
                  fill="url(#barGradient)"
                  opacity={0.85}
                />
                {/* 数值标签 */}
                {barHeight > 20 && (
                  <text
                    x={x + barWidth / 2}
                    y={y - 4}
                    fill="var(--text)"
                    fontSize={10}
                    textAnchor="middle"
                    fontWeight={500}
                  >
                    {formatAmount(d.amount)}
                  </text>
                )}
                {/* 日期标签 */}
                <text
                  x={x + barWidth / 2}
                  y={chartHeight + 24}
                  fill="var(--text-muted)"
                  fontSize={10}
                  textAnchor="middle"
                >
                  {formatDate(d.date)}
                </text>
              </g>
            );
          })}

          {/* 渐变定义 */}
          <defs>
            <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#6366f1" />
              <stop offset="100%" stopColor="#4f46e5" />
            </linearGradient>
          </defs>
        </svg>
      </div>
    </div>
  );
}
