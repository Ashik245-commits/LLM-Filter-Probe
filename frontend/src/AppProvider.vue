<template>
  <n-config-provider :theme="null">
    <n-message-provider>
      <n-dialog-provider>
        <App />
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import App from './App.vue';
</script>

<style scoped>
/* AppProvider 是纯容器组件，不需要额外样式 */
</style>
