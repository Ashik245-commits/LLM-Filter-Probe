"""
重试处理器 (Retry Handler)

职责：
- 管理重试逻辑
- 计算退避延迟
- 跟踪重试次数
"""
import asyncio
import logging
import random
from typing import Callable, Any, Optional
from ..presets import Preset
from ..constants import DEFAULT_ERROR_RECOVERY_MAX_BACKOFF

logger = logging.getLogger(__name__)


class RetryHandler:
    """重试处理器"""
    
    def __init__(self, preset: Preset, engine_id: str = ""):
        """
        初始化重试处理器
        
        Args:
            preset: 预设配置
            engine_id: 引擎 ID（用于日志追踪）
        """
        self.preset = preset
        self.engine_id = engine_id or "default"
        self.retry_count = 0
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        执行函数并在失败时重试
        
        Args:
            func: 要执行的异步函数
            *args: 位置参数
            **kwargs: 关键字参数
        
        Returns:
            函数的返回值
        
        Raises:
            Exception: 如果所有重试都失败
        """
        last_exception = None
        
        for attempt in range(self.preset.max_retries + 1):
            try:
                result = await func(*args, **kwargs)
                
                if attempt > 0:
                    logger.info(f"[{self.engine_id}] 重试成功 (第 {attempt} 次尝试)")
                
                return result
            
            except Exception as e:
                last_exception = e
                
                if attempt < self.preset.max_retries:
                    # 计算退避延迟
                    delay = self._calculate_backoff_delay(attempt)
                    logger.warning(
                        f"[{self.engine_id}] 尝试 {attempt + 1} 失败: {str(e)}, "
                        f"将在 {delay:.2f}s 后重试"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"[{self.engine_id}] 所有重试都失败 (共 {self.preset.max_retries} 次)"
                    )
        
        raise last_exception
    
    def _calculate_backoff_delay(self, attempt: int) -> float:
        """
        计算退避延迟
        
        使用指数退避 + 抖动 (Exponential Backoff with Jitter)
        
        Args:
            attempt: 当前尝试次数（从 0 开始）
        
        Returns:
            延迟时间（秒）
        """
        # 基础延迟：2^attempt
        base_delay = 2 ** attempt
        
        # 添加抖动：随机值在 [0, base_delay * jitter] 范围内
        jitter = random.uniform(0, base_delay * self.preset.jitter)
        
        total_delay = base_delay + jitter
        # 上限保护，避免指数退避过大
        if total_delay > DEFAULT_ERROR_RECOVERY_MAX_BACKOFF:
            total_delay = DEFAULT_ERROR_RECOVERY_MAX_BACKOFF
        
        return total_delay
    
    def reset(self):
        """重置重试计数"""
        self.retry_count = 0

