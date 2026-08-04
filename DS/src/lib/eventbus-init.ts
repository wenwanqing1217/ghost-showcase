/**
 * Server-side EventBus initialization for Next.js
 * 
 * This module initializes the EventBus and starts consumers
 * when the Next.js server process starts. Import this module
 * from any server-side code to ensure it runs once.
 * 
 * Usage: import '@/lib/eventbus-init' from any server-only module.
 * 
 * NOTE: This file must ONLY be imported from server-side code
 * (API routes, server components, etc.). Never import from client components.
 */

import { Redis } from 'ioredis';
import { initEventBus, getEventBus, EventType } from './eventbus';

let initialized = false;
let redis: Redis | null = null;

/**
 * Initialize the EventBus — called automatically on module import.
 * Creates Redis connection, registers handlers, starts consumer loop.
 */
async function initialize(): Promise<void> {
  if (initialized) return;

  try {
    const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';
    redis = new Redis(redisUrl, {
      retryStrategy: (times) => Math.min(times * 200, 2000),
      maxRetriesPerRequest: 3,
      lazyConnect: true,
    });

    const eventBus = initEventBus(redis);
    
    // Register event handlers for fulfillment
    eventBus.on(EventType.ORDER_CREATED, async (event) => {
      console.log('[EventBus] order:created:', event.id);
    });
    eventBus.on(EventType.ORDER_PAID, async (event) => {
      console.log('[EventBus] order:paid:', event.id);
    });
    eventBus.on(EventType.ORDER_FULFILLED, async (event) => {
      console.log('[EventBus] order:fulfilled:', event.id);
    });
    eventBus.on(EventType.ORDER_REFUNDED, async (event) => {
      console.log('[EventBus] order:refunded:', event.id);
    });
    eventBus.on(EventType.ORDER_CANCELLED, async (event) => {
      console.log('[EventBus] order:cancelled:', event.id);
    });
    eventBus.on(EventType.SUPPLY_INVENTORY_UPDATED, async (event) => {
      console.log('[EventBus] supply:inventory:updated:', event.id);
    });

    // Connect to Redis
    await redis.connect();

    // Start consuming events (activates consumer groups + XREADGROUP loop)
    await eventBus.startConsuming();

    initialized = true;
    console.log('[EventBus] Server-side initialization complete');
  } catch (error) {
    console.error('[EventBus] Server-side initialization failed:', error);
  }
}

/**
 * Ensure EventBus is ready — synchronous check.
 * If not initialized, triggers async initialization.
 * (Merged from eventbus-server.ts for backward compat)
 */
export function ensureEventBusReady(): void {
  if (!initialized) {
    initialize().catch((e) => console.error('[EventBus] ensureEventBusReady failed:', e));
  }
}

/**
 * Get the EventBus instance — throws if not initialized.
 * (Merged from eventbus-server.ts for backward compat)
 */
export function getEventBusInstance() {
  if (!initialized) {
    throw new Error('EventBus not initialized. Call ensureEventBusReady() first.');
  }
  return getEventBus();
}

/**
 * Shutdown the EventBus — disconnect Redis.
 * (Merged from eventbus-server.ts for backward compat)
 */
export function shutdownEventBus(): void {
  if (redis) {
    redis.disconnect();
    redis = null;
  }
  initialized = false;
}

// Initialize on import (server-side only)
initialize();
