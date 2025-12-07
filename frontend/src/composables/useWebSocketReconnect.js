import { ref, reactive, onUnmounted } from 'vue';

/**
 * 带自动重连功能的 WebSocket Hook
 *
 * @param {string} url WebSocket URL
 * @param {object} options 配置选项
 * @returns {object} WebSocket 实例、连接状态、发送方法等
 */
export function useWebSocketReconnect(url, options = {}) {
  const {
    maxRetries = 5, // 最大重连次数
    initialDelay = 1000, // 初始延迟 (ms)
    maxDelay = 30000, // 最大延迟 (ms)
    backoffMultiplier = 2, // 指数退避乘数
    connectionTimeout = 10000, // 连接超时 (ms)，默认 10 秒
    onMessage = () => {},
    onError = () => {},
    onOpen = () => {},
    onClose = () => {},
  } = options;

  const ws = ref(null);
  const isConnected = ref(false);
  const reconnectAttempt = ref(0);
  const reconnectTimer = ref(null);
  const connectionTimeoutTimer = ref(null);

  const state = reactive({
    status: 'disconnected', // 'connected', 'disconnected', 'reconnecting', 'failed'
    lastError: null,
    reconnectIn: 0, // 重连倒计时 (秒)
  });

  /**
   * 计算下一次重连的延迟时间 (指数退避 + 随机抖动)
   */
  const calculateDelay = () => {
    const delay = Math.min(
      initialDelay * Math.pow(backoffMultiplier, reconnectAttempt.value),
      maxDelay
    );
    return delay + Math.random() * 1000; // 添加随机抖动，避免雷鸣羊群效应
  };

  /**
   * 连接 WebSocket
   */
  const connect = () => {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      console.log('ℹ️ WebSocket 已连接');
      return Promise.resolve();
    }

    return new Promise((resolve, reject) => {
      try {
        console.log(`🔌 正在连接到 ${url}... (超时: ${connectionTimeout}ms)`);
        ws.value = new WebSocket(url);

        // 设置连接超时
        connectionTimeoutTimer.value = setTimeout(() => {
          console.error(`❌ WebSocket 连接超时 (${connectionTimeout}ms)`);
          if (ws.value && ws.value.readyState !== WebSocket.OPEN) {
            ws.value.close();
            reject(new Error(`WebSocket 连接超时 (${connectionTimeout}ms)`));
          }
        }, connectionTimeout);

        ws.value.onopen = (event) => {
          // 清除超时定时器
          if (connectionTimeoutTimer.value) {
            clearTimeout(connectionTimeoutTimer.value);
            connectionTimeoutTimer.value = null;
          }
          console.log('✅ WebSocket 连接成功');
          isConnected.value = true;
          state.status = 'connected';
          reconnectAttempt.value = 0;
          onOpen(event);
          resolve();
        };

        ws.value.onmessage = onMessage;

        ws.value.onerror = (error) => {
          // 清除超时定时器
          if (connectionTimeoutTimer.value) {
            clearTimeout(connectionTimeoutTimer.value);
            connectionTimeoutTimer.value = null;
          }
          console.error('❌ WebSocket 错误:', error);
          state.lastError = error;
          onError(error);
          reject(error);
        };

        ws.value.onclose = (event) => {
          // 清除超时定时器
          if (connectionTimeoutTimer.value) {
            clearTimeout(connectionTimeoutTimer.value);
            connectionTimeoutTimer.value = null;
          }
          console.log(`🔌 WebSocket 连接关闭 (Code: ${event.code})`);
          isConnected.value = false;
          state.status = 'disconnected';
          onClose(event);

          // 1000 是正常关闭，不应重连
          if (event.code !== 1000 && reconnectAttempt.value < maxRetries) {
            attemptReconnect();
          } else if (reconnectAttempt.value >= maxRetries) {
            console.error('❌ 达到最大重连次数，放弃重连');
            state.status = 'failed';
          }
        };
      } catch (error) {
        // 清除超时定时器
        if (connectionTimeoutTimer.value) {
          clearTimeout(connectionTimeoutTimer.value);
          connectionTimeoutTimer.value = null;
        }
        console.error('❌ WebSocket 连接异常:', error);
        reject(error);
      }
    });
  };

  /**
   * 尝试重新连接
   */
  const attemptReconnect = () => {
    if (reconnectTimer.value) {
      clearTimeout(reconnectTimer.value);
    }

    reconnectAttempt.value++;
    const delay = calculateDelay();

    console.log(
      `⏳ ${reconnectAttempt.value}/${maxRetries} 将在 ${Math.ceil(delay / 1000)}s 后重新连接...`
    );
    state.status = 'reconnecting';
    state.reconnectIn = Math.ceil(delay / 1000);

    const countdownInterval = setInterval(() => {
      state.reconnectIn--;
      if (state.reconnectIn <= 0) {
        clearInterval(countdownInterval);
      }
    }, 1000);

    reconnectTimer.value = setTimeout(() => {
      connect().catch(() => {
        // 连接失败，将在 onclose 中再次尝试
      });
    }, delay);
  };

  /**
   * 手动断开连接
   */
  const disconnect = () => {
    if (reconnectTimer.value) {
      clearTimeout(reconnectTimer.value);
    }
    if (connectionTimeoutTimer.value) {
      clearTimeout(connectionTimeoutTimer.value);
      connectionTimeoutTimer.value = null;
    }
    if (ws.value) {
      console.log('🚪 手动断开 WebSocket 连接');
      // 设置一个标志，防止 onclose 触发重连
      reconnectAttempt.value = maxRetries;
      ws.value.close(1000, 'Manual disconnection');
    }
  };

  /**
   * 发送数据
   */
  const send = (data) => {
    if (isConnected.value && ws.value) {
      ws.value.send(JSON.stringify(data));
    } else {
      console.warn('⚠️ WebSocket 未连接，无法发送数据');
    }
  };

  // 在组件卸载时清理资源
  onUnmounted(() => {
    disconnect();
  });

  return {
    ws,
    isConnected,
    state,
    connect,
    disconnect,
    send,
    reconnectAttempt,
  };
}
