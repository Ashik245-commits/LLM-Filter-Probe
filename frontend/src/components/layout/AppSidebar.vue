<template>
  <n-layout-sider
    :width="320"
    :collapsed="false"
    :bordered="true"
    :resizable="false"
    class="sidebar"
  >
    <div class="sidebar-content">
      <div class="logo">
        <h2>配置</h2>
      </div>

      <!-- 配置面板 -->
      <Settings :disabled="disabled" />
    </div>
  </n-layout-sider>
</template>

<script setup>
/**
 * @file AppSidebar.vue
 * @description 应用的侧边栏组件。
 *
 * 该组件作为所有配置项的容器，并根据 `disabled` prop 的状态（例如，在扫描进行中时）
 * 将其所有子组件（即整个设置面板）禁用。
 */
import Settings from '../settings/Settings.vue';

defineProps({
  /**
   * 是否禁用侧边栏中的所有控件。
   * @type {boolean}
   */
  disabled: {
    type: Boolean,
    default: false,
  },
});
</script>

<style scoped>
/* 侧边栏样式 */
.sidebar {
  /* 使用 Naive UI 主题变量 */
  background: var(--n-color);
  border-right: 1px solid var(--n-border-color);
  /* 确保不被主内容覆盖 */
  z-index: 10;
  flex-shrink: 0;
  /* 允许动态调整宽度 */
  width: 320px !important;
  min-width: 200px !important;
  max-width: 600px !important;
}

.sidebar-content {
  padding: 20px;
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  word-break: break-word;
  white-space: normal;
  word-wrap: break-word;
  /* 防止滚动条与内容重叠 */
  padding-right: 12px;
}

.logo {
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--n-border-color);
}

.logo h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--n-text-color);
  margin: 0;
  white-space: nowrap;
}
</style>
