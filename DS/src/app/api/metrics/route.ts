/**
 * DS Metrics — Prometheus metrics endpoint
 */

import { getMetrics } from "@/lib/metrics";

// ── Metrics Endpoint ──

export async function GET(): Promise<Response> {
  const metrics = await getMetrics();
  return new Response(metrics, {
    status: 200,
    headers: {
      "Content-Type": "text/plain",
      "Cache-Control": "no-cache, no-store, must-revalidate",
    },
  });
}
