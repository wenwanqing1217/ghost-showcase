export interface ShopifyProduct {
  id: string;
  title: string;
  bodyHtml?: string;
  tags?: string;
  status: string;
  vendor?: string;
  product_type?: string;
  createdAt?: string;
}

export interface ShopifyOrder {
  id: string;
  orderNumber?: number;
  totalPrice: string;
  currency: string;
  fulfillmentStatus?: string;
  createdAt: string;
  customer?: {
    firstName?: string;
    lastName?: string;
    email?: string;
  };
  lineItems?: Array<{
    id: number;
    title: string;
    quantity: number;
    price: string;
  }>;
  riskLevel?: string;
}

export interface ProductInput {
  title: string;
  category: string;
  keywords: string[];
  brief: string;
}

export interface ListingDraft {
  title: string;
  description: string;
  tags: string[];
  faqs: { question: string; answer: string }[];
}

export interface AgentRunRecord {
  id: string;
  agentType: string;
  input: string;
  output: string;
  status: string;
  durationMs?: number;
  createdAt: string;
}

export interface ApprovalRecord {
  id: string;
  workflowType: string;
  status: string;
  payload: string;
  result?: string;
  createdAt: string;
  decidedAt?: string;
}

export interface AlertRecord {
  id: string;
  severity: 'P1' | 'P2' | 'P3';
  category: string;
  message: string;
  metadata?: string;
  resolved: boolean;
  createdAt: string;
}

export interface DashboardMetrics {
  revenue: number;
  orders: number;
  avgOrderValue: number;
  agentRunsToday: number;
  approvalRate: number;
  p1Alerts: number;
}

export type WorkflowStatus = 'pending' | 'approved' | 'rejected';
