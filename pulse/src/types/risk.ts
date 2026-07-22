export interface RiskRule {
  id: string;
  severity: 'P1' | 'P2' | 'P3';
  category: string;
  description: string;
  check: (context: Record<string, unknown>) => boolean;
}

export interface RiskResult {
  passed: boolean;
  severity: 'P1' | 'P2' | 'P3';
  ruleId: string;
  message: string;
}
