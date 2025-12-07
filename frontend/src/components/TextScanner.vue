<template>
  <div class="text-scanner-refactored">
    <div class="scanner-layout">
      <!-- 日志面板 -->
      <div class="console-section">
        <ScanLogs />
      </div>

      <!-- 扫描控制与输入 -->
      <div class="scan-controls-and-input">
        <ScanInput v-model="inputText" :disabled="isScanning">
          <template #controls>
            <ScanControls
              :is-scanning="isScanning"
              :disabled="isScanDisabled || inputText.trim() === ''"
              :tooltip-text="tooltipText"
              @start="startScan(inputText)"
              @stop="stopScan"
            />
          </template>
        </ScanInput>
      </div>

      <!-- 结果表格 -->
      <div class="results-section">
        <ScanResults />
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="scanError" class="error-alert">
      <n-alert type="error" closable @close="scanError = ''">
        {{ scanError }}
      </n-alert>
    </div>
  </div>
</template>

<script setup>
/**
 * @file TextScanner.vue
 * @description 文本扫描器的主 UI 组件。
 *
 * 这个组件负责整合扫描功能的各个部分，包括：
 * - 日志显示 (ScanLogs)
 * - 文本输入 (ScanInput)
 * - 扫描控制按钮 (ScanControls)
 * - 结果展示 (ScanResults)
 *
 * 它通过 `useTextScanner` composable 与 Pinia store 交互，获取扫描状态并调用操作，
 * 自身只管理最小化的 UI 状态（如输入框的文本）。
 */
import { ref } from 'vue';
import { NAlert } from 'naive-ui';

import { useTextScanner } from '../composables/useTextScanner';

// 导入子组件
import ScanInput from './scanner/ScanInput.vue';
import ScanControls from './scanner/ScanControls.vue';
import ScanLogs from './ScanLogs.vue';
import ScanResults from './ScanResults.vue';

// 从 composable 中解构出状态和方法
const { isScanning, scanError, isScanDisabled, tooltipText, startScan, stopScan } =
  useTextScanner();

const inputText = ref('');
</script>

<style scoped>
.text-scanner-refactored {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.scanner-layout {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  padding: 16px;
  height: 100%;
}

.console-section {
  flex: 0 0 auto;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 100px;
  max-height: 400px;
}

.scan-controls-and-input {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.results-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.error-alert {
  padding: 0 16px 16px; /* 错误提示放在布局底部 */
}
</style>
