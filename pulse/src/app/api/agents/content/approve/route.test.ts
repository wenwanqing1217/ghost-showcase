import { describe, it, expect } from 'vitest';
import { POST } from '@/app/api/agents/content/approve/route';

describe('Content Approve API', () => {
  it('rejects missing approvalId', async () => {
    const res = await POST(new Request('http://localhost', { method: 'POST', body: JSON.stringify({ status: 'approved' }) }));
    const json = await res.json();
    expect(res.status).toBe(400);
    expect(json.success).toBe(false);
  });
});
