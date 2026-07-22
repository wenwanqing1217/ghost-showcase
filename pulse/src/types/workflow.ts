export interface ApprovalPayload {
  workflowType: string;
  data: Record<string, unknown>;
}

export interface WorkflowContext {
  approvalId?: string;
  actor?: 'user' | 'system';
}
