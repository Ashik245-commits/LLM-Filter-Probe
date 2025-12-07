<template>
  <div class="scan-controls-wrapper">
    <n-tooltip trigger="hover" placement="top" :disabled="isScanning">
      <template #trigger>
        <n-button
          v-if="!isScanning"
          type="primary"
          size="large"
          :disabled="disabled"
          class="scan-button"
          @click="$emit('start')"
        >
          开始扫描
        </n-button>
        <n-button v-else type="error" size="large" class="scan-button" @click="$emit('stop')">
          停止扫描
        </n-button>
      </template>
      <span>{{ tooltipText }}</span>
    </n-tooltip>
  </div>
</template>

<script setup>
/**
 * @file ScanControls.vue
 * @description 扫描控制按钮组件。
 *
 * 这个组件根据 `isScanning` 状态显示“开始扫描”或“停止扫描”按钮。
 * 它还通过 `disabled` prop 控制按钮的可用性，并通过 `tooltipText` prop 显示提示信息。
 * 当按钮被点击时，它会发出 `start` 或 `stop` 事件。
 */
import { defineProps, defineEmits } from 'vue';
import { NButton, NTooltip } from 'naive-ui';

defineProps({
  isScanning: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  tooltipText: {
    type: String,
    default: '准备就绪',
  },
});

defineEmits(['start', 'stop']);
</script>

<style scoped>
.scan-controls-wrapper {
  display: flex;
  justify-content: flex-end;
  align-items: center;
}

.scan-button {
  min-width: 140px;
  font-size: 14px;
  font-weight: 600;
  height: 40px;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
  transition: all 0.3s ease;
}

.scan-button:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.5);
  transform: translateY(-2px);
}

.scan-button:active:not(:disabled) {
  transform: translateY(0);
}
</style>
