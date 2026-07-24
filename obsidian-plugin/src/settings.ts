import { App, PluginSettingTab, Setting } from 'obsidian';
import GhostSyncPlugin from '../main';

export interface GhostSyncSettings {
  apiUrl: string;                // Ghost API 地址
  defaultSensitivity: number;    // 默认敏感度 (0-100)
  syncFolder: string;            // 同步文件夹
  autoSync: boolean;             // 是否自动同步
  syncIntervalMinutes: number;   // 同步间隔（分钟）
  conflictResolution: 'local' | 'remote' | 'newest';  // 冲突解决策略
}

export const DEFAULT_SETTINGS: GhostSyncSettings = {
  apiUrl: 'http://localhost:8000',
  defaultSensitivity: 30,
  syncFolder: 'ghost-memory',
  autoSync: false,
  syncIntervalMinutes: 30,
  conflictResolution: 'newest',
};

export class GhostSyncSettingTab extends PluginSettingTab {
  plugin: GhostSyncPlugin;

  constructor(app: App, plugin: GhostSyncPlugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display(): void {
    const { containerEl } = this;
    containerEl.empty();
    containerEl.createEl('h2', { text: 'Ghost 双链记忆同步' });

    // API 地址
    new Setting(containerEl)
      .setName('Ghost API 地址')
      .setDesc('后端 API 服务地址（默认 http://localhost:8000）')
      .addText(text => text
        .setPlaceholder('http://localhost:8000')
        .setValue(this.plugin.settings.apiUrl)
        .onChange(async (value) => {
          this.plugin.settings.apiUrl = value.replace(/\/$/, '');
          await this.plugin.saveSettings();
        }));

    // 默认敏感度
    new Setting(containerEl)
      .setName('默认敏感度')
      .setDesc('0 = 公开（知识链），100 = 绝密（私有链），70+ 自动进入私有链')
      .addSlider(slider => slider
        .setLimits(0, 100, 1)
        .setValue(this.plugin.settings.defaultSensitivity)
        .setDynamicTooltip()
        .onChange(async (value) => {
          this.plugin.settings.defaultSensitivity = value;
          await this.plugin.saveSettings();
        }));

    // 同步文件夹
    new Setting(containerEl)
      .setName('同步文件夹')
      .setDesc('本地 Obsidian 中用于存放 Ghost 记忆的文件夹')
      .addText(text => text
        .setPlaceholder('ghost-memory')
        .setValue(this.plugin.settings.syncFolder)
        .onChange(async (value) => {
          this.plugin.settings.syncFolder = value || 'ghost-memory';
          await this.plugin.saveSettings();
        }));

    // 自动同步
    new Setting(containerEl)
      .setName('自动同步')
      .setDesc('按间隔自动同步笔记和记忆')
      .addToggle(toggle => toggle
        .setValue(this.plugin.settings.autoSync)
        .onChange(async (value) => {
          this.plugin.settings.autoSync = value;
          await this.plugin.saveSettings();
        }));

    // 同步间隔
    new Setting(containerEl)
      .setName('同步间隔（分钟）')
      .setDesc('自动同步的时间间隔')
      .addSlider(slider => slider
        .setLimits(5, 120, 5)
        .setValue(this.plugin.settings.syncIntervalMinutes)
        .setDynamicTooltip()
        .onChange(async (value) => {
          this.plugin.settings.syncIntervalMinutes = value;
          await this.plugin.saveSettings();
        }));

    // 冲突解决
    new Setting(containerEl)
      .setName('冲突解决策略')
      .setDesc('当本地和远程都有修改时')
      .addDropdown(dropdown => dropdown
        .addOption('newest', '以最新为准')
        .addOption('local', '保留本地')
        .addOption('remote', '保留远程')
        .setValue(this.plugin.settings.conflictResolution)
        .onChange(async (value) => {
          this.plugin.settings.conflictResolution = value as 'local' | 'remote' | 'newest';
          await this.plugin.saveSettings();
        }));
  }
}
