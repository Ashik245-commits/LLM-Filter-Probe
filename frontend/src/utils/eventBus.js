/**
 * 一个简单的事件总线实现
 *
 * 提供一个全局的、轻量级的发布/订阅机制，用于在不同组件或模块之间解耦通信。
 * 这对于跨组件边界传递事件非常有用，例如，当一个深层嵌套的组件需要通知顶层应用某个状态变化时。
 */
const bus = {
  listeners: {},

  /**
   * 注册一个事件监听器
   * @param {string} event - 事件名称
   * @param {Function} callback - 事件触发时调用的回调函数
   */
  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  },

  /**
   * 注销一个事件监听器
   * @param {string} event - 事件名称
   * @param {Function} callback - 要注销的回调函数
   */
  off(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter((cb) => cb !== callback);
    }
  },

  /**
   * 触发一个事件
   * @param {string} event - 事件名称
   * @param  {...any} args - 传递给回调函数的参数
   */
  emit(event, ...args) {
    if (this.listeners[event]) {
      this.listeners[event].forEach((callback) => {
        try {
          callback(...args);
        } catch (e) {
          console.error(`Error in event bus listener for ${event}:`, e);
        }
      });
    }
  },
};

export default bus;
