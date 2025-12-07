<template>
  <div class="connection-form">
    <n-form ref="formRef">
      <!-- API 地址 -->
      <n-form-item label="API 地址" path="api_url">
        <n-popover placement="top" trigger="focus" :show-arrow="true">
          <template #trigger>
            <n-input
              :value="apiConfig.api_url"
              type="text"
              placeholder="https://api.openai.com/v1/"
              clearable
              :disabled="disabled"
              @update:value="(value) => rootStore.updateApiField('api_url', value)"
            />
          </template>
          <span>API 地址应包含 /v1 路径</span>
        </n-popover>
      </n-form-item>

      <!-- API Key -->
      <n-form-item label="API Key" path="api_key">
        <n-input
          :value="apiConfig.api_key"
          type="password"
          placeholder="输入 API Key (sk-...)"
          clearable
          show-password-on="click"
          :disabled="disabled"
          @update:value="(value) => rootStore.updateApiField('api_key', value)"
        />
      </n-form-item>

      <!-- 模型名称 -->
      <n-form-item label="模型名称 (api_model)" path="api_model">
        <n-popover placement="top" trigger="focus" :show-arrow="true">
          <template #trigger>
            <n-input
              :value="apiConfig.api_model"
              placeholder="输入模型名称，例如 gpt-4o-mini"
              clearable
              :disabled="disabled"
              @update:value="(value) => rootStore.updateApiField('api_model', value)"
            />
          </template>
          <span>请选择一个价格便宜、上下文长、并且响应快的模型</span>
        </n-popover>
      </n-form-item>

      <!-- 操作按钮 -->
      <div style="display: flex; gap: 8px; margin-top: 16px; flex-wrap: wrap; align-items: center">
        <!-- 测试连接按钮 -->
        <n-button
          type="default"
          size="medium"
          :loading="apiConfigUI.isTesting"
          :disabled="disabled || !apiConfig.api_url || !apiConfig.api_key || !apiConfig.api_model"
          @click="handleTestConnection"
        >
          <template #icon>
            <span v-if="apiConfigUI.testStatus === 'untested'"></span>
            <span v-else-if="apiConfigUI.testStatus === 'passed'">✅</span>
            <span v-else-if="apiConfigUI.testStatus === 'failed'">❌</span>
          </template>
          测试连接
        </n-button>

        <!-- 保存按钮 -->
        <n-tooltip placement="top" trigger="hover" :disabled="apiConfigUI.testStatus === 'passed'">
          <template #trigger>
            <n-button
              type="primary"
              size="medium"
              :loading="apiConfigUI.isSaving"
              :disabled="disabled || apiConfigUI.testStatus !== 'passed'"
              @click="handleSaveApiConfig"
            >
              保存并应用
            </n-button>
          </template>
          <span>请先成功测试连接后再保存</span>
        </n-tooltip>
      </div>
    </n-form>
  </div>
</template>

<script setup>
/**
 * @file ConnectionForm.vue
 * @description API 连接设置表单组件。
 *
 * 该组件提供用于输入 API 地址、密钥和模型名称的表单字段，
 * 并包含“测试连接”和“保存”按钮，用于验证和持久化 API 凭证。
 */
import { storeToRefs } from 'pinia';
import { NButton, NForm, NFormItem, NInput, NTooltip, NPopover, useMessage } from 'naive-ui';
import { useRootStore } from '../../stores/rootStore';

defineProps({
  disabled: {
    type: Boolean,
    default: false,
  },
});

const message = useMessage();
const rootStore = useRootStore();

// Destructure reactive state from the root store
const { apiConfig, apiConfigUI } = storeToRefs(rootStore);

/**
 * 处理测试连接按钮的点击事件
 */
async function handleTestConnection() {
  try {
    await rootStore.testConnection();
    if (apiConfigUI.value.testStatus === 'passed') {
      message.success('✅ 连接测试成功！');
    } else {
      message.error('❌ 连接测试失败');
    }
  } catch (err) {
    console.error('❌ 测试 API 连接失败:', err);
    message.error(`测试失败: ${err?.message || '未知错误'}`);
  }
}

/**
 * 处理保存 API 配置按钮的点击事件
 */
async function handleSaveApiConfig() {
  try {
    await rootStore.saveApiConfig();
    message.success('✅ API 配置已保存并应用！');
  } catch (err) {
    console.error('❌ 保存 API 配置失败:', err);
    message.error(`保存失败: ${err?.message || '未知错误'}`);
  }
}
</script>

<style scoped>
.connection-form {
  width: 100%;
}
</style>
