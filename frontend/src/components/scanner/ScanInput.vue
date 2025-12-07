<template>
  <div class="scan-input-wrapper">
    <div class="panel-header">
      <h3>输入文本</h3>
    </div>
    <n-input
      :value="modelValue"
      type="textarea"
      placeholder="粘贴要检测的文本... 或拖入文本文件"
      :rows="8"
      :disabled="disabled"
      clearable
      class="input-textarea"
      @update:value="emit('update:modelValue', $event)"
      @drop="handleFileDrop"
      @dragover.prevent
      @dragenter.prevent
    />
    <div class="input-footer">
      <div class="char-count-footer">
        <span class="char-count-label">字符数:</span>
        <span class="char-count-value">{{ modelValue.length }}</span>
      </div>
      <div v-if="$slots.controls" class="controls-slot">
        <slot name="controls"></slot>
      </div>
    </div>
    <n-alert v-if="error" type="error" closable @close="error = ''">
      {{ error }}
    </n-alert>
  </div>
</template>

<script setup>
/**
 * @file ScanInput.vue
 * @description 扫描输入组件，提供文本输入框和文件拖拽功能。
 *
 * 该组件支持 `v-model` 双向绑定，并提供了一个插槽 (`controls`) 用于嵌入控制按钮。
 * 它还内置了文件拖拽功能，可以读取文本文件的内容并更新 `modelValue`。
 */
import { ref, defineEmits, defineProps } from 'vue';
import { NInput, NAlert } from 'naive-ui';

defineProps({
  modelValue: {
    type: String,
    required: true,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['update:modelValue']);
const error = ref('');

/**
 * 处理文件拖拽事件。
 * @param {DragEvent} event - 拖拽事件对象。
 */
const handleFileDrop = async (event) => {
  event.preventDefault();
  event.stopPropagation();

  const files = event.dataTransfer?.files;
  if (!files || files.length === 0) return;

  const file = files[0];
  const textMimeTypes = [
    'text/plain',
    'text/html',
    'text/xml',
    'text/csv',
    'application/json',
    'application/javascript',
    'text/javascript',
    'text/markdown',
  ];
  const isTextFile =
    textMimeTypes.includes(file.type) ||
    file.name.match(/\.(txt|md|json|xml|csv|log|py|js|java|html|css)$/i);

  if (!isTextFile && file.size > 0) {
    error.value = `❌ 不支持的文件类型: ${file.type || '未知'}。请拖入文本文件。`;
    return;
  }

  const reader = new FileReader();
  reader.onload = (e) => {
    try {
      const content = e.target?.result;
      if (typeof content === 'string') {
        emit('update:modelValue', content);
        error.value = '';
      }
    } catch (err) {
      error.value = `❌ 文件读取失败: ${err.message}`;
    }
  };
  reader.onerror = () => {
    error.value = '❌ 文件读取失败';
  };
  reader.readAsText(file);
};
</script>

<style scoped>
.scan-input-wrapper {
  display: flex;
  flex-direction: column;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  overflow: hidden;
}

.panel-header {
  padding: 12px 16px;
  background: #f9f9f9;
  border-bottom: 1px solid #e0e0e0;
}

.panel-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.input-textarea {
  flex: 1;
  border-radius: 0;
  border: none;
}

.input-footer {
  padding: 12px;
  background: #f9f9f9;
  border-top: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.char-count-footer {
  font-size: 12px;
  color: #666;
}

.char-count-label {
  font-weight: 600;
}

.char-count-value {
  font-weight: 700;
  color: #3b82f6;
  font-size: 14px;
}

.controls-slot {
  display: flex;
  align-items: center;
}
</style>
