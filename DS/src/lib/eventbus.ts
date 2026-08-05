/**
 * Event Bus — Gateway-mediated event distribution (simplified)
 *
 * Architecture change:
 *   Before: DS connects directly to Redis Streams (ioredis required)
 *   After:  DS POSTs events to Gateway → Gateway writes to Redis Streams
 *
 * This eliminates the direct Redis dependency from the DS service,
 * reducing infrastructure coupling and simplifying deployment.
 *
 * Event Flow:
 *  货源库存变化 → DS POST /v1/internal/events/emit → Gateway → Redis Stream → OrchestratorEngine
 *  订单支付成功 → DS POST /v1/internal/events/emit → Gateway → Redis Stream → OrchestratorEngine
 */

// ── Event Types ──

// Runtime event type values (for use as EventBus.on(EventType.ORDER_CREATED, ...))
export const EventType = {
  SUPPLY_INVENTORY_UPDATED: 'supply:inventory:updated',
  SUPPLY_PRICE_CHANGED: 'supply:price:changed',
  SUPPLY_PRODUCTS_FETCHED: 'supply:products:fetched',
  SUPPLY_PRODUCT_ADDED: 'supply:product:added',
  ORDER_CREATED: 'order:created',
  ORDER_PAID: 'order:paid',
  ORDER_FULFILLED: 'order:fulfilled',
  ORDER_REFUNDED: 'order:refunded',
  ORDER_CANCELLED: 'order:cancelled',
  FULFILLMENT_TASK_CREATED: 'fulfillment:task:created',
  FULFILLMENT_TASK_COMPLETED: 'fulfillment:task:completed',
  FULFILLMENT_TASK_FAILED: 'fulfillment:task:failed',
  SYNC_STARTED: 'sync:started',
  SYNC_COMPLETED: 'sync:completed',
  SYNC_FAILED: 'sync:failed',
  SYSTEM_ALERT: 'system:alert',
  SYSTEM_QUOTA_EXCEEDED: 'system:quota:exceeded',
  SYSTEM_TASK_FAILED: 'system:task:failed',
} as const;

// TypeScript type for EventType values
export type EventTypeStr = typeof EventType[keyof typeof EventType];

export interface Event {
  id: string;
  type: EventTypeStr;
  tenantId: string;
  data: Record<string, unknown>;
  timestamp: number;
  source: string;
  correlationId?: string;
}

export interface EventBusConfig {
  /** Gateway base URL (default: /api/v1) */
  gatewayPrefix?: string;
}

const DEFAULT_GATEWAY_PREFIX = '/api/v1';

// ── Event Bus Core (simplified — Gateway-mediated emit) ──

export class EventBus {
  private gatewayPrefix: string;
  private handlers: Map<EventTypeStr, Set<(event: Event) => Promise<void>>>;
  private running = false;

  constructor(config: Partial<EventBusConfig> = {}) {
    this.gatewayPrefix = config.gatewayPrefix || DEFAULT_GATEWAY_PREFIX;
    this.handlers = new Map();
  }

  // ── Publishing (via Gateway HTTP) ──

  /**
   * Publish an event through the Gateway.
   * Gateway writes to Redis Streams on behalf of DS.
   */
  async publish(type: EventTypeStr, data: Record<string, unknown>, options: {
    tenantId: string;
    source?: string;
    correlationId?: string;
  }): Promise<string> {
    const event: Event = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
      type,
      tenantId: options.tenantId,
      data,
      timestamp: Date.now(),
      source: options.source || 'unknown',
      correlationId: options.correlationId,
    };

    try {
      const res = await fetch(`${this.gatewayPrefix}/internal/events/emit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: event.type,
          data: event.data,
          source: event.source,
          tenantId: event.tenantId,
        }),
      });

      if (!res.ok) {
        console.warn(`[EventBus] Gateway emit failed: ${res.status} ${res.statusText}`);
        return event.id;
      }

      const result = await res.json();
      return result.event_id || event.id;
    } catch (e) {
      console.warn(`[EventBus] Cannot reach Gateway: ${e}`);
      return event.id;
    }
  }

  /**
   * Publish multiple events through the Gateway.
   */
  async publishBatch(events: Array<{
    type: EventTypeStr;
    data: Record<string, unknown>;
    tenantId: string;
    source?: string;
    correlationId?: string;
  }>): Promise<string[]> {
    const results: string[] = [];
    for (const evt of events) {
      results.push(await this.publish(evt.type, evt.data, {
        tenantId: evt.tenantId,
        source: evt.source,
        correlationId: evt.correlationId,
      }));
    }
    return results;
  }

  // ── Subscription (local handlers, no Redis consumer) ──

  /**
   * Subscribe to events of a specific type.
   * Handlers are invoked locally when emitLocal() is called.
   * For cross-service events, use publish() which goes through Gateway → Redis.
   */
  on(type: EventTypeStr, handler: (event: Event) => Promise<void>): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }
    this.handlers.get(type)!.add(handler);

    // Return unsubscribe function
    return () => {
      this.handlers.get(type)?.delete(handler);
    };
  }

  /**
   * Emit an event to local handlers only (no Gateway call).
   * Useful for in-process event handling within DS.
   */
  async emitLocal(type: EventTypeStr, event: Event): Promise<void> {
    const handlers = this.handlers.get(type);
    if (!handlers || handlers.size === 0) return;

    const promises: Promise<void>[] = [];
    for (const handler of handlers) {
      promises.push(
        handler(event).catch(err => console.error(`[EventBus] Handler error for ${type}:`, err))
      );
    }
    await Promise.all(promises);
  }

  // ── Lifecycle (no-op — consumption happens in OrchestratorEngine via Redis) ──

  /**
   * Start consuming events.
   * NOTE: DS no longer consumes from Redis directly.
   * Consumption is handled by OrchestratorEngine (alphaid) via Redis consumer groups.
   * This method is a no-op for backward compatibility.
   */
  async startConsuming(): Promise<void> {
    if (this.running) return;
    this.running = true;
    console.log('[EventBus] DS EventBus started (Gateway-mediated emit, no local consumer)');
  }

  /**
   * Stop consuming events (no-op).
   */
  async stopConsuming(): Promise<void> {
    this.running = false;
  }
}

// ── Singleton ──


let _eventBus: EventBus | null = null;

export function initEventBus(config?: Partial<EventBusConfig>): EventBus {
  _eventBus = new EventBus(config);
  return _eventBus;
}

export function getEventBus(): EventBus {
  if (!_eventBus) {
    _eventBus = new EventBus();
  }
  return _eventBus;
}
