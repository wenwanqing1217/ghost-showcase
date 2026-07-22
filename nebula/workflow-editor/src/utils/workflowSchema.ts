import yaml from 'js-yaml'

export type WorkflowNodeType = 'start' | 'end' | 'tool' | 'condition'

export interface WorkflowNodeData {
  id: string
  type: WorkflowNodeType
  label: string
  tool?: string
  description?: string
  config?: Record<string, unknown>
}

export interface WorkflowEdgeData {
  id: string
  source: string
  target: string
  label?: string
}

export interface WorkflowDefinition {
  id: string
  name: string
  version: string
  description?: string
  triggers: string[]
  nodes: Array<{
    id: string
    type: string
    label: string
    tool?: string
    description?: string
    config?: Record<string, unknown>
  }>
  edges: Array<{
    id: string
    source: string
    target: string
    label?: string
  }>
}

export function nodesToReactFlow(nodes: WorkflowDefinition['nodes']) {
  return nodes.map((node) => ({
    id: node.id,
    type: node.type === 'condition' ? 'condition' : node.type === 'tool' ? 'tool' : node.type,
    position: { x: 0, y: 0 },
    data: {
      label: node.label,
      tool: node.tool,
      description: node.description,
      config: node.config,
    },
  }))
}

export function edgesToReactFlow(edges: WorkflowDefinition['edges']) {
  return edges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    label: edge.label,
    type: 'smoothstep',
  }))
}

export function reactFlowToWorkflow(
  nodes: Array<{ id: string; type: string; position: { x: number; y: number }; data: Record<string, unknown> }>,
  edges: Array<{ id: string; source: string; target: string; label?: string }>,
  meta: { id: string; name: string; version: string; description?: string; triggers: string[] },
): WorkflowDefinition {
  return {
    id: meta.id,
    name: meta.name,
    version: meta.version,
    description: meta.description,
    triggers: meta.triggers,
    nodes: nodes.map((node) => ({
      id: node.id,
      type: node.type,
      label: (node.data.label as string) || node.id,
      tool: node.data.tool as string | undefined,
      description: node.data.description as string | undefined,
      config: (node.data.config as Record<string, unknown>) || {},
    })),
    edges: edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: edge.label,
    })),
  }
}

export function workflowToYaml(workflow: WorkflowDefinition): string {
  return yaml.dump(workflow, {
    indent: 2,
    lineWidth: 120,
    noRefs: true,
  })
}

export function yamlToWorkflow(content: string): WorkflowDefinition {
  const parsed = yaml.load(content) as WorkflowDefinition
  if (!parsed || typeof parsed !== 'object' || !('id' in parsed) || !('nodes' in parsed)) {
    throw new Error('Invalid workflow YAML')
  }
  return parsed as WorkflowDefinition
}

export const TOOL_OPTIONS = [
  { value: 'map', label: '地图导航', icon: '🗺️' },
  { value: 'douyin', label: '抖音发布', icon: '🎬' },
  { value: 'shopify', label: 'Shopify 优化', icon: '🛍️' },
  { value: 'shortdramas', label: '短剧预审', icon: '🎭' },
  { value: 'feishu', label: '飞书通知', icon: '💬' },
  { value: 'wechat', label: '微信消息', icon: '📱' },
]
