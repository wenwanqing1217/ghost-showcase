import { memo } from 'react'
import { NodeProps } from 'reactflow'
import type { WorkflowNodeData } from '../../utils/workflowSchema'

function ToolNode({ data, selected }: NodeProps<WorkflowNodeData>) {
  const toolColors: Record<string, string> = {
    map: '#38bdf8',
    douyin: '#f472b6',
    shopify: '#a78bfa',
    shortdramas: '#f59e0b',
    feishu: '#22c55e',
    wechat: '#06b6d4',
  }

  const color = data.tool ? toolColors[data.tool] : '#64748b'

  return (
    <div
      className="min-w-[180px] rounded-lg border bg-mindflow-surface shadow-lg"
      style={{
        borderColor: selected ? '#22c55e' : '#334155',
        boxShadow: selected ? '0 0 0 2px rgba(34,197,94,0.35)' : undefined,
      }}
    >
      <div
        className="flex items-center gap-2 rounded-t-lg px-3 py-2"
        style={{ background: `${color}22` }}
      >
        <span className="h-2 w-2 rounded-full" style={{ background: color }} />
        <div className="text-sm font-semibold text-slate-100">{data.label}</div>
      </div>

      {data.description && (
        <div className="px-3 py-2 text-xs text-slate-400">{data.description}</div>
      )}

      {data.config && Object.keys(data.config).length > 0 && (
        <div className="border-t border-mindflow-border px-3 py-2">
          <div className="text-[10px] uppercase tracking-wide text-slate-500">配置</div>
          <pre className="mt-1 max-h-24 overflow-auto text-[11px] leading-tight text-slate-300">
            {JSON.stringify(data.config, null, 2)}
          </pre>
        </div>
      )}

      <div className="react-flow__handle react-flow__handle-top !bg-mindflow-accent" />
      <div className="react-flow__handle react-flow__handle-bottom !bg-mindflow-accent" />
    </div>
  )
}

export default memo(ToolNode)
