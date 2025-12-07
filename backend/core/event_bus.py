"""
事件总线 - 用于解耦各个组件之间的通信

职责：
  - 提供发布-订阅模式
  - 管理事件监听器
  - 分发事件到所有订阅者
  - 支持异步事件处理
"""
import asyncio
import logging
from typing import Callable, Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class EventBus:
    """
    事件总线 - 实现发布-订阅模式
    
    用法：
        # 创建事件总线
        bus = EventBus()
        
        # 订阅事件
        async def on_keyword_found(event):
            print(f"Found keyword: {event['keyword']}")
        
        bus.subscribe('keyword_found', on_keyword_found)
        
        # 发布事件
        await bus.emit('keyword_found', {'keyword': 'sensitive'})
    """

    def __init__(self):
        """初始化事件总线"""
        self._listeners: Dict[str, List[Callable]] = {}
        self._lock = asyncio.Lock()
        logger.info("[EventBus] 事件总线已初始化")

    def subscribe(self, event_type: str, handler: Callable) -> Callable:
        """
        订阅事件

        Args:
            event_type: 事件类型
            handler: 事件处理器（可以是同步或异步函数）
        
        Returns:
            取消订阅的函数
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        
        self._listeners[event_type].append(handler)
        logger.debug(f"[EventBus] 已订阅事件: {event_type} (共 {len(self._listeners[event_type])} 个监听器)")
        
        # 返回取消订阅函数
        def unsubscribe():
            if handler in self._listeners.get(event_type, []):
                self._listeners[event_type].remove(handler)
                logger.debug(f"[EventBus] 已取消订阅事件: {event_type}")
        
        return unsubscribe
    
    def unsubscribe(self, event_type: str, handler: Callable) -> bool:
        """
        取消订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
        
        Returns:
            是否成功取消订阅
        """
        if event_type in self._listeners and handler in self._listeners[event_type]:
            self._listeners[event_type].remove(handler)
            logger.debug(f"[EventBus] 已取消订阅事件: {event_type}")
            return True
        return False
    
    async def emit(self, event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        发布事件

        Args:
            event_type: 事件类型
            data: 事件数据
        """
        if event_type not in self._listeners:
            logger.debug(f"[EventBus] 事件 {event_type} 没有监听器")
            return
        
        handlers = self._listeners[event_type].copy()
        logger.debug(f"[EventBus] 发布事件: {event_type} (有 {len(handlers)} 个监听器)")
        
        # 并发执行所有处理器
        tasks = []
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    tasks.append(handler(data or {}))
                else:
                    # 同步函数在线程池中执行
                    loop = asyncio.get_event_loop()
                    tasks.append(loop.run_in_executor(None, handler, data or {}))
            except Exception as e:
                logger.error(f"[EventBus] 执行事件处理器失败: {e}", exc_info=True)
        
        if tasks:
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except Exception as e:
                logger.error(f"[EventBus] 事件处理失败: {e}", exc_info=True)
    
    def clear(self, event_type: Optional[str] = None) -> None:
        """
        清空事件监听器

        Args:
            event_type: 事件类型，如果为 None 则清空所有
        """
        if event_type is None:
            self._listeners.clear()
            logger.info("[EventBus] 已清空所有事件监听器")
        else:
            if event_type in self._listeners:
                self._listeners[event_type].clear()
                logger.debug(f"[EventBus] 已清空事件监听器: {event_type}")
    
    def get_listener_count(self, event_type: str) -> int:
        """
        获取特定事件的监听器数量
        
        Args:
            event_type: 事件类型
        
        Returns:
            监听器数量
        """
        return len(self._listeners.get(event_type, []))
    
    def get_all_event_types(self) -> List[str]:
        """
        获取所有已注册的事件类型
        
        Returns:
            事件类型列表
        """
        return list(self._listeners.keys())


# 全局事件总线实例
_global_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """获取全局事件总线实例"""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


def create_event_bus() -> EventBus:
    """创建新的事件总线实例"""
    return EventBus()


# 标准事件类型定义
class EventTypes:
    """标准事件类型常量"""
    
    # 扫描事件
    SCAN_STARTED = "scan_started"
    SCAN_COMPLETED = "scan_completed"
    SCAN_CANCELLED = "scan_cancelled"
    SCAN_ERROR = "scan_error"
    
    # 关键词事件
    KEYWORD_FOUND = "keyword_found"
    KEYWORD_MASKED = "keyword_masked"
    
    # 进度事件
    PROGRESS_UPDATED = "progress_updated"
    SEGMENT_PROCESSED = "segment_processed"
    
    # 日志事件
    LOG_MESSAGE = "log_message"
    ERROR_OCCURRED = "error_occurred"
    WARNING_OCCURRED = "warning_occurred"
    
    # 配置事件
    CONFIG_UPDATED = "config_updated"
    CONFIG_LOADED = "config_loaded"
    
    # 连接事件
    CONNECTION_ESTABLISHED = "connection_established"
    CONNECTION_LOST = "connection_lost"
    CONNECTION_ERROR = "connection_error"
