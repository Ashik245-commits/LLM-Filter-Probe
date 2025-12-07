/**
 * 配置加载工具函数
 * 提供通用的配置加载和保存功能，支持缓存机制
 */

import { apiGet, apiPost } from './apiClient';
import { CACHE_CONFIG } from '../constants/config';

/**
 * 配置缓存管理
 */
const configCache = {
  data: {},
  timestamps: {},

  /**
   * 获取缓存的配置
   * @param {string} endpoint - API 端点
   * @returns {any|null} 缓存的配置或 null
   */
  get(endpoint) {
    const cached = this.data[endpoint];
    const timestamp = this.timestamps[endpoint];

    if (!cached || !timestamp) return null;

    // 检查缓存是否过期
    if (Date.now() - timestamp > CACHE_CONFIG.CONFIG_TTL) {
      delete this.data[endpoint];
      delete this.timestamps[endpoint];
      return null;
    }

    return cached;
  },

  /**
   * 设置缓存的配置
   * @param {string} endpoint - API 端点
   * @param {any} data - 配置数据
   */
  set(endpoint, data) {
    this.data[endpoint] = data;
    this.timestamps[endpoint] = Date.now();
  },

  /**
   * 清除特定端点的缓存
   * @param {string} endpoint - API 端点
   */
  clear(endpoint) {
    delete this.data[endpoint];
    delete this.timestamps[endpoint];
  },

  /**
   * 清除所有缓存
   */
  clearAll() {
    this.data = {};
    this.timestamps = {};
  },
};

/**
 * 通用配置加载函数
 * @param {string} endpoint - API 端点
 * @param {*} defaultValue - 加载失败时的默认值
 * @param {boolean} forceRefresh - 是否强制刷新缓存
 * @returns {Promise<*>} 加载的配置数据
 */
export async function loadConfig(endpoint, defaultValue = {}, forceRefresh = false) {
  try {
    // 检查缓存
    if (!forceRefresh) {
      const cached = configCache.get(endpoint);
      if (cached) {
        console.log(`📦 使用缓存的配置: ${endpoint}`);
        return cached;
      }
    }

    // 从服务器加载
    const response = await apiGet(endpoint);

    // 处理响应格式（兼容新旧格式）
    const data = response || defaultValue;

    // 只缓存非空配置，避免缓存未初始化的配置
    // 对于 API 配置，检查是否有有效的 api_url 和 api_key
    const shouldCache =
      endpoint === '/api/api_config' ? data.api_url && data.api_key : Object.keys(data).length > 0;

    if (shouldCache) {
      configCache.set(endpoint, data);
    } else {
      console.warn(`⚠️ 配置为空，不缓存: ${endpoint}`);
    }

    return data;
  } catch (err) {
    console.error(`❌ 加载配置失败 (${endpoint}):`, err);
    return defaultValue;
  }
}

/**
 * 通用配置保存函数
 * @param {string} endpoint - API 端点
 * @param {*} payload - 要保存的数据
 * @returns {Promise<*>} 保存结果
 */
export async function saveConfig(endpoint, payload) {
  try {
    const response = await apiPost(endpoint, payload);

    // 保存后清除缓存，下次加载时会重新获取
    configCache.clear(endpoint);

    return response;
  } catch (err) {
    console.error(`❌ 保存配置失败 (${endpoint}):`, err);
    throw err;
  }
}

/**
 * 清除配置缓存
 * @param {string} endpoint - 可选，指定要清除的端点；不指定则清除所有
 */
export function clearConfigCache(endpoint) {
  if (endpoint) {
    configCache.clear(endpoint);
    console.log(`✅ 已清除缓存: ${endpoint}`);
  } else {
    configCache.clearAll();
    console.log('✅ 已清除所有缓存');
  }
}

/**
 * 获取缓存统计信息
 * @returns {object} 缓存统计
 */
export function getCacheStats() {
  return {
    cacheSize: Object.keys(configCache.data).length,
    cachedEndpoints: Object.keys(configCache.data),
    ttl: CACHE_CONFIG.CONFIG_TTL,
  };
}
