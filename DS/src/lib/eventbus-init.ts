/**
 * Server-side EventBus initialization
 * 
 * Import this module from any server-side code to ensure
 * the EventBus is initialized once when the Next.js server starts.
 * 
 * Usage: import '@/lib/eventbus-init' from any server-only module.
 * 
 * NOTE: This file must ONLY be imported from server-side code
 * (API routes, server components, etc.). Never import from client components.
 */

import { Redis } from 'ioredis';
import { initEventBus, EventType } from './eventbus';

let initialized = false;

async function initialize() {
  if (initialized) return;

  try {
    const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';
    const redis = new Redis(redisUrl, {
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

// Initialize on import (server-side only)
initialize();
