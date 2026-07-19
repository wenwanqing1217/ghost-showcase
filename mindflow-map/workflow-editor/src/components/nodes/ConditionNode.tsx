import { memo } from 'react'
import { Handle, Position, NodeProps } from 'reactflow'

function ConditionNode({ data, selected }: NodeProps) {
  return (
    <div
      className="w-56 rounded-lg border bg-mindflow-surface p-3 shadow-lg"
      style={{
        borderColor: selected ? '#22c55e' : '#334155',
        boxShadow: selected ? '0 0 0 2px rgba(34,197,94,0.35)' : undefined,
      }}
    >
      <div className="text-sm font-semibold text-slate-100">条件分支</div>
      {data.description && (
        <div className="mt-1 text-xs text-slate-400">{String(data.description)}</div>
      )}
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-mindflow-warning"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="true"
        className="!bg-mindflow-success"
        style={{ left: '30%' }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="false"
        className="!bg-mindflow-danger"
        style={{ left: '70%' }}
      />
      <div className="mt-1 flex justify-between text-[10px] text-slate-500">
        <span>True</span>
        <span>False</span>
      </div>
    </div>
  )
}

export default memo(ConditionNode)
