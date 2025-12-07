/**
 * API 端点常量定义
 * 集中管理所有 API 端点，便于维护和修改
 */

export const API_ENDPOINTS = {
  // 健康检查
  HEALTH: '/api/health',

  // 会话管理
  SESSION: {
    CREATE: '/api/session/create',
    GET: (id) => `/api/session/${id}`,
    DELETE: (id) => `/api/session/${id}`,
  },

  // 扫描操作
  SCAN: {
    CANCEL: (id) => `/api/scan/${id}/cancel`,
  },

  // 配置管理
  CONFIG: {
    API: '/api/api_config',
    SETTINGS: '/api/settings_config',
    PRESETS: '/api/presets_config',
  },

  // 验证
  VERIFY: '/api/verify',
};

/**
 * 获取 WebSocket URL
 * 根据当前页面协议自动选择 ws 或 wss
 * @param {string} sessionId - 会话 ID
 * @returns {string} WebSocket URL
 */
export function getWebSocketUrl(sessionId) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;
  return `${protocol}//${host}/ws/scan/${sessionId}`;
}
