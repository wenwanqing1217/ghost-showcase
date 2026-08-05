import { describe, it, expect, vi, beforeEach } from 'vitest';
import { EventBus, EventType, initEventBus, getEventBus } from '../lib/eventbus';

describe('EventBus', () => {
  beforeEach(() => {
    vi.resetModules();
    global.fetch = undefined as any;
  });

  describe('initEventBus / getEventBus', () => {
    it('should create and return singleton instance', async () => {
      const { initEventBus: init, getEventBus: get } = await import('../lib/eventbus');
      const a = init();
      const b = get();
      expect(a).toBe(b);
    });
  });

  describe('EventType', () => {
    it('should have all required event types defined', () => {
      expect(EventType.ORDER_CREATED).toBe('order:created');
      expect(EventType.ORDER_PAID).toBe('order:paid');
      expect(EventType.ORDER_REFUNDED).toBe('order:refunded');
      expect(EventType.SUPPLY_INVENTORY_UPDATED).toBe('supply:inventory:updated');
      expect(EventType.FULFILLMENT_TASK_CREATED).toBe('fulfillment:task:created');
      expect(EventType.SYSTEM_ALERT).toBe('system:alert');
    });
  });

  describe('publish', () => {
    it('should generate unique event IDs', async () => {
      const bus = initEventBus();
      let callCount = 0;
      global.fetch = vi.fn(() => {
        callCount++;
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ event_id: `mock-${callCount}` }),
        } as Response);
      });

      const id1 = await bus.publish(EventType.ORDER_CREATED, { test: 1 }, { tenantId: 't1' });
      const id2 = await bus.publish(EventType.ORDER_CREATED, { test: 2 }, { tenantId: 't1' });
      expect(id1).not.toBe(id2);
    });

    it('should POST to Gateway /api/v1/internal/events/emit', async () => {
      const bus = initEventBus();
      const mockFetch = vi.fn(() =>
        Promise.resolve({ ok: true, json: () => Promise.resolve({ event_id: 'gw-1' }) } as Response)
      );
      global.fetch = mockFetch;

      await bus.publish(EventType.ORDER_PAID, { amount: 100 }, { tenantId: 't1' });

      expect(mockFetch).toHaveBeenCalledTimes(1);
      const [url, options] = mockFetch.mock.calls[0];
      expect(url).toBe('/api/v1/internal/events/emit');
      expect(options.method).toBe('POST');
      expect(JSON.parse(options.body)).toMatchObject({
        type: 'order:paid',
        data: { amount: 100 },
        source: 'unknown',
        tenantId: 't1',
      });
    });

    it('should include source when provided', async () => {
      const bus = initEventBus();
      const mockFetch = vi.fn(() =>
        Promise.resolve({ ok: true, json: () => Promise.resolve({ event_id: 'gw-2' }) } as Response)
      );
      global.fetch = mockFetch;

      await bus.publish(EventType.SUPPLY_PRICE_CHANGED, { price: 50 }, {
        tenantId: 't1',
        source: 'webhook',
      });

      const body = JSON.parse(mockFetch.mock.calls[0][1].body);
      expect(body.source).toBe('webhook');
    });

    it('should handle Gateway unreachable gracefully', async () => {
      const bus = initEventBus();
      global.fetch = vi.fn(() => Promise.reject(new Error('ECONNREFUSED')));

      const consoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => {});
      const id = await bus.publish(EventType.SYSTEM_ALERT, { msg: 'x' }, { tenantId: 't1' });

      expect(consoleWarn).toHaveBeenCalled();
      expect(id).toBeDefined();
      consoleWarn.mockRestore();
    });
  });

  describe('on / emitLocal', () => {
    it('should register and invoke local handlers', async () => {
      const bus = initEventBus();
      const handler = vi.fn(async () => {});

      bus.on(EventType.ORDER_CREATED, handler);

      const event = { id: 'e1', type: EventType.ORDER_CREATED, tenantId: 't1', data: {}, timestamp: Date.now(), source: 'test' };
      await bus.emitLocal(EventType.ORDER_CREATED, event);

      expect(handler).toHaveBeenCalledTimes(1);
      expect(handler).toHaveBeenCalledWith(event);
    });

    it('should return unsubscribe function', async () => {
      const bus = initEventBus();
      const handler = vi.fn(async () => {});

      const unsub = bus.on(EventType.ORDER_CREATED, handler);
      await bus.emitLocal(EventType.ORDER_CREATED, { id: 'e1', type: EventType.ORDER_CREATED, tenantId: 't1', data: {}, timestamp: Date.now(), source: 'test' });
      expect(handler).toHaveBeenCalledTimes(1);

      unsub();
      await bus.emitLocal(EventType.ORDER_CREATED, { id: 'e2', type: EventType.ORDER_CREATED, tenantId: 't1', data: {}, timestamp: Date.now(), source: 'test' });
      expect(handler).toHaveBeenCalledTimes(1); // no additional call
    });

    it('should handle handler errors without crashing', async () => {
      const bus = initEventBus();
      const errorHandler = vi.fn(async () => { throw new Error('handler fail'); });
      const okHandler = vi.fn(async () => {});

      bus.on(EventType.SYSTEM_TASK_FAILED, errorHandler);
      bus.on(EventType.SYSTEM_TASK_FAILED, okHandler);

      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
      await bus.emitLocal(EventType.SYSTEM_TASK_FAILED, { id: 'e1', type: EventType.SYSTEM_TASK_FAILED, tenantId: 't1', data: {}, timestamp: Date.now(), source: 'test' });

      expect(errorHandler).toHaveBeenCalled();
      expect(okHandler).toHaveBeenCalled(); // second handler still runs
      consoleError.mockRestore();
    });
  });

  describe('startConsuming / stopConsuming', () => {
    it('should be no-ops (Gateway-mediated emit)', async () => {
      const bus = initEventBus();
      await expect(bus.startConsuming()).resolves.toBeUndefined();
      await expect(bus.stopConsuming()).resolves.toBeUndefined();
    });
  });
});
