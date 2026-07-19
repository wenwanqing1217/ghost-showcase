import { memo } from 'react'
import { Handle, Position, NodeProps } from 'reactflow'

function StartNode({ selected }: NodeProps) {
  return (
    <div
      className="flex items-center gap-2 rounded-full border border-mindflow-success bg-mindflow-surface px-4 py-2 shadow-lg"
      style={{
        boxShadow: selected ? '0 0 0 2px rgba(34,197,94,0.35)' : undefined,
      }}
    >
      <span className="h-2 w-2 rounded-full bg-mindflow-success" />
      <span className="text-sm font-semibold text-slate-100">开始</span>
      <Handle type="source" position={Position.Bottom} className="!bg-mindflow-success" />
    </div>
  )
}

export default memo(StartNode)
