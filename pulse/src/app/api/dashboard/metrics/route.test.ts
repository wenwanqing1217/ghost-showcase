import { describe, it, expect } from 'vitest';
import { GET } from '@/app/api/dashboard/metrics/route';

describe('Dashboard Metrics API', () => {
  it('returns metrics object', async () => {
    const request = new Request('http://localhost/api/dashboard/metrics', {
      headers: new Headers({ 'x-forwarded-for': '127.0.0.1' }),
    });
    const res = await GET(request);
    const json = await res.json();
    expect(json.success).toBe(true);
    expect(json.data).toHaveProperty('agentRunsToday');
    expect(json.data).toHaveProperty('approvalRate');
    expect(json.data).toHaveProperty('p1Alerts');
  });
});
