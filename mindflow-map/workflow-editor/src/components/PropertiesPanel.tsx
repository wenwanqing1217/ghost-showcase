import type { WorkflowDefinition } from '../utils/workflowSchema'

type WorkflowMeta = Pick<WorkflowDefinition, 'id' | 'name' | 'version' | 'description' | 'triggers'>

type PropertiesPanelProps = {
  selectedNode: Record<string, unknown> | null
  onUpdateNode: (updates: Record<string, unknown>) => void
  workflowMeta: WorkflowMeta
  onUpdateMeta: (meta: WorkflowMeta) => void
}

function getNodeLabel(node: Record<string, unknown>): string {
  const data = node.data as Record<string, unknown> | undefined
  return (data?.label as string) || (node.id as string) || ''
}

function getNodeType(node: Record<string, unknown>): string {
  return (node.type as string) || ''
}

function getNodeId(node: Record<string, unknown>): string {
  return (node.id as string) || ''
}

function getNodeTool(node: Record<string, unknown>): string {
  const data = node.data as Record<string, unknown> | undefined
  return (data?.tool as string) || ''
}

export function PropertiesPanel({ selectedNode, onUpdateNode, workflowMeta, onUpdateMeta }: PropertiesPanelProps) {
  return (
    <aside className="w-72 border-l border-mindflow-border bg-mindflow-surface p-4">
      <div className="mb-4">
        <div className="text-sm font-semibold text-slate-200">工作流属性</div>
        <div className="mt-2 flex flex-col gap-2">
          <label className="flex flex-col gap-1">
            <span className="text-[11px] text-slate-400">名称</span>
            <input
              value={workflowMeta.name}
              onChange={(e) => onUpdateMeta({ ...workflowMeta, name: e.target.value })}
              className="rounded-md border border-mindflow-border bg-mindflow-bg px-2 py-1 text-xs text-slate-200 outline-none focus:border-mindflow-accent"
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-[11px] text-slate-400">描述</span>
            <textarea
              value={workflowMeta.description || ''}
              onChange={(e) => onUpdateMeta({ ...workflowMeta, description: e.target.value })}
              className="h-16 rounded-md border border-mindflow-border bg-mindflow-bg px-2 py-1 text-xs text-slate-200 outline-none focus:border-mindflow-accent"
            />
          </label>
        </div>
      </div>

      <div>
        <div className="text-sm font-semibold text-slate-200">节点属性</div>
        {selectedNode ? (
          <div className="mt-2 flex flex-col gap-2">
            <label className="flex flex-col gap-1">
              <span className="text-[11px] text-slate-400">标签</span>
              <input
                value={getNodeLabel(selectedNode)}
                onChange={(e) => onUpdateNode({ label: e.target.value })}
                className="rounded-md border border-mindflow-border bg-mindflow-bg px-2 py-1 text-xs text-slate-200 outline-none focus:border-mindflow-accent"
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-[11px] text-slate-400">类型</span>
              <input
                value={getNodeType(selectedNode)}
                disabled
                className="rounded-md border border-mindflow-border bg-mindflow-bg px-2 py-1 text-xs text-slate-500"
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-[11px] text-slate-400">ID</span>
              <input
                value={getNodeId(selectedNode)}
                disabled
                className="rounded-md border border-mindflow-border bg-mindflow-bg px-2 py-1 text-xs text-slate-500"
              />
            </label>
            {getNodeType(selectedNode) === 'tool' && (
              <label className="flex flex-col gap-1">
                <span className="text-[11px] text-slate-400">工具</span>
                <select
                  value={getNodeTool(selectedNode)}
                  onChange={(e) => onUpdateNode({ tool: e.target.value })}
                  className="rounded-md border border-mindflow-border bg-mindflow-bg px-2 py-1 text-xs text-slate-200 outline-none focus:border-mindflow-accent"
                >
                  <option value="">选择工具...</option>
                  <option value="map">地图导航</option>
                  <option value="douyin">抖音发布</option>
                  <option value="shopify">Shopify 优化</option>
                  <option value="shortdramas">短剧预审</option>
                  <option value="feishu">飞书通知</option>
                  <option value="wechat">微信消息</option>
                </select>
              </label>
            )}
          </div>
        ) : (
          <div className="mt-2 text-xs text-slate-500">选择节点以编辑属性</div>
        )}
      </div>
    </aside>
  )
}
