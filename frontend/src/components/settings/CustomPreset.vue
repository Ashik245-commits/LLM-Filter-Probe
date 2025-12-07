<template>
  <div class="custom-preset-container">
    <!-- 规则配置区域 -->
    <div class="rules-section">
      <n-grid cols="1" x-gap="12" y-gap="0">
        <!-- 阻断状态码 -->
        <n-gi>
          <div class="rule-header">
            <span class="rule-icon"></span>
            <span class="rule-title">阻断状态码 (Block Status Codes)</span>
          </div>
          <n-form-item path="block_status_codes" :show-label="false" :show-feedback="false">
            <n-dynamic-tags
              :value="presetsConfig.customRules.block_status_codes.map(String)"
              :render-tag="(tag, index) => renderTag(tag, index, 'success')"
              :on-create="(label) => onCreateTag(label, 'block_status_codes')"
              placeholder="输入数字后回车（如 403、429）"
              :disabled="disabled"
              size="small"
              @update:value="onBlockStatusCodesChange"
            />
          </n-form-item>
          <div class="helper-text">请求遇到这些 HTTP 状态码时将被视为阻断。</div>
        </n-gi>

        <!-- 阻断关键字 -->
        <n-gi>
          <div class="rule-header">
            <span class="rule-icon"></span>
            <span class="rule-title">阻断关键字 (Block Keywords)</span>
          </div>
          <n-form-item path="block_keywords" :show-label="false" :show-feedback="false">
            <n-dynamic-tags
              :value="presetsConfig.customRules.block_keywords"
              :render-tag="(tag, index) => renderTag(tag, index, 'default')"
              :on-create="(label) => onCreateTag(label, 'block_keywords')"
              placeholder="输入关键字后回车（如 captcha、forbidden）"
              :disabled="disabled"
              size="small"
              @update:value="onBlockKeywordsChange"
            />
          </n-form-item>
          <div class="helper-text">响应内容包含这些关键字时将被视为阻断。</div>
        </n-gi>

        <!-- 重试状态码 -->
        <n-gi>
          <div class="rule-header">
            <span class="rule-icon"></span>
            <span class="rule-title">重试状态码 (Retry Status Codes)</span>
          </div>
          <n-form-item path="retry_status_codes" :show-label="false" :show-feedback="false">
            <n-dynamic-tags
              :value="presetsConfig.customRules.retry_status_codes.map(String)"
              :render-tag="(tag, index) => renderTag(tag, index, 'warning')"
              :on-create="(label) => onCreateTag(label, 'retry_status_codes')"
              placeholder="输入数字后回车（如 500、502、503）"
              :disabled="disabled"
              size="small"
              @update:value="onRetryStatusCodesChange"
            />
          </n-form-item>
          <div class="helper-text">遇到这些状态码会进行自动重试。</div>
        </n-gi>
      </n-grid>
    </div>

    <!-- 保存按钮 (仅在 custom 模式下显示) -->
    <div v-if="!disabled" class="action-buttons">
      <!-- 重置为默认按钮 -->
      <n-button
        type="primary"
        ghost
        size="medium"
        :disabled="presetsConfig.isSaving || disabled"
        @click="resetCustomConfig"
      >
        重置为空
      </n-button>

      <!-- 保存自定义配置按钮 -->
      <n-button
        type="primary"
        size="medium"
        :loading="presetsConfig.isSaving"
        :disabled="disabled"
        @click="saveCustomConfig"
      >
        保存自定义规则
      </n-button>
    </div>
  </div>
</template>

<script setup>
/**
 * @file CustomPreset.vue
 * @description 自定义预设配置组件。
 *
 * 该组件允许用户编辑“Custom”预设的规则，包括：
 * - 阻断状态码
 * - 阻断关键字
 * - 重试状态码
 *
 * 当 `disabled` prop 为 true 时，所有输入都将被禁用。
 */
import { h } from 'vue';
import { storeToRefs } from 'pinia';
import { NGrid, NGi, NFormItem, NDynamicTags, NTag, NButton, useMessage } from 'naive-ui';
import { useRootStore } from '../../stores/rootStore';

const props = defineProps({
  disabled: {
    type: Boolean,
    default: false,
  },
});

const message = useMessage();
const rootStore = useRootStore();

// Destructure reactive state from the root store
const { presetsConfig } = storeToRefs(rootStore);

/**
 * 渲染动态标签。
 * @param {string} tag - 标签的文本内容。
 * @param {number} index - 标签的索引。
 * @param {string} type - 标签的类型（'success', 'warning', 'default'），用于决定颜色。
 * @returns {VNode} Naive UI 的 NTag 组件。
 */
function renderTag(tag, index, type) {
  return h(
    NTag,
    {
      type,
      round: true,
      closable: !props.disabled,
      onClose: () => handleTagClose(index, type),
    },
    { default: () => tag }
  );
}

/**
 * 处理标签关闭事件。
 * @param {number} index - 要移除的标签的索引。
 * @param {string} type - 标签的类型，用于确定从哪个数组中移除。
 */
function handleTagClose(index, type) {
  if (type === 'success') {
    presetsConfig.value.customRules.block_status_codes.splice(index, 1);
  } else if (type === 'warning') {
    presetsConfig.value.customRules.retry_status_codes.splice(index, 1);
  } else {
    presetsConfig.value.customRules.block_keywords.splice(index, 1);
  }
}

/**
 * 处理新标签的创建事件，包括输入值的清理和验证。
 * @param {string} label - 用户输入的标签文本。
 * @param {string} type - 标签的类型，用于确定添加到哪个数组并应用相应的验证规则。
 * @returns {string|null} 如果验证通过，返回清理后的标签文本；否则返回 null。
 */
function onCreateTag(label, type) {
  const sanitized = label.trim();
  if (!sanitized) return null;

  const targetArray = {
    block_status_codes: presetsConfig.value.customRules.block_status_codes,
    retry_status_codes: presetsConfig.value.customRules.retry_status_codes,
    block_keywords: presetsConfig.value.customRules.block_keywords,
  }[type];

  const stringArray = targetArray.map(String);
  if (stringArray.includes(sanitized)) {
    message.warning('该值已存在');
    return null;
  }

  if (type.includes('status_codes')) {
    if (!/^\d+$/.test(sanitized)) {
      message.warning('请输入有效的数字状态码');
      return null;
    }
  }

  return sanitized;
}

/**
 * 当“阻断状态码”标签更新时，同步状态。
 * @param {string[]} value - 新的标签值数组。
 */
function onBlockStatusCodesChange(value) {
  presetsConfig.value.customRules.block_status_codes = value.map((v) => parseInt(v, 10) || 0);
}

/**
 * 当“阻断关键字”标签更新时，同步状态。
 * @param {string[]} value - 新的标签值数组。
 */
function onBlockKeywordsChange(value) {
  presetsConfig.value.customRules.block_keywords = value;
}

/**
 * 当“重试状态码”标签更新时，同步状态。
 * @param {string[]} value - 新的标签值数组。
 */
function onRetryStatusCodesChange(value) {
  presetsConfig.value.customRules.retry_status_codes = value.map((v) => parseInt(v, 10) || 0);
}

/**
 * 保存自定义规则。
 */
const saveCustomConfig = async () => {
  try {
    await rootStore.saveCustomRules();
    message.success('✅ 自定义规则已保存');
  } catch (error) {
    console.error('[CustomPreset] 保存失败:', error);
    message.error(`❌ 保存失败: ${error.message}`);
  }
};

/**
 * 将自定义规则重置为空并保存。
 */
const resetCustomConfig = async () => {
  try {
    presetsConfig.value.customRules.block_status_codes = [];
    presetsConfig.value.customRules.block_keywords = [];
    presetsConfig.value.customRules.retry_status_codes = [];
    await rootStore.saveCustomRules();
    message.success('✅ 自定义规则已重置为空');
  } catch (error) {
    console.error('[CustomPreset] 重置失败:', error);
    message.error(`❌ 重置失败: ${error.message}`);
  }
};
</script>

<style scoped>
.custom-preset-container {
  width: 100%;
}

.rules-section {
  margin-bottom: 8px;
}

:deep(.n-form-item) {
  margin-bottom: 0 !important;
}

:deep(.n-form-item__blank) {
  height: 0 !important;
}

.rule-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.rule-icon {
  font-size: 16px;
  display: inline-block;
}

.rule-title {
  font-weight: 600;
  font-size: 13px;
  color: #333;
}

.helper-text {
  margin-top: 4px;
  margin-bottom: 12px;
  font-size: 12px;
  color: #666;
  opacity: 0.8;
  line-height: 1.5;
}

.action-buttons {
  margin-top: 12px;
  display: flex;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid #e0e6ed;
}
</style>
