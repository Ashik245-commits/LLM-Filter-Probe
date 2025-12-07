<template>
  <div ref="containerRef" class="scan-logs">
    <div class="panel-header">
      <h3>实时日志</h3>
      <div class="header-actions">
        <span class="log-count">
          {{ logs.messages.length }} 条
          <span v-if="logStats" class="log-stats-details">{{ logStats }}</span>
        </span>
        <span class="auto-scroll-indicator">
          <span class="pulse-dot"></span>
          自动滚动
        </span>
        <n-button
          v-if="logs.messages.length > 0"
          size="small"
          type="primary"
          ghost
          @click="() => handleExportSelect('json')"
        >
          导出为 JSON
        </n-button>
        <n-button
          v-if="logs.messages.length > 0"
          size="small"
          type="tertiary"
          @click="rootStore.clearLogs"
        >
          清空日志
        </n-button>
      </div>
    </div>

    <div class="console-wrapper">
      <div ref="consoleRef" class="console">
        <div
          v-for="(log, index) in logs.messages"
          :key="index"
          :class="['log-line', `log-${log.level}`]"
        >
          <span class="log-time">{{ formatTime(log.timestamp) }}</span>
          <span class="log-level">[{{ log.level.toUpperCase() }}]</span>
          <span class="log-message">
            <!-- 为特定日志添加图标和阶段标签 -->
            <span v-if="log.message.includes('[Macro]')" class="log-stage macro">二分算法</span>
            <span v-else-if="log.message.includes('[Micro]')" class="log-stage micro"
              >双向挤压算法</span
            >

            <span v-if="log.message.includes('敏感词定位完成')" class="log-icon"></span>
            <span
              v-else-if="
                log.message.includes('触发二分查找') || log.message.includes('触发智能交接')
              "
              class="log-icon"
            ></span>
            <span v-else-if="log.message.includes('三路探测')" class="log-icon"></span>
            <span v-else-if="log.message.includes('扫描完成')" class="log-icon">✅</span>
            <span v-else-if="log.message.includes('错误')" class="log-icon">❌</span>
            {{ log.message }}
          </span>
        </div>
        <div v-if="logs.messages.length === 0" class="log-empty">等待扫描开始...</div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * @file ScanLogs.vue
 * @description 实时日志显示组件。
 *
 * 该组件从 Pinia store 中获取日志消息，并以控制台的形式实时展示。
 * 主要功能包括：
 * - 自动滚动到底部以显示最新日志。
 * - 动态调整容器高度以适应内容。
 * - 提供日志导出（JSON, CSV, TXT）和清空功能。
 * - 显示日志统计信息（如错误、警告数量）。
 * - 为特定类型的日志（如算法阶段、成功、错误）添加视觉提示。
 */
import { ref, watch, nextTick, onMounted, computed } from 'vue';
import { storeToRefs } from 'pinia';
import { NButton, NDropdown } from 'naive-ui';
import { useRootStore } from '../stores/rootStore';
import { exportLogs, getLogStats } from '../utils/logManager';

const rootStore = useRootStore();
const { logs } = storeToRefs(rootStore);

const consoleRef = ref(null);
const containerRef = ref(null);

/**
 * 计算日志统计信息，用于在 UI 上显示错误、警告和成功日志的数量。
 * @returns {string|null} 格式化的统计字符串，例如 "(2 错误, 1 警告)"，如果没有可统计的日志则返回 null。
 */
const logStats = computed(() => {
  if (!logs.value.messages || logs.value.messages.length === 0) {
    return null;
  }
  const stats = getLogStats(logs.value.messages);
  const parts = [];
  if (stats.byLevel.error) parts.push(`${stats.byLevel.error} 错误`);
  if (stats.byLevel.warning) parts.push(`${stats.byLevel.warning} 警告`);
  if (stats.byLevel.success) parts.push(`${stats.byLevel.success} 成功`);
  return parts.length > 0 ? `(${parts.join(', ')})` : '';
});

/**
 * 处理日志导出下拉菜单的选择事件。
 * @param {string} key - 用户选择的导出格式（'json', 'csv', 'txt'）。
 */
const handleExportSelect = (key) => {
  try {
    exportLogs(logs.value.messages, key);
  } catch (error) {
    console.error(`导出日志失败 (格式: ${key}):`, error);
    // 可以在这里添加一个用户通知
  }
};

/**
 * 格式化时间戳为 HH:mm:ss.SSS 格式。
 * @param {string} timestamp - ISO 格式的时间戳字符串。
 * @returns {string} 格式化后的时间字符串。
 */
const formatTime = (timestamp) => {
  try {
    const date = new Date(timestamp);
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    const ms = String(date.getMilliseconds()).padStart(3, '0');
    return `${hours}:${minutes}:${seconds}.${ms}`;
  } catch {
    return timestamp;
  }
};

/**
 * 将日志控制台滚动到底部，以确保最新的日志可见。
 * 使用 nextTick 和 requestAnimationFrame 来确保在 DOM 更新后执行滚动。
 */
const scrollConsoleToBottom = () => {
  nextTick(() => {
    if (consoleRef.value) {
      // 使用 requestAnimationFrame 确保 DOM 已更新
      requestAnimationFrame(() => {
        consoleRef.value.scrollTop = consoleRef.value.scrollHeight;
      });
    }
  });
};

/**
 * 动态调整日志容器的高度以适应内容。
 * 这提供了一种“折叠”效果，当日志较少时容器较小，日志增多时容器变大，但有最大高度限制。
 */
const updateContainerHeight = () => {
  nextTick(() => {
    if (containerRef.value && consoleRef.value) {
      const scrollHeight = consoleRef.value.scrollHeight;
      const headerHeight = 44; // panel-header 的高度
      const totalNeeded = scrollHeight + headerHeight;

      // 最小 100px，最大 600px（增加最大高度以显示更多日志）
      const newHeight = Math.min(Math.max(totalNeeded, 100), 600);

      containerRef.value.style.height = newHeight + 'px';
    }
  });
};

// 监听日志消息变化，自动滚动到底部
watch(
  () => logs.value.messages.length,
  () => {
    scrollConsoleToBottom();
    updateContainerHeight();
  },
  { flush: 'post' } // 确保在 DOM 更新后执行
);

// 监听日志内容变化（防止日志内容更新时不滚动）
watch(
  () => logs.value.messages,
  () => {
    scrollConsoleToBottom();
  },
  { deep: true, flush: 'post' }
);

onMounted(() => {
  updateContainerHeight();
  scrollConsoleToBottom();
});
</script>

<style scoped>
/* Styles remain the same */
.scan-logs {
  display: flex;
  flex-direction: column;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  overflow: hidden;
  height: 100%;
  max-height: 100%;
  min-height: 0;
}
.panel-header {
  padding: 12px 16px;
  background: #f9f9f9;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.panel-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}
.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}
.log-count {
  font-size: 12px;
  color: #999;
  display: flex;
  align-items: center;
  gap: 6px;
}

.log-stats-details {
  color: #666;
  font-weight: 500;
}

.auto-scroll-indicator {
  font-size: 12px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 4px;
}

.pulse-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  background-color: #10b981;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
.console-wrapper {
  flex: 1;
  min-height: 100px;
  max-height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  height: 100%;
}
.console {
  position: relative;
  background: #1e1e1e;
  color: #d4d4d4;
  font-family: 'Consolas', 'Courier New', Courier, monospace;
  font-size: 13px;
  line-height: 1.6;
  padding: 16px;
  overflow-y: auto;
  overflow-x: hidden;
  scroll-behavior: smooth;
  max-height: 100%;
  height: 100%;
  box-sizing: border-box;
  flex: 1;
}
.console::-webkit-scrollbar {
  width: 8px;
}
.console::-webkit-scrollbar-track {
  background: #252526;
}
.console::-webkit-scrollbar-thumb {
  background: #424242;
  border-radius: 4px;
}
.console::-webkit-scrollbar-thumb:hover {
  background: #4e4e4e;
}
.log-line {
  display: flex;
  gap: 8px;
}
.log-time {
  color: #888;
}
.log-level {
  font-weight: 600;
}
.log-info {
  color: #4ec9b0;
}
.log-warning {
  color: #dcdcaa;
}
.log-error {
  color: #f48771;
}
.log-success {
  color: #89d185;
  font-weight: 600;
}
.log-empty {
  color: #666;
  text-align: center;
  padding: 20px;
}
.log-icon {
  margin-right: 6px;
  font-weight: bold;
}
.log-stage {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 600;
  margin-right: 8px;
}
.log-stage.macro {
  background-color: #4a5f8f;
  color: #a8d5ff;
}
.log-stage.micro {
  background-color: #6f4a8f;
  color: #d8a8ff;
}
</style>
