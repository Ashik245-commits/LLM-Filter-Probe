<template>
  <div class="scan-progress-wrapper">
    <!-- 进度头部 -->
    <div class="progress-header">
      <div class="header-left">
        <h4>📊 扫描进度</h4>
        <n-tag v-if="isScanning" type="warning" size="small" round style="margin-left: 8px">
          🔄 扫描中...
        </n-tag>
        <n-tag v-else-if="isPrecisionMode" type="info" size="small" round style="margin-left: 8px">
          🔍 精确定位中...
        </n-tag>
        <n-tag v-else-if="isCompleted" type="success" size="small" round style="margin-left: 8px">
          ✅ 已完成
        </n-tag>
      </div>
      <div class="header-right">
        <span class="stat-item">
          <span class="stat-label">进度:</span>
          <span class="stat-value">{{ progress.percentage }}%</span>
        </span>
        <span class="stat-separator">|</span>
        <span class="stat-item">
          <span class="stat-label">已扫描:</span>
          <span class="stat-value">{{ formatNumber(progress.scanned) }}</span>
        </span>
        <span class="stat-separator">|</span>
        <span class="stat-item">
          <span class="stat-label">敏感词:</span>
          <span class="stat-value sensitive">{{ progress.sensitive_count }}</span>
        </span>
      </div>
    </div>

    <!-- 进度条 -->
    <div class="progress-bar-section">
      <n-progress
        type="line"
        :percentage="progress.percentage"
        :indicator-placement="'inside'"
        :status="progressStatus"
        :height="28"
        border-radius="6px"
        show-indicator
      />
    </div>

    <!-- 精确扫描提示 -->
    <div v-if="isPrecisionMode" class="precision-hint">
      <div class="hint-content">
        <span class="hint-icon">🔍</span>
        <span class="hint-text">
          正在进行精确定位扫描，可能需要较长时间。系统正在逐字符分析以找到准确的敏感词位置...
        </span>
        <n-spin :size="'small'" />
      </div>
    </div>

    <!-- 详细统计 -->
    <div class="progress-details">
      <div class="detail-item">
        <span class="detail-label">总字符数:</span>
        <span class="detail-value">{{ formatNumber(progress.total) }}</span>
      </div>
      <div class="detail-item">
        <span class="detail-label">已扫描:</span>
        <span class="detail-value">{{ formatNumber(progress.scanned) }}</span>
      </div>
      <div class="detail-item">
        <span class="detail-label">剩余:</span>
        <span class="detail-value">{{ formatNumber(progress.total - progress.scanned) }}</span>
      </div>
      <div class="detail-item">
        <span class="detail-label">敏感片段:</span>
        <span class="detail-value sensitive">{{ progress.sensitive_count }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * @file ScanProgress.vue
 * @description 扫描进度显示组件。
 *
 * 该组件以可视化的方式展示扫描任务的实时进度，包括：
 * - 总体进度百分比。
 * - 已扫描/总字符数。
 * - 已发现的敏感词数量。
 * - 一个特殊的“精确定位中”状态，用于提示用户扫描已进入最后阶段。
 */
import { defineProps, computed } from 'vue';
import { NProgress, NTag, NSpin } from 'naive-ui';
import { useRootStore } from '../../stores/rootStore';

const props = defineProps({
  progress: {
    type: Object,
    required: true,
    default: () => ({
      scanned: 0,
      total: 0,
      percentage: 0,
      sensitive_count: 0,
    }),
  },
});

const rootStore = useRootStore();

// 计算属性
/**
 * 计算是否处于常规扫描状态（非精确定位阶段）。
 */
const isScanning = computed(() => {
  return rootStore.scanState.isScanning && !isPrecisionMode.value;
});

/**
 * 计算是否处于精确定位模式。
 * 这是一个启发式规则：当扫描仍在进行，但进度已达到一个较高阈值（如80%）时，
 * 我们假设扫描已进入消耗大量时间的精确定位阶段。
 */
const isPrecisionMode = computed(() => {
  // 当进度在 80-99% 之间且仍在扫描时，认为是精确定位模式
  return (
    rootStore.scanState.isScanning &&
    props.progress.percentage >= 80 &&
    props.progress.percentage < 100
  );
});

/**
 * 计算扫描是否已完成。
 */
const isCompleted = computed(() => {
  return !rootStore.scanState.isScanning && props.progress.percentage === 100;
});

/**
 * 根据扫描状态计算进度条的颜色。
 * @returns {'success' | 'info' | 'warning'} Naive UI 进度条的状态。
 */
const progressStatus = computed(() => {
  if (props.progress.percentage === 100) return 'success';
  if (isPrecisionMode.value) return 'info';
  return 'warning';
});

/**
 * 格式化数字，为其添加千位分隔符。
 * @param {number} num - 要格式化的数字。
 * @returns {string} 格式化后的字符串。
 */
const formatNumber = (num) => {
  if (!num) return '0';
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
};
</script>

<style scoped>
.scan-progress-wrapper {
  padding: 16px;
  background: linear-gradient(135deg, #f5f7fa 0%, #f9fafb 100%);
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-header h4 {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: #1f2937;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-label {
  color: #999;
  font-weight: 500;
}

.stat-value {
  color: #1f2937;
  font-weight: 700;
  font-family: 'Monaco', 'Courier New', monospace;
}

.stat-value.sensitive {
  color: #ef4444;
  font-size: 13px;
}

.stat-separator {
  color: #ddd;
  margin: 0 4px;
}

/* 进度条部分 */
.progress-bar-section {
  width: 100%;
}

/* 精确扫描提示 */
.precision-hint {
  padding: 12px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 6px;
  animation: slideIn 0.3s ease-out;
}

.hint-content {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #1e40af;
}

.hint-icon {
  font-size: 16px;
  animation: spin 2s linear infinite;
}

.hint-text {
  flex: 1;
  line-height: 1.5;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 详细统计 */
.progress-details {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  padding-top: 8px;
  border-top: 1px solid #e0e0e0;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
}

.detail-label {
  font-size: 11px;
  font-weight: 600;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-value {
  font-size: 14px;
  font-weight: 700;
  color: #1f2937;
  font-family: 'Monaco', 'Courier New', monospace;
}

.detail-value.sensitive {
  color: #ef4444;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .progress-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-right {
    width: 100%;
    flex-wrap: wrap;
  }

  .progress-details {
    grid-template-columns: repeat(2, 1fr);
  }

  .hint-content {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 480px) {
  .progress-details {
    grid-template-columns: 1fr;
  }

  .header-right {
    font-size: 11px;
  }
}
</style>
