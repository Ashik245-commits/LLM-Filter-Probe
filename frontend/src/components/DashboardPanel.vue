<template>
  <div class="dashboard-panel">
    <!-- Mission Control 头部卡片 -->
    <n-card class="mission-control" :bordered="false">
      <n-grid :cols="gridCols" :x-gap="24" :y-gap="16" responsive="screen">
        <!-- 左列：连接与健康状态 -->
        <n-grid-item>
          <div class="health-card">
            <!-- 标题 -->
            <div class="card-header">
              <h3 class="card-title">
                <n-icon class="title-icon">
                  <HeartbeatIcon />
                </n-icon>
                连接状态
              </h3>
              <div class="connectivity-dot" :class="system.connectionStatus"></div>
            </div>

            <!-- 内容网格 -->
            <div class="health-content">
              <!-- API 域名 -->
              <div class="metric-item">
                <div class="metric-label">
                  <n-icon class="metric-icon">
                    <GlobeIcon />
                  </n-icon>
                  API 域名
                </div>
                <div class="metric-value domain">{{ apiDomainDisplay }}</div>
              </div>

              <!-- 模型 -->
              <div class="metric-item">
                <div class="metric-label">
                  <n-icon class="metric-icon">
                    <CubeIcon />
                  </n-icon>
                  模型
                </div>
                <n-tag type="info" round size="small" class="model-tag">
                  {{ apiConfig.api_model || '--' }}
                </n-tag>
              </div>

              <!-- 实时延迟 -->
              <div class="metric-item">
                <div class="metric-label">
                  <n-icon class="metric-icon">
                    <SpeedometerIcon />
                  </n-icon>
                  实时延迟
                </div>
                <div class="metric-value latency" :class="latencyStatus">
                  {{ displayCurrentLatency }}
                </div>
              </div>

              <!-- 平均延迟 -->
              <div class="metric-item">
                <div class="metric-label">
                  <n-icon class="metric-icon">
                    <BarChartIcon />
                  </n-icon>
                  平均延迟
                </div>
                <div class="metric-value latency" :class="latencyStatus">
                  {{ displayAverageLatency }}
                </div>
              </div>
            </div>
          </div>
        </n-grid-item>

        <!-- 右列：任务进度 -->
        <n-grid-item>
          <div class="progress-card">
            <!-- 标题 -->
            <div class="card-header">
              <h3 class="card-title">
                <n-icon class="title-icon">
                  <RocketIcon />
                </n-icon>
                任务进度
                <n-tag :type="scanningStatusColor" round size="small" style="margin-left: 8px">
                  {{ scanningStatusText }}
                </n-tag>
              </h3>
              <span class="progress-percentage">{{ scanState.progress }}%</span>
            </div>

            <!-- 进度条 -->
            <div class="progress-bar-container">
              <n-progress
                :percentage="scanState.progress"
                :status="progressStatus"
                :show-indicator="true"
                :height="12"
                :border-radius="6"
              />
            </div>

            <!-- 统计网格 -->
            <div class="stats-grid">
              <!-- 总数 -->
              <div class="stat-box">
                <div class="stat-label">总字符</div>
                <div class="stat-value">{{ scanState.totalBytes }}</div>
              </div>

              <!-- 已扫描 -->
              <div class="stat-box">
                <div class="stat-label">已扫描</div>
                <div class="stat-value">{{ scanState.scannedBytes }}</div>
              </div>

              <!-- 敏感内容 -->
              <div class="stat-box sensitive">
                <div class="stat-label">敏感内容</div>
                <div class="stat-value">{{ results.statistics.found }}</div>
              </div>
            </div>
          </div>
        </n-grid-item>
      </n-grid>
    </n-card>
  </div>
</template>

<script setup>
/**
 * @file DashboardPanel.vue
 * @description 仪表盘面板组件。
 *
 * 该组件显示应用的核心状态和性能指标，包括：
 * - 后端连接状态、API 域名和当前模型。
 * - API 的实时和平均延迟。
 * - 当前扫描任务的进度和统计数据。
 * - 通过定期健康检查（心跳）来监控后端服务的可用性。
 */
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { storeToRefs } from 'pinia';
import { useRootStore } from '../stores/rootStore';
import { NCard, NGrid, NGridItem, NIcon, NProgress, NTag } from 'naive-ui';
import {
  Heart as HeartbeatIcon,
  Globe as GlobeIcon,
  Cube as CubeIcon,
  Speedometer as SpeedometerIcon,
  BarChart as BarChartIcon,
  Rocket as RocketIcon,
} from '@vicons/ionicons5';

const rootStore = useRootStore();

const { apiConfig, scanState, results, system, monitor, latencyStatus } = storeToRefs(rootStore);

const heartbeatInterval = ref(null);

const gridCols = '1 s:1 m:2 l:2';

/**
 * 从完整的 API URL 中提取并显示域名。
 * @returns {string} API 域名，如果 URL 无效或未设置则返回 '--'。
 */
const apiDomainDisplay = computed(() => {
  try {
    return apiConfig.value.api_url ? new URL(apiConfig.value.api_url).hostname : '--';
  } catch (e) {
    return '--';
  }
});

/**
 * 格式化用于显示的实时延迟。
 * @returns {string} 格式化的延迟字符串（例如 "123 ms"），如果无法获取则返回 '--'。
 */
const displayCurrentLatency = computed(() => {
  return system.value.connectionStatus === 'online' && monitor.value.currentLatency > 0
    ? `${monitor.value.currentLatency} ms`
    : '--';
});

/**
 * 格式化用于显示的平均延迟。
 * @returns {string} 格式化的延迟字符串（例如 "123 ms"），如果无法获取则返回 '--'。
 */
const displayAverageLatency = computed(() => {
  return system.value.connectionStatus === 'online' && monitor.value.averageLatency > 0
    ? `${monitor.value.averageLatency} ms`
    : '--';
});

/**
 * 根据扫描状态计算进度条的颜色状态。
 * @returns {'error' | 'success' | 'info' | 'default'} Naive UI 进度条的状态。
 */
const progressStatus = computed(() => {
  if (scanState.value.error) return 'error';
  if (scanState.value.progress === 100) return 'success';
  if (scanState.value.isScanning) return 'info';
  return 'default';
});

/**
 * 根据扫描状态计算用于显示的文本。
 * @returns {'扫描中...' | '空闲'} 状态文本。
 */
const scanningStatusText = computed(() => {
  if (scanState.value.isScanning) return '扫描中...';
  return '空闲';
});

/**
 * 根据扫描状态计算状态标签的颜色。
 * @returns {'warning' | 'default'} Naive UI 标签的颜色类型。
 */
const scanningStatusColor = computed(() => {
  if (scanState.value.isScanning) return 'warning';
  return 'default';
});

/**
 * 执行一次后端健康检查，并根据结果更新延迟和连接状态。
 */
const performHealthCheck = async () => {
  if (system.value.connectionStatus !== 'online') return;

  try {
    const startTime = performance.now();
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const response = await fetch('/api/health', { method: 'GET', signal: controller.signal });

    clearTimeout(timeoutId);
    const endTime = performance.now();
    const latency = Math.round(endTime - startTime);

    if (response.ok) {
      rootStore.recordLatency(latency);
    } else {
      rootStore.setConnectionStatus('offline');
    }
  } catch (err) {
    rootStore.setConnectionStatus('offline');
  }
};

/**
 * 启动心跳机制，定期执行健康检查。
 */
function startHeartbeat() {
  if (heartbeatInterval.value) clearInterval(heartbeatInterval.value);
  heartbeatInterval.value = window.setInterval(performHealthCheck, 10000);
}

/**
 * 停止心跳机制。
 */
function stopHeartbeat() {
  if (heartbeatInterval.value) {
    clearInterval(heartbeatInterval.value);
    heartbeatInterval.value = null;
  }
}

onMounted(startHeartbeat);
onUnmounted(stopHeartbeat);
</script>

<style scoped>
/* Styles remain the same */
.dashboard-panel {
  width: 100%;
  margin-bottom: 20px;
}
.mission-control {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(139, 92, 246, 0.05) 100%);
  border: 1px solid rgba(59, 130, 246, 0.1);
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}
.mission-control:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  border-color: rgba(59, 130, 246, 0.2);
}
.health-card,
.progress-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 0;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.card-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--n-text-color);
  display: flex;
  align-items: center;
  gap: 8px;
}
.title-icon {
  font-size: 20px;
  color: #3b82f6;
}
.connectivity-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  transition: all 0.3s ease;
}
.connectivity-dot.online {
  background: #10b981;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
  animation: pulse-online 2s infinite;
}
.connectivity-dot.offline {
  background: #ef4444;
  box-shadow: 0 0 8px rgba(239, 68, 68, 0.3);
}
@keyframes pulse-online {
  0%,
  100% {
    box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
  }
  50% {
    box-shadow: 0 0 16px rgba(16, 185, 129, 0.8);
  }
}
.health-content {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}
.metric-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.metric-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--n-text-color-2);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.metric-icon {
  font-size: 14px;
  color: #8b5cf6;
}
.metric-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--n-text-color);
  font-family: 'Monaco', 'Courier New', monospace;
  line-height: 1.2;
  word-break: break-all;
}
.metric-value.domain {
  font-size: 16px;
  color: #3b82f6;
  font-weight: 600;
}
.metric-value.latency {
  transition: color 0.3s ease;
}
.metric-value.latency.success {
  color: #10b981;
}
.metric-value.latency.warning {
  color: #f59e0b;
}
.metric-value.latency.error {
  color: #ef4444;
}
.model-tag {
  width: fit-content;
  font-weight: 600;
}
.progress-percentage {
  font-size: 24px;
  font-weight: 800;
  color: #3b82f6;
  font-family: 'Monaco', 'Courier New', monospace;
}
.progress-bar-container {
  margin: 12px 0;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-top: 8px;
}
.stat-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 12px;
  background: rgba(59, 130, 246, 0.05);
  border: 1px solid rgba(59, 130, 246, 0.1);
  border-radius: 8px;
  transition: all 0.3s ease;
}
.stat-box:hover {
  background: rgba(59, 130, 246, 0.1);
  border-color: rgba(59, 130, 246, 0.2);
}
.stat-box.sensitive {
  background: rgba(239, 68, 68, 0.05);
  border-color: rgba(239, 68, 68, 0.1);
}
.stat-box.sensitive:hover {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.2);
}
.stat-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--n-text-color-2);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}
.stat-value {
  font-size: 24px;
  font-weight: 800;
  color: var(--n-text-color);
  font-family: 'Monaco', 'Courier New', monospace;
  line-height: 1;
}
.stat-box.sensitive .stat-value {
  color: #ef4444;
}
:deep(.n-card) {
  background: var(--n-color);
}
@media (max-width: 768px) {
  .health-content {
    grid-template-columns: 1fr;
  }
  .stats-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  .card-title {
    font-size: 14px;
  }
  .metric-value {
    font-size: 16px;
  }
  .metric-value.domain {
    font-size: 14px;
  }
  .progress-percentage {
    font-size: 20px;
  }
  .stat-value {
    font-size: 20px;
  }
}
@media (max-width: 480px) {
  .health-content {
    grid-template-columns: 1fr;
  }
  .stats-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  .card-title {
    font-size: 13px;
  }
  .metric-value {
    font-size: 14px;
  }
  .metric-value.domain {
    font-size: 12px;
  }
  .progress-percentage {
    font-size: 18px;
  }
  .stat-value {
    font-size: 18px;
  }
  .stat-label {
    font-size: 10px;
  }
}
</style>
