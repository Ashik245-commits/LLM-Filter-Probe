<template>
  <div class="advanced-config">
    <n-form label-placement="top">
      <n-grid :cols="2" :x-gap="12" :y-gap="8">
        <!-- 并发数 - 占满整行 -->
        <n-gi span="2">
          <n-form-item label="并发数" path="concurrency">
            <n-popover trigger="focus" placement="top" :show-arrow="true">
              <template #trigger>
                <n-slider
                  v-model:value="settingsConfig.concurrency"
                  :min="1"
                  :max="50"
                  :step="1"
                  :disabled="disabled"
                />
              </template>
              <div style="max-width: 300px; line-height: 1.6">
                <strong>并发数说明</strong><br />
                <strong>范围：1-50</strong><br />
                同时发送的 HTTP 请求数量。<br />
                • <strong>1-5</strong>：低并发，适合网络不稳定或服务器限制严格的环境<br />
                • <strong>5-15</strong>：推荐值，平衡速度和服务器压力<br />
                • <strong>15-30</strong>：高并发，适合网络稳定且服务器性能好的环境<br />
                • <strong>30-50</strong>：极高并发，可能导致请求被拒绝或 IP 被限制<br />
                💡 并发数越高，扫描速度越快，但也会增加服务器压力
              </div>
            </n-popover>
          </n-form-item>
        </n-gi>

        <!-- 最大重试次数 + 重试抖动 -->
        <n-gi span="1">
          <n-form-item label="最大重试次数" path="max_retries">
            <n-popover trigger="focus" placement="top" :show-arrow="true">
              <template #trigger>
                <n-input-number
                  v-model:value="settingsConfig.max_retries"
                  :min="1"
                  :max="10"
                  :step="1"
                  :disabled="disabled"
                  :show-button="false"
                  size="small"
                  style="width: 100%"
                  placeholder="建议 3-5 次"
                />
              </template>
              <div style="max-width: 300px; line-height: 1.6">
                <strong>最大重试次数说明</strong><br />
                <strong>范围：1-10</strong><br />
                • <strong>1-3 次</strong>：快速扫描，适合网络稳定的环境<br />
                • <strong>3-5 次</strong>：推荐值，平衡速度和可靠性<br />
                • <strong>5-10 次</strong>：网络不稳定时使用，增加成功率<br />
                💡 每次重试间隔会加入随机抖动以避免请求堆积
              </div>
            </n-popover>
          </n-form-item>
        </n-gi>

        <n-gi span="1">
          <n-form-item label="重试抖动" path="jitter">
            <n-popover trigger="focus" placement="top" :show-arrow="true">
              <template #trigger>
                <n-input-number
                  v-model:value="settingsConfig.jitter"
                  :min="0"
                  :max="5"
                  :step="0.1"
                  :disabled="disabled"
                  :show-button="false"
                  size="small"
                  style="width: 100%"
                  placeholder="建议 0.5-1.0"
                />
              </template>
              <div style="max-width: 300px; line-height: 1.6">
                <strong>重试抖动说明 (秒)</strong><br />
                <strong>范围：0-5</strong><br />
                • <strong>0</strong>：无抖动，立即重试（可能导致请求堆积）<br />
                • <strong>0.5-1.0</strong>：推荐值，避免请求同时到达<br />
                • <strong>1.0-5.0</strong>：网络拥塞时使用，增加间隔<br />
                💡 抖动是在重试间隔基础上添加的随机延迟
              </div>
            </n-popover>
          </n-form-item>
        </n-gi>

        <!-- 超时时间 + Token 上限 -->
        <n-gi span="1">
          <n-form-item label="超时时间" path="timeout_seconds">
            <n-popover trigger="focus" placement="top" :show-arrow="true">
              <template #trigger>
                <n-input-number
                  v-model:value="settingsConfig.timeout_seconds"
                  :min="1"
                  :max="120"
                  :step="5"
                  :disabled="disabled"
                  :show-button="false"
                  size="small"
                  style="width: 100%"
                  placeholder="建议 20-50"
                />
              </template>
              <div style="max-width: 300px; line-height: 1.6">
                <strong>超时时间说明 (秒)</strong><br />
                <strong>范围：1-120</strong><br />
                • <strong>1-10</strong>：快速超时，适合网络快速的环境<br />
                • <strong>20-50</strong>：推荐值，适合大多数 API 服务<br />
                • <strong>50-120</strong>：网络较慢或大模型处理时间长时使用<br />
                💡 超时过短会导致请求中断，过长会影响扫描效率
              </div>
            </n-popover>
          </n-form-item>
        </n-gi>

        <n-gi span="1">
          <n-form-item label="Token 上限" path="token_limit">
            <n-popover trigger="focus" placement="top" :show-arrow="true">
              <template #trigger>
                <n-input-number
                  v-model:value="settingsConfig.token_limit"
                  :min="1"
                  :max="1000"
                  :step="1"
                  :disabled="disabled"
                  :show-button="false"
                  size="small"
                  style="width: 100%"
                  placeholder="建议 100-500"
                />
              </template>
              <div style="max-width: 300px; line-height: 1.6">
                <strong>Token 上限说明</strong><br />
                <strong>范围：1-1000</strong><br />
                • <strong>&lt;100</strong>：推荐值，如果不需要使用关键词拦截，填1即可<br />
                • <strong>100-1000</strong>：可能增大费用<br />
                💡 Token 上限决定了每次请求模型最多返回的输出内容，决定了API花费
              </div>
            </n-popover>
          </n-form-item>
        </n-gi>

        <!-- 分块大小 + 最小粒度 -->
        <n-gi span="1">
          <n-form-item label="分块大小" path="chunk_size">
            <n-popover trigger="focus" placement="top" :show-arrow="true">
              <template #trigger>
                <n-input-number
                  v-model:value="settingsConfig.chunk_size"
                  :min="100"
                  :max="1000000"
                  :step="100"
                  :disabled="disabled"
                  :show-button="false"
                  size="small"
                  style="width: 100%"
                  placeholder="建议 20000-50000"
                />
              </template>
              <div style="max-width: 300px; line-height: 1.6">
                <strong>分块大小说明 (字符)</strong><br />
                <strong>范围：100-1,000,000</strong><br />
                • <strong>100-1,000</strong>：极小块，用于精细扫描<br />
                • <strong>1,000-10,000</strong>：小块，如果频繁遇到 Token 限制，可使用此值<br />
                • <strong>10,000-20,000</strong>：平衡方案，适合混合内容<br />
                • <strong>20,000-50,000</strong>：推荐值，可显著减少请求数<br />
                • <strong>50,000-1,000,000</strong>：大块，适合处理长文本<br />
                💡 更大的块可以一次扫描更多文本，但如果超过模型上下文限制会自动分割
              </div>
            </n-popover>
          </n-form-item>
        </n-gi>

        <n-gi span="1">
          <n-form-item label="最小粒度" path="min_granularity">
            <n-popover trigger="focus" placement="top" :show-arrow="true">
              <template #trigger>
                <n-input-number
                  v-model:value="settingsConfig.min_granularity"
                  :min="1"
                  :max="1000"
                  :step="5"
                  :disabled="disabled"
                  :show-button="false"
                  size="small"
                  style="width: 100%"
                  placeholder="建议 15-50"
                />
              </template>
              <div style="max-width: 300px; line-height: 1.6">
                <strong>最小粒度说明 (字符)</strong><br />
                <strong>范围：1-1000</strong><br />
                最终定位的敏感词最小长度。当文本段长度小于此值时，停止递归分割。<br />
                • <strong>1</strong>：推荐值，精确匹配 1-3 字符的敏感词<br />
                • <strong>2-5</strong>：适合 2-5 字符的敏感词<br />
                • <strong>10-50</strong>：快速扫描，但可能遗漏短敏感词<br />
                💡 设置为 1 可以精确定位所有长度的敏感词
              </div>
            </n-popover>
          </n-form-item>
        </n-gi>

        <!-- 重叠大小 + 文本分割符 -->
        <n-gi span="1">
          <n-form-item label="重叠大小" path="overlap_size">
            <n-popover trigger="focus" placement="top" :show-arrow="true">
              <template #trigger>
                <n-input-number
                  v-model:value="settingsConfig.overlap_size"
                  :min="0"
                  :max="1000"
                  :step="1"
                  :disabled="disabled"
                  :show-button="false"
                  size="small"
                  style="width: 100%"
                  placeholder="建议 5-15"
                />
              </template>
              <div style="max-width: 300px; line-height: 1.6">
                <strong>重叠大小说明 (字符)</strong><br />
                <strong>范围：0-1000</strong><br />
                二分切分时的重叠安全区，防止敏感词被分割。<br />
                • <strong>15</strong>：推荐值，覆盖长词<br />
                • <strong>0-10</strong>：较小重叠，适合短敏感词<br />
                • <strong>20-50</strong>：更安全但会增加重复检测<br />
                • <strong>50-1000</strong>：实验性，不推荐设置大敏感词长度<br />
                💡 中文检测设置为15即可
              </div>
            </n-popover>
          </n-form-item>
        </n-gi>

        <n-gi span="1">
          <n-form-item label="文本分割符" path="delimiter">
            <n-popover trigger="focus" placement="top" :show-arrow="true">
              <template #trigger>
                <n-input
                  v-model:value="settingsConfig.delimiter"
                  placeholder="例如 \n 或 \n\n"
                  :disabled="disabled"
                  size="small"
                />
              </template>
              <div style="max-width: 300px; line-height: 1.6">
                <strong>文本分割符说明</strong><br />
                用于在二分查找前对文本进行初步分割。<br />
                💡 对于本项目算法 本参数对效果实际影响不大 默认为空即可
              </div>
            </n-popover>
          </n-form-item>
        </n-gi>

        <!-- 系统代理 - 占满整行 -->
        <n-gi span="2">
          <n-form-item label="系统代理" path="use_system_proxy">
            <n-popover trigger="hover" placement="top" :show-arrow="true">
              <template #trigger>
                <n-switch v-model:value="settingsConfig.use_system_proxy" :disabled="disabled">
                  <template #checked> 开启 </template>
                  <template #unchecked> 关闭 </template>
                </n-switch>
              </template>
              <div style="max-width: 300px; line-height: 1.6">
                <strong>系统代理说明</strong><br />
                是否使用操作系统的代理设置进行网络请求。<br />
                • <strong>开启</strong>：所有网络请求将通过系统配置的代理服务器。<br />
                • <strong>关闭</strong>：网络请求将直接发送，不使用任何代理。<br />
                💡 如果你处于需要代理才能访问外部网络的环境（如公司内网），请开启此选项。
              </div>
            </n-popover>
          </n-form-item>
        </n-gi>

        <!-- 保存按钮 -->
        <n-gi span="2">
          <div class="action-buttons">
            <!-- 重置为默认按钮 -->
            <n-button type="primary" ghost :disabled="disabled" size="medium" @click="handleReset">
              重置为默认
            </n-button>

            <!-- 保存高级设置按钮 -->
            <n-button
              type="primary"
              :loading="settingsConfig.isSaving"
              :disabled="disabled"
              size="medium"
              @click="handleSave"
            >
              保存高级设置
            </n-button>
          </div>
        </n-gi>
      </n-grid>
    </n-form>
  </div>
</template>

<script setup>
/**
 * @file AdvancedConfig.vue
 * @description 高级设置配置组件。
 *
 * 该组件提供用于调整应用核心行为的表单字段，包括：
 * - 网络设置（并发数、超时、重试）
 * - 算法参数（分块大小、最小粒度、重叠大小）
 * - 系统设置（系统代理）
 *
 * 它还提供了“重置为默认”和“保存”功能。
 */
import { storeToRefs } from 'pinia';
import {
  NForm,
  NFormItem,
  NGrid,
  NGi,
  NSlider,
  NInputNumber,
  NInput,
  NSwitch,
  NButton,
  NPopover,
  useMessage,
} from 'naive-ui';
import { useRootStore } from '../../stores/rootStore';

defineProps({
  disabled: {
    type: Boolean,
    default: false,
  },
});

const rootStore = useRootStore();
const message = useMessage();

const { settingsConfig } = storeToRefs(rootStore);

/**
 * 保存高级设置
 */
const handleSave = async () => {
  try {
    await rootStore.saveSettings();
    message.success('✅ 高级设置已保存');
  } catch (error) {
    console.error('[AdvancedConfig] 保存失败:', error);
    message.error(`❌ 保存失败: ${error.message}`);
  }
};

/**
 * 重置为默认值
 */
const handleReset = async () => {
  try {
    // 创建一个包含默认值的对象
    const defaultSettings = {
      concurrency: 15,
      timeout_seconds: 30,
      max_retries: 3,
      chunk_size: 30000,
      token_limit: 20,
      jitter: 0.5,
      delimiter: '\n',
      use_system_proxy: true,
      min_granularity: 1,
      overlap_size: 12,
    };

    // 遍历并更新 store 中的每个字段
    for (const key in defaultSettings) {
      rootStore.updateSettingField(key, defaultSettings[key]);
    }

    // 保存重置后的配置
    await rootStore.saveSettings();
    message.success('✅ 已重置为默认值并保存');
  } catch (error) {
    console.error('[AdvancedConfig] 重置失败:', error);
    message.error(`❌ 重置失败: ${error.message}`);
  }
};
</script>

<style scoped>
.advanced-config {
  width: 100%;
}

:deep(.n-form-item) {
  margin-bottom: 0 !important;
}

:deep(.n-form-item__label) {
  margin-bottom: 4px;
  font-size: 13px;
  font-weight: 500;
}

:deep(.n-form-item__content) {
  font-size: 13px;
}

.action-buttons {
  display: flex;
  gap: 8px;
  margin-top: 4px;
  padding-top: 8px;
  border-top: 1px solid #e0e6ed;
}
</style>
