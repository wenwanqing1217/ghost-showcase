import { describe, it, expect } from 'vitest';
import { approvalSchema, ticketCreateSchema, adsRecommendSchema, validateBody } from '@/lib/validation/schemas';

describe('approvalSchema', () => {
  it('accepts valid approval', () => {
    const result = approvalSchema.safeParse({ approvalId: 'abc123', status: 'approved' });
    expect(result.success).toBe(true);
  });

  it('rejects missing approvalId', () => {
    const result = approvalSchema.safeParse({ status: 'approved' });
    expect(result.success).toBe(false);
  });

  it('rejects empty approvalId', () => {
    const result = approvalSchema.safeParse({ approvalId: '', status: 'approved' });
    expect(result.success).toBe(false);
  });

  it('rejects invalid status', () => {
    const result = approvalSchema.safeParse({ approvalId: 'abc', status: 'invalid' });
    expect(result.success).toBe(false);
  });

  it('accepts all valid statuses', () => {
    for (const status of ['pending', 'approved', 'rejected']) {
      const result = approvalSchema.safeParse({ approvalId: 'abc', status });
      expect(result.success).toBe(true);
    }
  });
});

describe('ticketCreateSchema', () => {
  it('accepts valid ticket', () => {
    const result = ticketCreateSchema.safeParse({ severity: 'error', message: 'Something broke' });
    expect(result.success).toBe(true);
  });

  it('accepts minimal ticket (defaults)', () => {
    const result = ticketCreateSchema.safeParse({ message: 'Help needed' });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.severity).toBe('info');
      expect(result.data.category).toBe('customer_service');
    }
  });

  it('rejects empty message', () => {
    const result = ticketCreateSchema.safeParse({ message: '' });
    expect(result.success).toBe(false);
  });

  it('rejects invalid severity', () => {
    const result = ticketCreateSchema.safeParse({ severity: 'fatal', message: 'test' });
    expect(result.success).toBe(false);
  });

  it('truncates long messages validation', () => {
    const result = ticketCreateSchema.safeParse({ message: 'x'.repeat(2001) });
    expect(result.success).toBe(false);
  });

  it('accepts optional metadata', () => {
    const result = ticketCreateSchema.safeParse({
      message: 'Test',
      metadata: { orderId: '123', tags: ['urgent'] },
    });
    expect(result.success).toBe(true);
  });
});

describe('adsRecommendSchema', () => {
  it('accepts empty object (all optional)', () => {
    const result = adsRecommendSchema.safeParse({});
    expect(result.success).toBe(true);
  });

  it('accepts valid recommendation request', () => {
    const result = adsRecommendSchema.safeParse({
      campaignId: 'camp_123',
      budget: 500,
      goal: 'conversions',
    });
    expect(result.success).toBe(true);
  });

  it('rejects negative budget', () => {
    const result = adsRecommendSchema.safeParse({ budget: -100 });
    expect(result.success).toBe(false);
  });

  it('rejects excessive budget', () => {
    const result = adsRecommendSchema.safeParse({ budget: 2000000 });
    expect(result.success).toBe(false);
  });

  it('rejects invalid goal', () => {
    const result = adsRecommendSchema.safeParse({ goal: 'world_domination' });
    expect(result.success).toBe(false);
  });
});

describe('validateBody helper', () => {
  it('returns success with valid data', () => {
    const result = validateBody(approvalSchema, { approvalId: 'abc', status: 'approved' });
    expect(result.success).toBe(true);
  });

  it('returns errors with invalid data', () => {
    const result = validateBody(approvalSchema, { status: 'invalid' });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.errors.length).toBeGreaterThan(0);
    }
  });
});
