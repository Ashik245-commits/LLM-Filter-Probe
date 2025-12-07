import { computed } from 'vue';
import { useRootStore } from '../stores/rootStore';

/**
 * @description A simplified Vue Composition API composable for controlling the text scanner UI.
 *
 * This composable acts as a bridge between the UI components and the central Pinia store.
 * It no longer manages WebSocket connections directly. All state and actions are delegated
 * to the rootStore, which is the single source of truth.
 *
 * @returns {object} An object containing reactive state and methods to control the scanner UI.
 */
export function useTextScanner() {
  const rootStore = useRootStore();

  // --- Computed Properties (delegated to the store) ---

  const isScanning = computed(() => rootStore.scanState.isScanning);

  const isScanDisabled = computed(() => {
    return (
      rootStore.system.connectionStatus !== 'online' ||
      !rootStore.system.sessionId ||
      rootStore.scanState.isScanning
    );
  });

  const tooltipText = computed(() => {
    if (rootStore.system.connectionStatus !== 'online') {
      return '❌ 连接已断开。请检查后端服务或刷新页面。';
    }
    if (!rootStore.system.sessionId) {
      return '❌ 会话未创建。正在等待会话初始化...';
    }
    if (rootStore.scanState.isScanning) {
      return '⏳ 扫描进行中...';
    }
    return '✅ 准备就绪';
  });

  // --- Scan Control Methods (delegated to the store) ---

  /**
   * @description Starts the scanning process by calling the store action.
   * @param {string} inputText - The text to be scanned.
   */
  const startScan = (inputText) => {
    if (isScanDisabled.value || !inputText) return;

    // The store will handle the logic of sending the message via WebSocket
    rootStore.sendScanRequest(inputText);
  };

  /**
   * @description Requests to stop the current scan by calling the store action.
   */
  const stopScan = async () => {
    await rootStore.cancelScan();
  };

  return {
    isScanning,
    isScanDisabled,
    tooltipText,
    startScan,
    stopScan,
  };
}
