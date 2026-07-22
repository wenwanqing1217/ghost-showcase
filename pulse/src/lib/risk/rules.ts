import { RiskRule, RiskResult } from '@/types/risk';
import { logger } from '@/lib/observability/logger';

export const riskRules: RiskRule[] = [
  {
    id: 'ad-budget-cap',
    severity: 'P1',
    category: 'ads',
    description: 'Daily ad spend must not exceed budget cap',
    check: (ctx) => {
      const spend = Number(ctx.adSpend ?? 0);
      const cap = Number(ctx.adBudgetCap ?? 0);
      return spend > cap;
    },
  },
  {
    id: 'content-banned-words',
    severity: 'P2',
    category: 'content',
    description: 'Product listing must not contain banned words',
    check: (ctx) => {
      const text = String(ctx.text ?? '');
      const banned = ['best', 'guarantee', 'cure', 'miracle'];
      return banned.some((word) => text.toLowerCase().includes(word));
    },
  },
  {
    id: 'price-change-threshold',
    severity: 'P3',
    category: 'product',
    description: 'Price change must be within allowed threshold',
    check: (ctx) => {
      const delta = Number(ctx.priceDeltaPercent ?? 0);
      return Math.abs(delta) > 20;
    },
  },
];

export function evaluateRules(context: Record<string, unknown>): RiskResult[] {
  const results = riskRules.map((rule) => ({
    passed: !rule.check(context),
    severity: rule.severity,
    ruleId: rule.id,
    message: rule.description,
  }));

  const failed = results.filter((r) => !r.passed);
  if (failed.length > 0) {
    logger.warn('Risk rules failed', { rules: failed.map((r) => r.ruleId), context });
  }

  return results;
}
