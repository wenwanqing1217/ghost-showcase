/**
 * Ghost 双链记忆 API 客户端
 *
 * 使用 Obsidian 的 requestUrl（支持 CORS，无需 CORS 插件）
 */

import { requestUrl, RequestUrlResponse } from 'obsidian';

export interface MemoryRecord {
  memory_id: string;
  content: string;
  category: string;
  sensitivity: number;
  source: string;
  tags: string[];
  timestamp: number;
  _chain: 'private' | 'knowledge';
}

export interface SaveMemoryRequest {
  content: string;
  category: string;
  sensitivity: number;
  source: string;
  tags: string[];
}

export interface QueryRequest {
  chain: string;
  keyword?: string;
  category?: string;
  max_sensitivity?: number;
  limit?: number;
}

export class GhostAPI {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  /**
   * 健康检查
   */
  async health(): Promise<boolean> {
    try {
      const res = await requestUrl({ url: `${this.baseUrl}/health`, method: 'GET' });
      return res.status === 200;
    } catch {
      return false;
    }
  }

  /**
   * 保存记忆到 Ghost
   */
  async saveMemory(req: SaveMemoryRequest): Promise<{ success: boolean; memory_id: string; chain: string }> {
    const res = await requestUrl({
      url: `${this.baseUrl}/api/v1/dual-chain/save`,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    return res.json;
  }

  /**
   * 查询记忆
   */
  async queryMemories(req: QueryRequest): Promise<{ results: MemoryRecord[]; count: number }> {
    const res = await requestUrl({
      url: `${this.baseUrl}/api/v1/dual-chain/query`,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    return res.json;
  }

  /**
   * 获取所有知识链记忆
   */
  async getAllKnowledge(): Promise<MemoryRecord[]> {
    const res = await this.queryMemories({
      chain: 'knowledge',
      limit: 100,
    });
    return res.results;
  }

  /**
   * 获取所有私有链记忆（不解密，仅摘要）
   */
  async getAllPrivate(): Promise<MemoryRecord[]> {
    const res = await this.queryMemories({
      chain: 'private',
      limit: 100,
    });
    return res.results;
  }

  /**
   * 迁移记忆到另一条链
   */
  async migrateMemory(memoryId: string, targetChain: 'private' | 'knowledge'): Promise<{ success: boolean }> {
    const res = await requestUrl({
      url: `${this.baseUrl}/api/v1/dual-chain/migrate`,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ memory_id: memoryId, target_chain: targetChain }),
    });
    return res.json;
  }

  /**
   * 删除记忆
   */
  async deleteMemory(memoryId: string): Promise<{ success: boolean }> {
    const res = await requestUrl({
      url: `${this.baseUrl}/api/v1/dual-chain/${memoryId}`,
      method: 'DELETE',
    });
    return res.json;
  }

  /**
   * 获取统计
   */
  async getStats(): Promise<{
    private_count: number;
    knowledge_count: number;
    total_count: number;
    private_encrypted_ratio: number;
  }> {
    const res = await requestUrl({
      url: `${this.baseUrl}/api/v1/dual-chain/stats`,
      method: 'GET',
    });
    return res.json;
  }
}
