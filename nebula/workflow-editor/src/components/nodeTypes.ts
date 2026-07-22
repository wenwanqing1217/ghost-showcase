import { memo } from 'react'
import { NodeTypes as FlowNodeTypes } from 'reactflow'
import ToolNode from './nodes/ToolNode'
import ConditionNode from './nodes/ConditionNode'
import StartNode from './nodes/StartNode'
import EndNode from './nodes/EndNode'

export const nodeTypes: FlowNodeTypes = {
  tool: memo(ToolNode),
  condition: memo(ConditionNode),
  start: memo(StartNode),
  end: memo(EndNode),
}
