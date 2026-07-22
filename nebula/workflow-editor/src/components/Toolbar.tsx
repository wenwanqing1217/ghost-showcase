import yaml from 'js-yaml'

export function Toolbar({
  onAddTool,
  onAddCondition,
  onExport,
  onImport,
  onDownload,
  yamlOutput,
  onYamlChange,
}: {
  onAddTool: () => void
  onAddCondition: () => void
  onExport: () => void
  onImport: () => void
  onDownload: () => void
  yamlOutput: string
  onYamlChange: (value: string) => void
}) {
  const handleImport = () => {
    try {
      const parsed = yaml.load(yamlOutput) as { nodes?: Array<{ id: string }>; edges?: Array<{ id: string }> }
      if (!parsed || !Array.isArray(parsed.nodes) || !Array.isArray(parsed.edges)) {
        throw new Error('YAML 必须包含 nodes 和 edges 数组')
      }
      onImport()
    } catch (e) {
      alert(`导入失败: ${(e as Error).message}`)
    }
  }

  return (
    <aside className="w-64 border-r border-mindflow-border bg-mindflow-surface p-4">
      <div className="mb-4">
        <div className="text-sm font-semibold text-slate-200">工具箱</div>
        <div className="mt-2 flex flex-col gap-2">
          <button
            onClick={onAddTool}
            className="rounded-md border border-mindflow-border bg-mindflow-bg px-3 py-2 text-left text-xs text-slate-200 transition-colors hover:border-mindflow-accent hover:text-white"
          >
            + 添加工具节点
          </button>
          <button
            onClick={onAddCondition}
            className="rounded-md border border-mindflow-border bg-mindflow-bg px-3 py-2 text-left text-xs text-slate-200 transition-colors hover:border-mindflow-warning hover:text-white"
          >
            + 添加条件分支
          </button>
        </div>
      </div>

      <div className="mb-4">
        <div className="text-sm font-semibold text-slate-200">YAML</div>
        <div className="mt-2 flex flex-col gap-2">
          <button
            onClick={onExport}
            className="rounded-md border border-mindflow-border bg-mindflow-bg px-3 py-2 text-left text-xs text-slate-200 transition-colors hover:border-mindflow-accent hover:text-white"
          >
            导出到 YAML
          </button>
          <button
            onClick={onDownload}
            className="rounded-md border border-mindflow-border bg-mindflow-bg px-3 py-2 text-left text-xs text-slate-200 transition-colors hover:border-mindflow-success hover:text-white"
          >
            下载文件
          </button>
          <button
            onClick={handleImport}
            className="rounded-md border border-mindflow-border bg-mindflow-bg px-3 py-2 text-left text-xs text-slate-200 transition-colors hover:border-mindflow-warning hover:text-white"
          >
            从 YAML 导入
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        <div className="text-sm font-semibold text-slate-200">YAML 预览</div>
        <textarea
          value={yamlOutput}
          onChange={(e) => onYamlChange(e.target.value)}
          placeholder="在此粘贴 YAML 以导入..."
          className="mt-2 h-64 w-full rounded-md border border-mindflow-border bg-mindflow-bg p-2 font-mono text-[11px] leading-tight text-slate-300 outline-none focus:border-mindflow-accent"
        />
      </div>
    </aside>
  )
}

