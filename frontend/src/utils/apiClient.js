/**
 * 通用 API 客户端工具函数
 *
 * 提供统一的 API 调用接口，包括：
 * - 自动添加 Content-Type 头
 * - 统一的错误处理
 * - 自动 JSON 解析
 * - 日志记录
 */

import { HTTP_CONFIG } from '../constants/config';

/**
 * 执行 API 调用
 * @param {string} endpoint - API 端点路径
 * @param {object} options - 请求选项
 * @returns {Promise<any>} 响应数据
 */
export async function apiCall(endpoint, options = {}) {
  const { method = 'GET', body = null, headers = {}, timeout = HTTP_CONFIG.TIMEOUT } = options;

  const requestOptions = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
  };

  if (body) {
    requestOptions.body = typeof body === 'string' ? body : JSON.stringify(body);
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    const response = await fetch(endpoint, {
      ...requestOptions,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    const contentType = response.headers.get('content-type');
    const isJson = contentType && contentType.includes('application/json');

    if (!isJson) {
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || `HTTP Error: ${response.status}`);
      }
      return await response.text();
    }

    const payload = await response.json();

    if (!response.ok) {
      // FastAPI wraps HTTPExceptions in a "detail" field.
      const errorMessage = payload.detail?.message || payload.detail || JSON.stringify(payload);
      throw new Error(errorMessage);
    }

    if (payload.status === 'ok') {
      return payload.data;
    } else {
      throw new Error(payload.message || 'API returned an unspecified error.');
    }
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new Error(`请求超时 (${timeout}ms)`);
    }
    throw err;
  }
}

/**
 * GET 请求
 * @param {string} endpoint - API 端点
 * @param {object} options - 请求选项
 * @returns {Promise<any>} 响应数据
 */
export async function apiGet(endpoint, options = {}) {
  return apiCall(endpoint, { ...options, method: 'GET' });
}

/**
 * POST 请求
 * @param {string} endpoint - API 端点
 * @param {any} body - 请求体
 * @param {object} options - 请求选项
 * @returns {Promise<any>} 响应数据
 */
export async function apiPost(endpoint, body, options = {}) {
  return apiCall(endpoint, { ...options, method: 'POST', body });
}

/**
 * PUT 请求
 * @param {string} endpoint - API 端点
 * @param {any} body - 请求体
 * @param {object} options - 请求选项
 * @returns {Promise<any>} 响应数据
 */
export async function apiPut(endpoint, body, options = {}) {
  return apiCall(endpoint, { ...options, method: 'PUT', body });
}

/**
 * DELETE 请求
 * @param {string} endpoint - API 端点
 * @param {object} options - 请求选项
 * @returns {Promise<any>} 响应数据
 */
export async function apiDelete(endpoint, options = {}) {
  return apiCall(endpoint, { ...options, method: 'DELETE' });
}
