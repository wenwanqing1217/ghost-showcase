/**
 * DS Metrics — Prometheus observability for Ghost DS (Next.js API routes)
 */

import { Counter, Histogram, Gauge, register } from "prom-client";
import type { NextRequest, NextResponse } from "next/server";

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

// ── Metrics Middleware ──
// 放在 lib（非路由文件），遵守 Next.js 路由文件只允许导出 HTTP 方法的规定

export function withMetrics<T extends unknown[]>(
  handler: (req: NextRequest, ...args: T) => Promise<NextResponse>,
  routePattern: string,
) {
  return async (req: NextRequest, ...args: T): Promise<NextResponse> => {
    const start = Date.now();
    const method = req.method;

    try {
      const response = await handler(req, ...args);
      const duration = (Date.now() - start) / 1000;
      const status = response.status;

      httpRequestsTotal.labels(method, routePattern, String(status)).inc();
      httpRequestDurationSeconds.labels(method, routePattern).observe(duration);

      return response;
    } catch (error) {
      const duration = (Date.now() - start) / 1000;
      httpRequestsTotal.labels(method, routePattern, "500").inc();
      httpRequestDurationSeconds.labels(method, routePattern).observe(duration);
      throw error;
    }
  };
}
