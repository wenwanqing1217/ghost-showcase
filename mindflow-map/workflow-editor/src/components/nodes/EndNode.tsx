import { memo } from 'react'
import { Handle, Position, NodeProps } from 'reactflow'

function EndNode({ selected }: NodeProps) {
  return (
    <div
      className="flex items-center gap-2 rounded-full border border-mindflow-danger bg-mindflow-surface px-4 py-2 shadow-lg"
      style={{
        boxShadow: selected ? '0 0 0 2px rgba(239,68,68,0.35)' : undefined,
      }}
    >
      <Handle type="target" position={Position.Top} className="!bg-mindflow-danger" />
      <span className="text-sm font-semibold text-slate-100">结束</span>
    </div>
  )
}

export default memo(EndNode)
