/**
 * DS Metrics — Prometheus metrics endpoint and middleware
 */

import { NextRequest, NextResponse } from "next/server";
import {
  httpRequestsTotal,
  httpRequestDurationSeconds,
  registry,
} from "@/lib/metrics";

// ── Metrics Middleware ──

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

// ── Metrics Endpoint ──

export async function GET(): Promise<Response> {
  const metrics = await registry.metrics();
  return new Response(metrics, {
    status: 200,
    headers: {
      "Content-Type": registry.contentType,
      "Cache-Control": "no-cache, no-store, must-revalidate",
    },
  });
}
