/**
 * Session-based authentication for DS Dashboard.
 * Uses signed httpOnly cookies. No external dependencies.
 */

import { createHash, randomBytes, timingSafeEqual } from 'crypto';

// ── Session store (in-memory; for single-instance demo) ──
interface Session {
  user: string;
  createdAt: number;
}

const SESSIONS = new Map<string, Session>();
const SESSION_TTL_MS = 1000 * 60 * 60 * 8; // 8 hours

// Signing key (regenerated on restart — acceptable for demo)
const SIGNING_KEY = randomBytes(32).toString('hex');

function sign(value: string): string {
  return createHmac('sha256', SIGNING_KEY, value);
}

function createHmac(alg: string, key: string, data: string): string {
  return createHash(alg).update(key + data).digest('hex');
}

function constantTimeCompare(a: string, b: string): boolean {
  const bufA = Buffer.from(a);
  const bufB = Buffer.from(b);
  if (bufA.length !== bufB.length) return false;
  return timingSafeEqual(bufA, bufB);
}

// ── Public API ──

export function createSession(user: string): string {
  const token = randomBytes(32).toString('hex');
  SESSIONS.set(token, { user, createdAt: Date.now() });
  return token;
}

export function validateSession(token: string): Session | null {
  const session = SESSIONS.get(token);
  if (!session) return null;
  if (Date.now() - session.createdAt > SESSION_TTL_MS) {
    SESSIONS.delete(token);
    return null;
  }
  return session;
}

export function destroySession(token: string): void {
  SESSIONS.delete(token);
}

/** Build a signed cookie value: token.signature */
export function buildCookieValue(token: string): string {
  return `${token}.${sign(token)}`;
}

/** Verify and extract token from cookie value */
export function verifyCookieValue(cookieValue: string): string | null {
  const dotIndex = cookieValue.lastIndexOf('.');
  if (dotIndex === -1) return null;
  const token = cookieValue.slice(0, dotIndex);
  const sig = cookieValue.slice(dotIndex + 1);
  const expected = sign(token);
  if (!constantTimeCompare(sig, expected)) return null;
  return token;
}

/** Periodic cleanup (call occasionally) ── */
export function cleanupSessions(): void {
  const now = Date.now();
  for (const [token, session] of SESSIONS) {
    if (now - session.createdAt > SESSION_TTL_MS) {
      SESSIONS.delete(token);
    }
  }
}
