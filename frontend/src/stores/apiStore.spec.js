/**
 * apiStore.js 的单元测试
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useApiStore } from './apiStore';

describe('API Store', () => {
  beforeEach(() => {
    // 为每个测试创建一个新的 Pinia 实例
    setActivePinia(createPinia());
  });

  it('应该初始化 API 配置', () => {
    const apiStore = useApiStore();

    expect(apiStore.config).toBeDefined();
    expect(apiStore.config.url).toBe('');
    expect(apiStore.config.key).toBe('');
    expect(apiStore.config.model).toBe('gpt-4o-mini');
    expect(apiStore.config.isValid).toBe(false);
    expect(apiStore.config.testStatus).toBe('untested');
  });

  it('应该更新字段并重置测试状态', () => {
    const apiStore = useApiStore();
    apiStore.config.testStatus = 'passed';
    apiStore.config.isValid = true;

    apiStore.updateField('url', 'https://new-api.com/v1');

    expect(apiStore.config.url).toBe('https://new-api.com/v1');
    expect(apiStore.config.testStatus).toBe('untested');
    expect(apiStore.config.isValid).toBe(false);
  });

  // 注意：loadConfig, saveConfig, 和 testConnection
  // 依赖于 fetch，这需要进行 mock 测试。
  // 在这里，我们只测试状态的更新逻辑。
});
