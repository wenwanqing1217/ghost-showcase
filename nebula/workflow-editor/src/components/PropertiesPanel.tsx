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

type MapAction = 'search' | 'route' | 'weather'

type MapNavigationConfig = {
  action: MapAction
  city: string
  origin: string
  destination: string
  mode: string
  originLatitude: string
  originLongitude: string
  destinationLatitude: string
  destinationLongitude: string
  departureTime: string
  description: string
}

const EMPTY_MAP_CONFIG: MapNavigationConfig = {
  action: 'search',
  city: '',
  origin: '',
  destination: '',
  mode: 'driving',
  originLatitude: '',
  originLongitude: '',
  destinationLatitude: '',
  destinationLongitude: '',
  departureTime: '',
  description: '',
}

function readMapConfig(node: Record<string, unknown>): MapNavigationConfig {
  const data = node.data as Record<string, unknown> | undefined
  const config = (data?.config as Partial<MapNavigationConfig> | undefined) || {}
  return { ...EMPTY_MAP_CONFIG, ...config }
}

export function PropertiesPanel({ selectedNode, onUpdateNode, workflowMeta, onUpdateMeta }: PropertiesPanelProps) {
  const mapConfig = selectedNode ? (getNodeTool(selectedNode) === 'map' ? readMapConfig(selectedNode) : null) : null

  const updateMapConfig = (updates: Partial<MapNavigationConfig>) => {
    if (!selectedNode) return
    const current = readMapConfig(selectedNode)
    const next = { ...current, ...updates }
    onUpdateNode({ ...selectedNode, data: { ...(selectedNode.data || {}), config: next } })
  }

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
            <label className="flex flex-col gap-1">
              <span className="text-[11px] text-slate-400">工具</span>
              <select
                value={getNodeTool(selectedNode)}
                onChange={(e) => {
                  const tool = e.target.value
                  onUpdateNode({ tool, config: tool === 'map' ? { ...EMPTY_MAP_CONFIG } : {} })
                }}
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

            {mapConfig && (
              <div className="flex flex-col gap-2 rounded-md border border-mindflow-border bg-mindflow-bg p-2">
                <div className="text-[11px] font-semibold text-slate-200">地图配置</div>
                <label className="flex flex-col gap-1">
                  <span className="text-[10px] text-slate-400">动作</span>
                  <select
                    value={mapConfig.action}
                    onChange={(e) => updateMapConfig({ action: e.target.value as MapAction })}
                    className="rounded-md border border-mindflow-border bg-mindflow-surface px-2 py-1 text-xs text-slate-200 outline-none focus:border-mindflow-accent"
                  >
                    <option value="search">地点搜索</option>
                    <option value="route">路线规划</option>
                    <option value="weather">天气查询</option>
                  </select>
                </label>

                <label className="flex flex-col gap-1">
                  <span className="text-[10px] text-slate-400">描述</span>
                  <input
                    value={mapConfig.description}
                    onChange={(e) => updateMapConfig({ description: e.target.value })}
                    placeholder="用于工作流展示与节点备注"
                    className="rounded-md border border-mindflow-border bg-mindflow-surface px-2 py-1 text-xs text-slate-200 outline-none focus:border-mindflow-accent"
                  />
                </label>

                {(mapConfig.action === 'search' || mapConfig.action === 'weather') && (
                  <label className="flex flex-col gap-1">
                    <span className="text-[10px] text-slate-400">地区</span>
                    <input
                      value={mapConfig.city}
                      onChange={(e) => updateMapConfig({ city: e.target.value })}
                      placeholder={mapConfig.action === 'weather' ? '例如：北京' : '例如：北京'}
                      className="rounded-md border border-mindflow-border bg-mindflow-surface px-2 py-1 text-xs text-slate-200 outline-none focus:border-mindflow-accent"
                    />
                  </label>
                )}

                {mapConfig.action === 'route' && (
                  <>
                    <label className="flex flex-col gap-1">
                      <span className="text-[10px] text-slate-400">起点</span>
                      <input
                        value={mapConfig.origin}
                        onChange={(e) => updateMapConfig({ origin: e.target.value })}
                        placeholder="例如：天安门"
                        className="rounded-md border border-mindflow-border bg-mindflow-surface px-2 py-1 text-xs text-slate-200 outline-none focus:border-mindflow-accent"
                      />
                    </label>
                    <label className="flex flex-col gap-1">
                      <span className="text-[10px] text-slate-400">终点</span>
                      <input
                        value={mapConfig.destination}
                        onChange={(e) => updateMapConfig({ destination: e.target.value })}
                        placeholder="例如：故宫"
                        className="rounded-md border border-mindflow-border bg-mindflow-surface px-2 py-1 text-xs text-slate-200 outline-none focus:border-mindflow-accent"
                      />
                    </label>
                    <label className="flex flex-col gap-1">
                      <span className="text-[10px] text-slate-400">出行方式</span>
                      <select
                        value={mapConfig.mode}
                        onChange={(e) => updateMapConfig({ mode: e.target.value })}
                        className="rounded-md border border-mindflow-border bg-mindflow-surface px-2 py-1 text-xs text-slate-200 outline-none focus:border-mindflow-accent"
                      >
                        <option value="driving">驾车</option>
                        <option value="walking">步行</option>
                        <option value="transit">公交</option>
                        <option value="riding">骑行</option>
                      </select>
                    </label>
                    <label className="flex flex-col gap-1">
                      <span className="text-[10px] text-slate-400">出发时间</span>
                      <input
                        value={mapConfig.departureTime}
                        onChange={(e) => updateMapConfig({ departureTime: e.target.value })}
                        placeholder="ISO 8601，选填"
                        className="rounded-md border border-mindflow-border bg-mindflow-surface px-2 py-1 text-xs text-slate-200 outline-none focus:border-mindflow-accent"
                      />
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      <label className="flex flex-col gap-1">
                        <span className="text-[10px] text-slate-400">起点纬度</span>
                        <input
                          value={mapConfig.originLatitude}
                          onChange={(e) => updateMapConfig({ originLatitude: e.target.value })}
                          placeholder="选填"
                          className="rounded-md border border-mindflow-border bg-mindflow-surface px-2 py-1 text-xs text-slate-200 outline-none focus:border-mindflow-accent"
                        />
                      </label>
                      <label className="flex flex-col gap-1">
                        <span className="text-[10px] text-slate-400">起点经度</span>
                        <input
                          value={mapConfig.originLongitude}
                          onChange={(e) => updateMapConfig({ originLongitude: e.target.value })}
                          placeholder="选填"
                          className="rounded-md border border-mindflow-border bg-mindflow-surface px-2 py-1 text-xs text-slate-200 outline-none focus:border-mindflow-accent"
                        />
                      </label>
                      <label className="flex flex-col gap-1">
                        <span className="text-[10px] text-slate-400">终点纬度</span>
                        <input
                          value={mapConfig.destinationLatitude}
                          onChange={(e) => updateMapConfig({ destinationLatitude: e.target.value })}
                          placeholder="选填"
                          className="rounded-md border border-mindflow-border bg-mindflow-surface px-2 py-1 text-xs text-slate-200 outline-none focus:border-mindflow-accent"
                        />
                      </label>
                      <label className="flex flex-col gap-1">
                        <span className="text-[10px] text-slate-400">终点经度</span>
                        <input
                          value={mapConfig.destinationLongitude}
                          onChange={(e) => updateMapConfig({ destinationLongitude: e.target.value })}
                          placeholder="选填"
                          className="rounded-md border border-mindflow-border bg-mindflow-surface px-2 py-1 text-xs text-slate-200 outline-none focus:border-mindflow-accent"
                        />
                      </label>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="mt-2 text-xs text-slate-500">选择节点以编辑属性</div>
        )}
      </div>
    </aside>
  )
}
