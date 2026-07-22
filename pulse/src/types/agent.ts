export interface AgentInput {
  type: 'content' | 'ads' | 'cs' | 'product';
  payload: Record<string, unknown>;
}

export interface AgentOutput {
  success: boolean;
  data?: unknown;
  error?: string;
}

export interface BaseAgent {
  type: string;
  execute(input: AgentInput): Promise<AgentOutput>;
}
