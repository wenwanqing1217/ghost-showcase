import { describe, it, expect, vi, beforeEach } from 'vitest';

// Hoist mock object so vi.mock factory can reference it
const { mockPrisma } = vi.hoisted(() => ({
  mockPrisma: {
    agentRun: { count: vi.fn() },
    approval: { count: vi.fn() },
    alert: { count: vi.fn() },
    order: { count: vi.fn(), findMany: vi.fn() },
  },
}));

vi.mock('@/lib/db', () => ({
  prisma: mockPrisma,
}));

import { getDashboardMetrics } from '@/lib/db/metrics';

describe('getDashboardMetrics', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calculates revenue from orders correctly', async () => {
    mockPrisma.agentRun.count.mockResolvedValue(5);
    mockPrisma.approval.count.mockResolvedValueOnce(8).mockResolvedValueOnce(10);
    mockPrisma.alert.count.mockResolvedValue(2);
    mockPrisma.order.count.mockResolvedValue(3);
    mockPrisma.order.findMany.mockResolvedValue([
      { totalPrice: '29.99' },
      { totalPrice: '49.99' },
      { totalPrice: '19.99' },
    ]);

    const metrics = await getDashboardMetrics();

    expect(metrics.revenue).toBeCloseTo(99.97, 2);
    expect(metrics.orders).toBe(3);
    expect(metrics.avgOrderValue).toBeCloseTo(33.32, 1);
  });

  it('handles empty database (zero orders)', async () => {
    mockPrisma.agentRun.count.mockResolvedValue(0);
    mockPrisma.approval.count.mockResolvedValueOnce(0).mockResolvedValueOnce(0);
    mockPrisma.alert.count.mockResolvedValue(0);
    mockPrisma.order.count.mockResolvedValue(0);
    mockPrisma.order.findMany.mockResolvedValue([]);

    const metrics = await getDashboardMetrics();

    expect(metrics.revenue).toBe(0);
    expect(metrics.orders).toBe(0);
    expect(metrics.avgOrderValue).toBe(0);
    expect(metrics.approvalRate).toBe(0);
  });

  it('handles malformed price strings gracefully', async () => {
    mockPrisma.agentRun.count.mockResolvedValue(1);
    mockPrisma.approval.count.mockResolvedValueOnce(1).mockResolvedValueOnce(1);
    mockPrisma.alert.count.mockResolvedValue(0);
    mockPrisma.order.count.mockResolvedValue(2);
    mockPrisma.order.findMany.mockResolvedValue([
      { totalPrice: 'invalid' },
      { totalPrice: '25.50' },
    ]);

    const metrics = await getDashboardMetrics();

    expect(metrics.revenue).toBe(25.5);
  });

  it('returns fallback values on database error', async () => {
    mockPrisma.agentRun.count.mockRejectedValue(new Error('DB connection failed'));

    const metrics = await getDashboardMetrics();

    // Should return hardcoded fallback, not throw
    expect(metrics.revenue).toBe(12450);
    expect(metrics.orders).toBe(186);
  });

  it('calculates approval rate correctly', async () => {
    mockPrisma.agentRun.count.mockResolvedValue(0);
    mockPrisma.approval.count.mockResolvedValueOnce(7).mockResolvedValueOnce(10);
    mockPrisma.alert.count.mockResolvedValue(0);
    mockPrisma.order.count.mockResolvedValue(0);
    mockPrisma.order.findMany.mockResolvedValue([]);

    const metrics = await getDashboardMetrics();

    expect(metrics.approvalRate).toBe(70);
  });
});
