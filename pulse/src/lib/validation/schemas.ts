/**
 * Zod validation schemas for DS API routes.
 * Centralized to ensure consistent input validation.
 */

import { z } from 'zod';

// ── Content Approval ──

export const approvalSchema = z.object({
  approvalId: z.string().min(1, 'approvalId is required').max(128),
  status: z.enum(['pending', 'approved', 'rejected'], {
    errorMap: () => ({ message: 'status must be one of: pending, approved, rejected' }),
  }),
});

// ── CS Tickets ──

export const ticketCreateSchema = z.object({
  severity: z.enum(['info', 'warning', 'error', 'critical']).default('info'),
  category: z.string().max(64).default('customer_service'),
  message: z.string().min(1, 'message is required').max(2000),
  metadata: z.record(z.unknown()).optional(),
});

export const ticketQuerySchema = z.object({
  status: z.enum(['info', 'warning', 'error', 'critical']).optional(),
});

// ── Ads ──

export const adsRecommendSchema = z.object({
  campaignId: z.string().max(128).optional(),
  budget: z.number().positive().max(1000000).optional(),
  goal: z.enum(['awareness', 'traffic', 'conversions', 'revenue']).optional(),
});

// ── Common helpers ──

export function validateBody<T>(schema: z.ZodSchema<T>, body: unknown): { success: true; data: T } | { success: false; errors: string[] } {
  const result = schema.safeParse(body);
  if (result.success) {
    return { success: true, data: result.data };
  }
  return {
    success: false,
    errors: result.error.errors.map((e) => `${e.path.join('.')}: ${e.message}`),
  };
}
