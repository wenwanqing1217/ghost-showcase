/**
 * 双链同步管理器
 *
 * 双向同步逻辑：
 * - Obsidian → Ghost：读取本地 markdown，上传到对应链
 * - Ghost → Obsidian：下载远程记忆，写入本地 markdown
 * - 冲突检测：比较修改时间戳
 */

import { Vault, TFile } from 'obsidian';
import { GhostAPI, MemoryRecord, SaveMemoryRequest } from './api';
import { GhostSyncSettings } from './settings';

interface SyncResult {
  pushed: number;
  pulled: number;
  conflicts: number;
  errors: string[];
}

// Ghost 记忆的 frontmatter 标记
const GHOST_MARKER = 'ghost-memory-id';

export class SyncManager {
  private vault: Vault;
  private api: GhostAPI;
  private settings: GhostSyncSettings;

  constructor(vault: Vault, settings: GhostSyncSettings) {
    this.vault = vault;
    this.api = new GhostAPI(settings.apiUrl);
    this.settings = settings;
  }

  /**
   * 执行完整双向同步
   */
  async sync(): Promise<SyncResult> {
    const result: SyncResult = { pushed: 0, pulled: 0, conflicts: 0, errors: [] };

    // 1. 上传本地新笔记
    const pushResult = await this.push();
    result.pushed = pushResult.pushed;
    result.errors.push(...pushResult.errors);

    // 2. 下载远程新记忆
    const pullResult = await this.pull();
    result.pulled = pullResult.pulled;
    result.conflicts = pullResult.conflicts;
    result.errors.push(...pullResult.errors);

    return result;
  }

  /**
   * 上传：Obsidian → Ghost
   */
  async push(): Promise<{ pushed: number; errors: string[] }> {
    const result = { pushed: 0, errors: [] as string[] };
    const folder = this.settings.syncFolder;

    // 获取同步文件夹下所有 markdown
    const files = this.vault.getMarkdownFiles().filter(f =>
      f.path === folder || f.path.startsWith(folder + '/')
    );

    for (const file of files) {
      try {
        const content = await this.vault.read(file);
        const { frontmatter, body } = this.parseFrontmatter(content);

        // 已同步过的跳过（有 ghost-memory-id）
        if (frontmatter[GHOST_MARKER]) {
          continue;
        }

        // 从 frontmatter 提取元数据
        const sensitivity = this.parseSensitivity(frontmatter);
        const category = frontmatter.category || this.inferCategory(file);
        const tags = this.parseTags(frontmatter);
        const title = file.basename;

        const req: SaveMemoryRequest = {
          content: `# ${title}\n\n${body}`,
          category,
          sensitivity,
          source: 'obsidian',
          tags,
        };

        const res = await this.api.saveMemory(req);
        if (res.success) {
          // 回写 memory_id 到 frontmatter
          const updated = this.setFrontmatterValue(content, GHOST_MARKER, res.memory_id);
          await this.vault.modify(file, updated);
          result.pushed++;
        }
      } catch (err) {
        result.errors.push(`${file.path}: ${err.message}`);
      }
    }

    return result;
  }

  /**
   * 下载：Ghost → Obsidian
   */
  async pull(): Promise<{ pulled: number; conflicts: number; errors: string[] }> {
    const result = { pulled: 0, conflicts: 0, errors: [] as string[] };
    const folder = this.settings.syncFolder;

    // 确保同步文件夹存在
    await this.ensureFolder(folder);

    // 获取所有知识链记忆（私有链不解密下载）
    const memories = await this.api.getAllKnowledge();

    // 建立本地已有 memory_id 的索引
    const localIds = await this.getLocalGhostIds();

    for (const mem of memories) {
      try {
        if (localIds.has(mem.memory_id)) {
          // 已有，检查是否需要更新
          const local = localIds.get(mem.memory_id)!;
          if (mem.timestamp > local.timestamp) {
            // 远程更新，写回本地
            await this.writeMemoryToFile(folder, mem);
            result.pulled++;
          } else if (mem.timestamp < local.timestamp) {
            // 本地更新，冲突
            result.conflicts++;
          }
          continue;
        }

        // 新记忆，写入本地
        await this.writeMemoryToFile(folder, mem);
        result.pulled++;
      } catch (err) {
        result.errors.push(`${mem.memory_id}: ${err.message}`);
      }
    }

    return result;
  }

  // ── 内部方法 ──

  /**
   * 将 Ghost 记忆写入本地 markdown 文件
   */
  private async writeMemoryToFile(folder: string, mem: MemoryRecord): Promise<void> {
    const title = this.sanitizeFilename(mem.content.split('\n')[0].replace(/^#\s*/, '') || mem.memory_id);
    const filePath = `${folder}/${title}.md`;

    const fm: Record<string, string | number | string[]> = {
      [GHOST_MARKER]: mem.memory_id,
      category: mem.category,
      sensitivity: mem.sensitivity,
      chain: mem._chain,
      source: mem.source,
      tags: mem.tags,
      timestamp: mem.timestamp,
      'synced_at': Math.floor(Date.now() / 1000),
    };

    const frontmatterYaml = this.buildFrontmatter(fm);
    const content = `${frontmatterYaml}\n${mem.content.replace(/^#.*\n/, '')}`;

    // 文件已存在则修改，否则创建
    const existing = this.vault.getAbstractFileByPath(filePath);
    if (existing) {
      await this.vault.modify(existing as TFile, content);
    } else {
      await this.vault.create(filePath, content);
    }
  }

  /**
   * 解析 Obsidian 文件的 YAML frontmatter
   */
  private parseFrontmatter(content: string): { frontmatter: Record<string, any>; body: string } {
    const match = content.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/);
    if (!match) return { frontmatter: {}, body: content };

    const frontmatter: Record<string, any> = {};
    for (const line of match[1].split('\n')) {
      const kv = line.match(/^(\w[\w-]*):\s*(.+)$/);
      if (kv) {
        const key = kv[1];
        let val: any = kv[2].trim();
        // 解析数组 [a, b, c]
        if (val.startsWith('[') && val.endsWith(']')) {
          val = val.slice(1, -1).split(',').map((s: string) => s.trim());
        }
        // 解析数字
        else if (/^\d+$/.test(val)) {
          val = parseInt(val, 10);
        }
        frontmatter[key] = val;
      }
    }
    return { frontmatter, body: match[2] };
  }

  /**
   * 构建 YAML frontmatter 字符串
   */
  private buildFrontmatter(data: Record<string, any>): string {
    const lines = Object.entries(data).map(([k, v]) => {
      if (Array.isArray(v)) {
        return `${k}: [${v.join(', ')}]`;
      }
      return `${k}: ${v}`;
    });
    return `---\n${lines.join('\n')}\n---`;
  }

  /**
   * 设置 frontmatter 字段
   */
  private setFrontmatterValue(content: string, key: string, value: string): string {
    if (content.startsWith('---\n')) {
      // 已有 frontmatter，追加字段
      const endIdx = content.indexOf('\n---', 4);
      if (endIdx > 0) {
        const before = content.slice(0, endIdx);
        const after = content.slice(endIdx);
        // 检查是否已有此 key
        if (before.includes(`${key}:`)) {
          return before.replace(new RegExp(`${key}:.*`), `${key}: ${value}`) + after;
        }
        return before + `\n${key}: ${value}` + after;
      }
    }
    // 无 frontmatter，新建
    return `---\n${key}: ${value}\n---\n${content}`;
  }

  /**
   * 从 frontmatter 提取敏感度
   */
  private parseSensitivity(fm: Record<string, any>): number {
    if (fm.sensitivity !== undefined) {
      const s = parseInt(fm.sensitivity, 10);
      if (!isNaN(s)) return Math.max(0, Math.min(100, s));
    }
    return this.settings.defaultSensitivity;
  }

  /**
   * 从 frontmatter 提取标签
   */
  private parseTags(fm: Record<string, any>): string[] {
    if (!fm.tags) return [];
    if (Array.isArray(fm.tags)) return fm.tags;
    if (typeof fm.tags === 'string') {
      return fm.tags.split(',').map((t: string) => t.trim()).filter(Boolean);
    }
    return [];
  }

  /**
   * 根据文件路径推断分类
   */
  private inferCategory(file: TFile): string {
    const folder = file.parent?.path || '';
    if (folder.includes('知识') || folder.includes('knowledge')) return 'knowledge';
    if (folder.includes('日记') || folder.includes('diary')) return 'experience';
    if (folder.includes('项目') || folder.includes('project')) return 'general';
    return 'general';
  }

  /**
   * 获取所有本地已同步的 Ghost 记忆 ID
   */
  private async getLocalGhostIds(): Promise<Map<string, { timestamp: number; file: TFile }>> {
    const result = new Map<string, { timestamp: number; file: TFile }>();
    const folder = this.settings.syncFolder;

    const files = this.vault.getMarkdownFiles().filter(f =>
      f.path === folder || f.path.startsWith(folder + '/')
    );

    for (const file of files) {
      const content = await this.vault.read(file);
      const { frontmatter } = this.parseFrontmatter(content);
      if (frontmatter[GHOST_MARKER]) {
        result.set(frontmatter[GHOST_MARKER], {
          timestamp: frontmatter.timestamp || 0,
          file,
        });
      }
    }

    return result;
  }

  /**
   * 确保文件夹存在
   */
  private async ensureFolder(path: string): Promise<void> {
    const parts = path.split('/');
    let current = '';
    for (const part of parts) {
      current = current ? `${current}/${part}` : part;
      const exists = this.vault.getAbstractFileByPath(current);
      if (!exists) {
        await this.vault.createFolder(current);
      }
    }
  }

  /**
   * 清理文件名中的非法字符
   */
  private sanitizeFilename(name: string): string {
    return name
      .replace(/[\\/:*?"<>|]/g, '_')
      .replace(/\s+/g, '-')
      .slice(0, 60) || `memory-${Date.now()}`;
  }
}
