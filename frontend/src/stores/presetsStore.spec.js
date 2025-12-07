/**
 * presetsStore.js 的单元测试
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { usePresetsStore } from './presetsStore';
import { useSettingsStore } from './settingsStore';

describe('Presets Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('应该初始化预设配置', () => {
    const presetsStore = usePresetsStore();

    expect(presetsStore.state.availablePresets).toEqual([]);
    expect(presetsStore.state.customRules).toEqual({
      block_status_codes: [],
      block_keywords: [],
      retry_status_codes: [],
    });
  });

  it('isCustomPreset 计算属性应该能正确工作', () => {
    const presetsStore = usePresetsStore();
    const settingsStore = useSettingsStore();

    expect(presetsStore.isCustomPreset).toBe(false);

    settingsStore.setPreset('custom');
    expect(presetsStore.isCustomPreset).toBe(true);
  });
});
