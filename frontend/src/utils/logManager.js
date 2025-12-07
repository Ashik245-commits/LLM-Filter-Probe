/**
 * 日志管理工具
 * 提供日志的持久化、导出、时间清理等功能
 */

import { LOG_CONFIG } from '../constants/config';

/**
 * 日志管理器
 */
class LogManager {
  constructor() {
    this.storageKey = 'llm_probe_logs';
    this.maxSize = LOG_CONFIG.MAX_SIZE;
    this.retentionTime = LOG_CONFIG.RETENTION_TIME;
  }

  /**
   * 保存日志到本地存储
   * @param {Array} messages - 日志消息数组
   */
  saveLogs(messages) {
    try {
      const logsToSave = messages.map((msg) => ({
        ...msg,
        timestamp: msg.timestamp || new Date().toISOString(),
      }));

      localStorage.setItem(this.storageKey, JSON.stringify(logsToSave));
    } catch (err) {
      console.error('❌ 保存日志失败:', err);
      // 如果存储空间不足，清除最旧的日志
      if (err.name === 'QuotaExceededError') {
        this.clearOldLogs(messages);
      }
    }
  }

  /**
   * 从本地存储加载日志
   * @returns {Array} 日志消息数组
   */
  loadLogs() {
    try {
      const stored = localStorage.getItem(this.storageKey);
      if (!stored) return [];

      const logs = JSON.parse(stored);

      // 过滤过期的日志
      return this.filterExpiredLogs(logs);
    } catch (err) {
      console.error('❌ 加载日志失败:', err);
      return [];
    }
  }

  /**
   * 过滤过期的日志
   * @param {Array} logs - 日志数组
   * @returns {Array} 过滤后的日志
   */
  filterExpiredLogs(logs) {
    const now = Date.now();
    return logs.filter((log) => {
      const logTime = new Date(log.timestamp).getTime();
      return now - logTime < this.retentionTime;
    });
  }

  /**
   * 清除最旧的日志
   * @param {Array} messages - 当前日志数组
   */
  clearOldLogs(messages) {
    try {
      // 保留最新的 50% 日志
      const keepCount = Math.floor(this.maxSize * 0.5);
      const logsToKeep = messages.slice(-keepCount);

      localStorage.setItem(this.storageKey, JSON.stringify(logsToKeep));
      console.log(`⚠️ 存储空间不足，已清除旧日志，保留最新 ${keepCount} 条`);
    } catch (err) {
      console.error('❌ 清除旧日志失败:', err);
      // 最后的手段：清空所有日志
      localStorage.removeItem(this.storageKey);
    }
  }

  /**
   * 导出日志为 JSON 文件
   * @param {Array} messages - 日志消息数组
   * @param {string} filename - 文件名
   */
  exportLogsAsJson(messages, filename = 'logs.json') {
    try {
      const dataStr = JSON.stringify(messages, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      this.downloadFile(dataBlob, filename);
    } catch (err) {
      console.error('❌ 导出 JSON 日志失败:', err);
      throw err;
    }
  }

  /**
   * 导出日志为 CSV 文件
   * @param {Array} messages - 日志消息数组
   * @param {string} filename - 文件名
   */
  exportLogsAsCsv(messages, filename = 'logs.csv') {
    try {
      const headers = ['Timestamp', 'Level', 'Message'];
      const rows = messages.map((msg) => [
        msg.timestamp || '',
        msg.level || 'info',
        `"${(msg.message || '').replace(/"/g, '""')}"`, // CSV 转义
      ]);

      const csvContent = [headers.join(','), ...rows.map((row) => row.join(','))].join('\n');

      const dataBlob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      this.downloadFile(dataBlob, filename);
    } catch (err) {
      console.error('❌ 导出 CSV 日志失败:', err);
      throw err;
    }
  }

  /**
   * 导出日志为纯文本文件
   * @param {Array} messages - 日志消息数组
   * @param {string} filename - 文件名
   */
  exportLogsAsText(messages, filename = 'logs.txt') {
    try {
      const textContent = messages
        .map((msg) => `[${msg.timestamp || 'N/A'}] [${msg.level || 'info'}] ${msg.message || ''}`)
        .join('\n');

      const dataBlob = new Blob([textContent], { type: 'text/plain;charset=utf-8;' });
      this.downloadFile(dataBlob, filename);
    } catch (err) {
      console.error('❌ 导出文本日志失败:', err);
      throw err;
    }
  }

  /**
   * 下载文件
   * @param {Blob} blob - 文件内容
   * @param {string} filename - 文件名
   */
  downloadFile(blob, filename) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  /**
   * 清除所有日志
   */
  clearAllLogs() {
    try {
      localStorage.removeItem(this.storageKey);
      console.log('✅ 已清除所有日志');
    } catch (err) {
      console.error('❌ 清除日志失败:', err);
    }
  }

  /**
   * 获取日志统计信息
   * @param {Array} messages - 日志消息数组
   * @returns {object} 统计信息
   */
  getStats(messages) {
    const stats = {
      total: messages.length,
      byLevel: {},
      oldestLog: null,
      newestLog: null,
    };

    messages.forEach((msg) => {
      const level = msg.level || 'info';
      stats.byLevel[level] = (stats.byLevel[level] || 0) + 1;
    });

    if (messages.length > 0) {
      stats.oldestLog = messages[0].timestamp;
      stats.newestLog = messages[messages.length - 1].timestamp;
    }

    return stats;
  }
}

// 导出单例
export const logManager = new LogManager();

/**
 * 便捷函数：保存日志
 */
export function saveLogs(messages) {
  logManager.saveLogs(messages);
}

/**
 * 便捷函数：加载日志
 */
export function loadLogs() {
  return logManager.loadLogs();
}

/**
 * 便捷函数：导出日志
 */
export function exportLogs(messages, format = 'json', filename) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
  const defaultFilename = `logs_${timestamp}.${format === 'csv' ? 'csv' : format === 'text' ? 'txt' : 'json'}`;

  switch (format) {
    case 'csv':
      logManager.exportLogsAsCsv(messages, filename || defaultFilename);
      break;
    case 'text':
      logManager.exportLogsAsText(messages, filename || defaultFilename);
      break;
    case 'json':
    default:
      logManager.exportLogsAsJson(messages, filename || defaultFilename);
      break;
  }
}

/**
 * 便捷函数：清除日志
 */
export function clearLogs() {
  logManager.clearAllLogs();
}

/**
 * 便捷函数：获取日志统计
 */
export function getLogStats(messages) {
  return logManager.getStats(messages);
}
