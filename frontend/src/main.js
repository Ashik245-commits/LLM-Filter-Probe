import { createApp } from 'vue';
import { createPinia } from 'pinia';
import naive from 'naive-ui';
import AppProvider from './AppProvider.vue';

/**
 * 创建 Vue 应用实例，使用 AppProvider 作为根组件。
 * AppProvider 作为一个集中的提供者组件，用于包裹整个应用，
 * 以便在应用顶层统一处理 Naive UI 的主题、对话框、通知等全局服务。
 */
const app = createApp(AppProvider);

// 注册 Pinia 状态管理库
app.use(createPinia());

// 注册 Naive UI 组件库
app.use(naive);

// 将应用挂载到 DOM 中的 #app 元素上
app.mount('#app');
