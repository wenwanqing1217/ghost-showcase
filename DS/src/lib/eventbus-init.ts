/**
 * Server-side EventBus initialization for Next.js
 * 
 * This module initializes the EventBus and registers local handlers.
 * Events are published through the Gateway (HTTP), which writes to Redis Streams.
 * Consumption from Redis Streams is handled by OrchestratorEngine (alphaid).
 * 
 * Usage: import '@/lib/eventbus-init' from any server-only module.
 * 
 * NOTE: This file must ONLY be imported from server-side code
 * (API routes, server components, etc.). Never import from client components.
 */

import { initEventBus, getEventBus, EventType } from './eventbus';

let initialized = false;

/**
 * Initialize the EventBus — called automatically on module import.
 * Registers local handlers. Publishing goes through Gateway → Redis.
 * Consumption is handled by OrchestratorEngine via Redis consumer groups.
 */
async function initialize(): Promise<void> {
  if (initialized) return;

  try {
    const eventBus = initEventBus();

    // Register local event handlers (for in-process emitLocal calls)
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

    // Start local handler loop (no-op for Gateway-mediated emit)
    await eventBus.startConsuming();

    initialized = true;
    console.log('[EventBus] Server-side initialization complete (Gateway-mediated)');
  } catch (error) {
    console.error('[EventBus] Server-side initialization failed:', error);
  }
}

/**
 * Ensure EventBus is ready — synchronous check.
 * If not initialized, triggers async initialization.
 */
export function ensureEventBusReady(): void {
  if (!initialized) {
    initialize().catch((e) => console.error('[EventBus] ensureEventBusReady failed:', e));
  }
}

/**
 * Get the EventBus instance — throws if not initialized.
 */
export function getEventBusInstance() {
  if (!initialized) {
    throw new Error('EventBus not initialized. Call ensureEventBusReady() first.');
  }
  return getEventBus();
}

/**
 * Shutdown the EventBus — no-op (no persistent connections to close).
 */
export function shutdownEventBus(): void {
  initialized = false;
  console.log('[EventBus] Shutdown complete');
}
