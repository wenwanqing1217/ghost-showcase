// 共享类型定义

export interface Message {
  role: 'user' | 'assistant' | 'system'
  content: string
}

export interface WorkflowNode {
  id: string
  type: string
  name: string
  config?: Record<string, unknown>
}

export interface Workflow {
  id: string
  name: string
  description: string
  nodes: WorkflowNode[]
  edges: { from: string; to: string }[]
}

export interface WorkflowExecutionResult {
  success: boolean
  workflowId: string
  workflowName: string
  result: string
  steps: ExecutionStep[]
  error?: string
  data?: Record<string, unknown>
}

export interface ExecutionStep {
  nodeId: string
  nodeName: string
  status: 'pending' | 'running' | 'success' | 'error'
  output?: unknown
  error?: string
  duration?: number
  nodeType?: string
  result?: unknown
  startedAt?: number
  finishedAt?: number
}

export interface WorkflowTemplate {
  id: string
  name: string
  description: string
  trigger: {
    type: 'intent' | 'keyword'
    patterns: string[]
  }
  workflow: Workflow
}

export interface ExecuteWorkflowRequest {
  message: string
  userId?: string
}

export interface ExecuteWorkflowResponse {
  success: boolean
  data?: WorkflowExecutionResult
  error?: string
}

export interface LLMConfig {
  provider: string
  model: string
  endpoint: string
  apiKey: string
  maxTokens: number
  temperature: number
  topP: number
}

// Mobile Assistant types
export interface AssistantMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
  metadata?: Record<string, unknown>
}

export interface AssistantSession {
  id: string
  userId?: string
  messages: AssistantMessage[]
  context: Record<string, unknown>
  createdAt: number
  updatedAt: number
}

export interface AssistantCapability {
  id: string
  name: string
  description: string
  enabled: boolean
  icon?: string
}

// Map / Location types
export interface LocationPoint {
  lat: number
  lng: number
  label?: string
  metadata?: Record<string, unknown>
}

export interface MapRoute {
  id: string
  name: string
  points: LocationPoint[]
  createdAt: number
}

export interface GeoContext {
  currentLocation?: LocationPoint
  nearbyPoints: LocationPoint[]
  routes: MapRoute[]
}
