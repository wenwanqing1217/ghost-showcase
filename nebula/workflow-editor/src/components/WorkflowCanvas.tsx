import { useCallback, useRef, useState } from 'react'
import ReactFlow, {
  addEdge,
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  Node,
  Edge,
  Connection,
  useNodesState,
  useEdgesState,
  Panel,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { Toolbar } from './Toolbar'
import { PropertiesPanel } from './PropertiesPanel'
import { nodeTypes } from './nodeTypes'
import {
  nodesToReactFlow,
  edgesToReactFlow,
  reactFlowToWorkflow,
  workflowToYaml,
  yamlToWorkflow,
  TOOL_OPTIONS,
} from '../utils/workflowSchema'

type WorkflowMeta = {
  id: string
  name: string
  version: string
  description?: string
  triggers: string[]
}

const DEFAULT_META: WorkflowMeta = {
  id: 'demo-workflow',
  name: '未命名工作流',
  version: '1.0.0',
  description: '',
  triggers: ['manual'],
}

const INITIAL_NODES: Node[] = nodesToReactFlow([
  { id: 'start-1', type: 'start', label: '开始' },
  { id: 'tool-1', type: 'tool', label: '地图导航', tool: 'map', description: '搜索附近咖啡厅' },
  { id: 'end-1', type: 'end', label: '结束' },
])

const INITIAL_EDGES: Edge[] = edgesToReactFlow([
  { id: 'e1', source: 'start-1', target: 'tool-1' },
  { id: 'e2', source: 'tool-1', target: 'end-1' },
])

export function WorkflowCanvas() {
  const [nodes, setNodes, onNodesChange] = useNodesState(INITIAL_NODES)
  const [edges, setEdges, onEdgesChange] = useEdgesState(INITIAL_EDGES)
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)
  const [workflowMeta, setWorkflowMeta] = useState<WorkflowMeta>(DEFAULT_META)
  const [yamlOutput, setYamlOutput] = useState('')
  const reactFlowWrapper = useRef<HTMLDivElement>(null)

  const onConnect = useCallback(
    (connection: Connection) =>
      setEdges((eds) => addEdge({ ...connection, type: 'smoothstep' }, eds)),
    [setEdges],
  )

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNode(node)
  }, [])

  const onPaneClick = useCallback(() => {
    setSelectedNode(null)
  }, [])

  const addNode = useCallback(
    (type: 'tool' | 'condition') => {
      const id = `${type}-${Date.now()}`
      const newNode: Node = {
        id,
        type,
        position: { x: Math.random() * 400 + 100, y: Math.random() * 400 + 100 },
        data: {
          label: type === 'tool' ? '新工具节点' : '条件分支',
        },
      }
      setNodes((nds) => [...nds, newNode])
    },
    [setNodes],
  )

  const exportYaml = useCallback(() => {
    const workflow = reactFlowToWorkflow(
      nodes as Array<{ id: string; type: string; position: { x: number; y: number }; data: Record<string, unknown> }>,
      edges as Array<{ id: string; source: string; target: string; label?: string }>,
      workflowMeta,
    )
    const yaml = workflowToYaml(workflow)
    setYamlOutput(yaml)
  }, [nodes, edges, workflowMeta])

  const importYaml = useCallback(() => {
    try {
      const workflow = yamlToWorkflow(yamlOutput)
      setWorkflowMeta({
        id: workflow.id,
        name: workflow.name,
        version: workflow.version,
        description: workflow.description || '',
        triggers: workflow.triggers,
      })
      setNodes(nodesToReactFlow(workflow.nodes))
      setEdges(edgesToReactFlow(workflow.edges))
    } catch (e) {
      alert(`导入失败: ${(e as Error).message}`)
    }
  }, [yamlOutput, setNodes, setEdges])

  const downloadYaml = useCallback(() => {
    const workflow = reactFlowToWorkflow(
      nodes as Array<{ id: string; type: string; position: { x: number; y: number }; data: Record<string, unknown> }>,
      edges as Array<{ id: string; source: string; target: string; label?: string }>,
      workflowMeta,
    )
    const yaml = workflowToYaml(workflow)
    const blob = new Blob([yaml], { type: 'text/yaml' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${workflowMeta.name || 'workflow'}.yaml`
    a.click()
    URL.revokeObjectURL(url)
  }, [nodes, edges, workflowMeta])

  const updateSelectedNode = useCallback(
    (updates: Record<string, unknown>) => {
      if (!selectedNode) return
      setNodes((nds) =>
        nds.map((node) =>
          node.id === selectedNode.id
            ? { ...node, data: { ...node.data, ...updates } }
            : node,
        ),
      )
      setSelectedNode((node) =>
        node ? { ...node, data: { ...node.data, ...updates } } : node,
      )
    },
    [selectedNode, setNodes],
  )

  return (
    <div className="flex h-screen w-full flex-col">
      <header className="flex items-center justify-between border-b border-mindflow-border bg-mindflow-surface px-4 py-2">
        <div className="flex items-center gap-3">
          <div className="text-lg font-bold text-slate-100">MindFlow</div>
          <div className="text-xs text-slate-400">Workflow Editor</div>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span>节点: {nodes.length}</span>
          <span>·</span>
          <span>连线: {edges.length}</span>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <Toolbar
          onAddTool={() => addNode('tool')}
          onAddCondition={() => addNode('condition')}
          onExport={exportYaml}
          onImport={importYaml}
          onDownload={downloadYaml}
          yamlOutput={yamlOutput}
          onYamlChange={setYamlOutput}
        />

        <div className="flex-1" ref={reactFlowWrapper}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            nodeTypes={nodeTypes}
            fitView
            snapToGrid
            snapGrid={[16, 16]}
          >
            <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="#334155" />
            <Controls />
            <MiniMap
              nodeColor={(node) => {
                if (node.type === 'start') return '#22c55e'
                if (node.type === 'end') return '#ef4444'
                if (node.type === 'condition') return '#f59e0b'
                return '#38bdf8'
              }}
              maskColor="rgba(15,23,42,0.8)"
            />
            <Panel position="top-right" className="rounded-lg border border-mindflow-border bg-mindflow-surface p-3">
              <div className="text-xs text-slate-400">快速开始</div>
              <div className="mt-2 flex flex-col gap-2">
                {TOOL_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => {
                      const id = `tool-${Date.now()}`
                      const newNode: Node = {
                        id,
                        type: 'tool',
                        position: { x: Math.random() * 400 + 100, y: Math.random() * 400 + 100 },
                        data: {
                          label: option.label,
                          tool: option.value,
                          description: '',
                        },
                      }
                      setNodes((nds) => [...nds, newNode])
                    }}
                    className="flex items-center gap-2 rounded-md border border-mindflow-border bg-mindflow-bg px-3 py-1.5 text-left text-xs text-slate-200 transition-colors hover:border-mindflow-accent hover:text-white"
                  >
                    <span>{option.icon}</span>
                    <span>{option.label}</span>
                  </button>
                ))}
              </div>
            </Panel>
          </ReactFlow>
        </div>

        <PropertiesPanel
          selectedNode={selectedNode}
          onUpdateNode={updateSelectedNode}
          workflowMeta={workflowMeta}
          onUpdateMeta={setWorkflowMeta}
        />
      </div>
    </div>
  )
}
