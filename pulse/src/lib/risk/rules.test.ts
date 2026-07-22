import { describe, it, expect } from 'vitest';
import { evaluateRules } from '@/lib/risk/rules';

describe('Risk Rules', () => {
  // ── Ad Budget Cap ──
  describe('ad-budget-cap', () => {
    it('flags ad budget overrun', () => {
      const results = evaluateRules({ adSpend: 100, adBudgetCap: 50 });
      expect(results.find((r) => r.ruleId === 'ad-budget-cap')?.passed).toBe(false);
    });

    it('passes when spend is within budget', () => {
      const results = evaluateRules({ adSpend: 30, adBudgetCap: 50 });
      expect(results.find((r) => r.ruleId === 'ad-budget-cap')?.passed).toBe(true);
    });

    it('passes when spend equals budget', () => {
      const results = evaluateRules({ adSpend: 50, adBudgetCap: 50 });
      expect(results.find((r) => r.ruleId === 'ad-budget-cap')?.passed).toBe(true);
    });

    it('passes when no spend data', () => {
      const results = evaluateRules({});
      expect(results.find((r) => r.ruleId === 'ad-budget-cap')?.passed).toBe(true);
    });
  });

  // ── Banned Words ──
  describe('content-banned-words', () => {
    it('flags banned word "best"', () => {
      const results = evaluateRules({ text: 'This is the best product ever!' });
      expect(results.find((r) => r.ruleId === 'content-banned-words')?.passed).toBe(false);
    });

    it('flags banned word "guarantee"', () => {
      const results = evaluateRules({ text: 'We guarantee results' });
      expect(results.find((r) => r.ruleId === 'content-banned-words')?.passed).toBe(false);
    });

    it('is case insensitive', () => {
      const results = evaluateRules({ text: 'This is the BEST product' });
      expect(results.find((r) => r.ruleId === 'content-banned-words')?.passed).toBe(false);
    });

    it('passes clean content', () => {
      const results = evaluateRules({ text: 'A quality product for daily use' });
      expect(results.find((r) => r.ruleId === 'content-banned-words')?.passed).toBe(true);
    });

    it('passes empty text', () => {
      const results = evaluateRules({ text: '' });
      expect(results.find((r) => r.ruleId === 'content-banned-words')?.passed).toBe(true);
    });
  });

  // ── Price Change ──
  describe('price-change-threshold', () => {
    it('flags price increase above threshold', () => {
      const results = evaluateRules({ priceDeltaPercent: 30 });
      expect(results.find((r) => r.ruleId === 'price-change-threshold')?.passed).toBe(false);
    });

    it('flags price decrease above threshold', () => {
      const results = evaluateRules({ priceDeltaPercent: -25 });
      expect(results.find((r) => r.ruleId === 'price-change-threshold')?.passed).toBe(false);
    });

    it('passes change within threshold', () => {
      const results = evaluateRules({ priceDeltaPercent: 15 });
      expect(results.find((r) => r.ruleId === 'price-change-threshold')?.passed).toBe(true);
    });

    it('passes change at exact threshold', () => {
      const results = evaluateRules({ priceDeltaPercent: 20 });
      expect(results.find((r) => r.ruleId === 'price-change-threshold')?.passed).toBe(true);
    });
  });

  // ── Combined ──
  describe('evaluateRules combined', () => {
    it('returns results for all rules', () => {
      const results = evaluateRules({});
      expect(results).toHaveLength(3);
    });

    it('returns severity for each result', () => {
      const results = evaluateRules({});
      results.forEach((r) => {
        expect(r.severity).toBeDefined();
        expect(['P1', 'P2', 'P3']).toContain(r.severity);
      });
    });
  });
});
