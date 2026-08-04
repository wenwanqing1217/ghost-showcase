/**
 * DS Metrics — Prometheus observability for Ghost DS (Next.js API routes)
 */

import { Counter, Histogram, Gauge, register } from "prom-client";

// ── Metrics Registry ──
export const registry = register;

// ── HTTP Request Metrics ──
export const httpRequestsTotal = new Counter({
  name: "ds_http_requests_total",
  help: "Total DS HTTP requests",
  labelNames: ["method", "route", "status"],
  registers: [registry],
});

export const httpRequestDurationSeconds = new Histogram({
  name: "ds_http_request_duration_seconds",
  help: "DS HTTP request duration in seconds",
  labelNames: ["method", "route"],
  buckets: [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
  registers: [registry],
});

// ── Business Metrics ──
export const ordersTotal = new Counter({
  name: "ds_orders_total",
  help: "Total orders created/updated",
  labelNames: ["action", "status"],
  registers: [registry],
});

export const productsTotal = new Counter({
  name: "ds_products_total",
  help: "Total product sync operations",
  labelNames: ["action", "source"],
  registers: [registry],
});

export const syncOperationsTotal = new Counter({
  name: "ds_sync_operations_total",
  help: "Total sync operations",
  labelNames: ["entity", "status"],
  registers: [registry],
});

export const activeTenants = new Gauge({
  name: "ds_active_tenants",
  help: "Number of active tenants with recent activity",
  registers: [registry],
});

// ── Helper: get metrics content ──
export async function getMetrics(): Promise<string> {
  return registry.metrics();
}
