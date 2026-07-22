/**
 * Service Auth 中间件测试
 */

import { describe, it, expect } from 'vitest';
import { NextRequest } from 'next/server';
import { validateServiceKey } from './service-auth';

const VALID_KEY = 'test-service-key-abc123';

describe('validateServiceKey', () => {
  const originalKey = process.env.DS_API_KEY;

  beforeEach(() => {
    process.env.DS_API_KEY = VALID_KEY;
  });

  afterEach(() => {
    if (originalKey !== undefined) {
      process.env.DS_API_KEY = originalKey;
    } else {
      delete process.env.DS_API_KEY;
    }
  });

  it('should accept valid service key', () => {
    const request = new NextRequest('http://localhost/api/webhooks/mindflow-map', {
      headers: { 'x-service-key': VALID_KEY },
    });

    const result = validateServiceKey(request);
    expect(result.valid).toBe(true);
  });

  it('should reject missing header', () => {
    const request = new NextRequest('http://localhost/api/webhooks/mindflow-map');

    const result = validateServiceKey(request);
    expect(result.valid).toBe(false);
    expect(result.error).toContain('Missing');
  });

  it('should reject invalid key', () => {
    const request = new NextRequest('http://localhost/api/webhooks/mindflow-map', {
      headers: { 'x-service-key': 'wrong-key' },
    });

    const result = validateServiceKey(request);
    expect(result.valid).toBe(false);
    expect(result.error).toContain('Invalid');
  });

  it('should reject when DS_API_KEY not configured', () => {
    delete process.env.DS_API_KEY;

    const request = new NextRequest('http://localhost/api/webhooks/mindflow-map', {
      headers: { 'x-service-key': 'any-key' },
    });

    const result = validateServiceKey(request);
    expect(result.valid).toBe(false);
    expect(result.error).toContain('not configured');
  });

  it('should be case-insensitive for header name', () => {
    const request = new NextRequest('http://localhost/api/webhooks/mindflow-map', {
      headers: { 'X-Service-Key': VALID_KEY },
    });

    const result = validateServiceKey(request);
    expect(result.valid).toBe(true);
  });
});
