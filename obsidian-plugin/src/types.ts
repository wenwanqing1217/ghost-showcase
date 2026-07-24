/**
 * 共享类型定义
 */

export interface NoteFile {
  path: string;
  title: string;
  content: string;
  frontmatter: Record<string, any>;
  modified: number;
  created: number;
}

export interface SyncStatus {
  lastSync: number | null;
  totalPushed: number;
  totalPulled: number;
  lastError: string | null;
}

export interface DualChainStats {
  private_count: number;
  knowledge_count: number;
  total_count: number;
  private_encrypted_ratio: number;
}
