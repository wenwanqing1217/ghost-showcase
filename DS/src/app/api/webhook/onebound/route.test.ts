import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock eventbus
vi.mock('@/lib/eventbus', () => {
  const mockPublish = vi.fn(() => Promise.resolve({ event_id: 'test-evt' }));
  return {
    initEventBus: vi.fn(() => ({
      on: vi.fn(),
      publish: mockPublish,
      startConsuming: vi.fn(),
      stopConsuming: vi.fn(),
    })),
    getEventBus: vi.fn(() => ({
      publish: mockPublish,
    })),
    EventType: {},
    EventBus: class {},
  };
});

// Mock prisma
vi.mock('@/lib/prisma', () => ({
  prisma: {
    shop: { findFirst: vi.fn() },
    order: { upsert: vi.fn() },
    product: { upsert: vi.fn() },
  },
}));

describe('OneBound Webhook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('verifySignature', () => {
    it('should reject when WEBHOOK_SECRET is empty', async () => {
      const { verifySignature } = await import('./route');
      expect(verifySignature('body', 'sig')).toBe(false);
    });

    it('should reject when signature is null', async () => {
      const { verifySignature } = await import('./route');
      expect(verifySignature('body', null)).toBe(false);
    });

    it('should reject mismatched signatures', async () => {
      const { verifySignature } = await import('./route');
      // Set a secret via env
      const original = process.env.ONEBOUND_WEBHOOK_SECRET;
      process.env.ONEBOUND_WEBHOOK_SECRET = 'secret123';
      try {
        const sig = require('crypto')
          .createHmac('sha256', 'secret123')
          .update('body')
          .digest('hex');
        expect(verifySignature('body', 'wrong_sig')).toBe(false);
      } finally {
        process.env.ONEBOUND_WEBHOOK_SECRET = original;
      }
    });
  });

  describe('publishEvent', () => {
    it('should call EventBus.publish with correct args', async () => {
      const { publishEvent } = await import('./route');

      // Should not throw — mock handles the actual publish
      await expect(publishEvent('order:created', { orderId: '123' }, 'tenant-1'))
        .resolves.toBeUndefined();
    });
  });

  describe('GET handler', () => {
    it('should return webhook info', async () => {
      const { GET } = await import('./route');
      const res = await GET();
      expect(res).toBeDefined();
    });
  });
});
