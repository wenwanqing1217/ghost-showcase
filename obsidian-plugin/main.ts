import { Plugin, TFile, Vault, Notice } from 'obsidian';
import { GhostSyncSettings, DEFAULT_SETTINGS } from './src/settings';
import { GhostSyncSettingTab } from './src/settings';
import { SyncManager } from './src/sync';

export default class GhostSyncPlugin extends Plugin {
  settings: GhostSyncSettings;
  syncManager: SyncManager | null = null;
  syncInterval: number | null = null;

  async onload() {
    await this.loadSettings();

    // 设置标签页
    this.addSettingTab(new GhostSyncSettingTab(this.app, this));

    // 手动同步按钮（Ribbon）
    this.addRibbonIcon('refresh-cw', 'Ghost 双链同步', async () => {
      await this.runSync();
    });

    // 命令面板
    this.addCommand({
      id: 'ghost-sync-now',
      name: '立即同步 Ghost 双链记忆',
      callback: () => this.runSync(),
    });

    this.addCommand({
      id: 'ghost-pull-only',
      name: '仅下载（Ghost → Obsidian）',
      callback: () => this.runPull(),
    });

    this.addCommand({
      id: 'ghost-push-only',
      name: '仅上传（Obsidian → Ghost）',
      callback: () => this.runPush(),
    });

    // 自动同步
    if (this.settings.autoSync) {
      this.startAutoSync();
    }
  }

  onunload() {
    if (this.syncInterval) {
      window.clearInterval(this.syncInterval);
      this.syncInterval = null;
    }
  }

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings() {
    await this.saveData(this.settings);
    // 设置变更后重启自动同步
    if (this.settings.autoSync) {
      this.startAutoSync();
    } else {
      this.stopAutoSync();
    }
  }

  startAutoSync() {
    this.stopAutoSync();
    const ms = this.settings.syncIntervalMinutes * 60 * 1000;
    this.syncInterval = window.setInterval(() => this.runSync(), ms);
    new Notice(`Ghost 自动同步已开启（每 ${this.settings.syncIntervalMinutes} 分钟）`);
  }

  stopAutoSync() {
    if (this.syncInterval) {
      window.clearInterval(this.syncInterval);
      this.syncInterval = null;
    }
  }

  async runSync() {
    try {
      new Notice('🔄 Ghost 同步中...');
      this.syncManager = new SyncManager(this.app.vault, this.settings);
      const result = await this.syncManager.sync();
      new Notice(`✅ 同步完成 ↑${result.pushed} ↓${result.pulled} ⚠${result.conflicts}`);
    } catch (err) {
      new Notice(`❌ 同步失败: ${err.message}`);
    }
  }

  async runPull() {
    try {
      this.syncManager = new SyncManager(this.app.vault, this.settings);
      const result = await this.syncManager.pull();
      new Notice(`⬇ 下载完成: ${result.pulled} 条记忆`);
    } catch (err) {
      new Notice(`❌ 下载失败: ${err.message}`);
    }
  }

  async runPush() {
    try {
      this.syncManager = new SyncManager(this.app.vault, this.settings);
      const result = await this.syncManager.push();
      new Notice(`⬆ 上传完成: ${result.pushed} 条笔记`);
    } catch (err) {
      new Notice(`❌ 上传失败: ${err.message}`);
    }
  }
}
