"""
WebSocket 处理器 (WebSocket Handler) - 重构版

职责：
- 处理 WebSocket 连接的生命周期
- 解析来自客户端的消息
- 将扫描任务委托给 ScanService
- 将来自 ScanService 的实时事件转发给客户端
"""
import json
import logging
from typing import Dict, Any, Callable, Optional

from services.scan_service import ScanService

logger = logging.getLogger(__name__)

class WebSocketHandler:
    """处理 WebSocket 消息并与 ScanService 交互"""

    def __init__(self, session_id: str, scan_service: ScanService):
        """
        初始化处理器

        Args:
            session_id: 当前会话的 ID
            scan_service: 用于执行扫描任务的服务实例
        """
        self.session_id = session_id
        self.scan_service = scan_service
        self.is_scanning = False
        self.should_stop = False
        self.message_callback: Optional[Callable] = None

    async def set_message_callback(self, callback: Callable):
        """设置用于向客户端发送消息的回调函数"""
        self.message_callback = callback

    async def handle_message(self, message: str) -> bool:
        """
        处理来自客户端的单个消息

        Args:
            message: 原始消息字符串

        Returns:
            消息是否被成功处理
        """
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            await self._send_error("无效的 JSON 格式")
            return False

        message_type = data.get("type")
        message_data = data.get("data", {})

        # 处理停止扫描请求
        if message_type == "stop_scan":
            await self.scan_service.stop_scan()
            logger.info(f"[{self.session_id}] WebSocket received stop_scan request.")
            return True

        if self.is_scanning:
            await self._send_error("当前已有扫描任务在进行中，请等待其完成。")
            return False

        self.is_scanning = True
        try:
            if message_type == "scan_text":
                await self._handle_scan_text(message_data)
            else:
                await self._send_error(f"不支持的消息类型: '{message_type}'.")
            return True
        except Exception as e:
            logger.error(f"[{self.session_id}] 处理消息时发生错误: {e}", exc_info=True)
            await self._send_error(f"服务器内部错误: {e}")
            return False
        finally:
            self.is_scanning = False

    async def _handle_scan_text(self, data: Dict[str, Any]):
        """
        处理文本扫描请求
        """
        text = data.get("text")
        if not text:
            await self._send_error("请求中的 'text' 字段不能为空。")
            return

        logger.info(f"[{self.session_id}] WebSocket handler received scan_text request for {len(text)} chars.")
        
        # 确保 ScanService 已初始化并设置事件回调
        if not self.scan_service.is_initialized:
            await self.scan_service.initialize(event_callback=self._send_message)
        
        # 调用 ScanService 执行扫描，并将 _send_message 作为事件回调传递
        await self.scan_service.scan_text(text, self._send_message)

    async def _send_message(self, message: Dict[str, Any]):
        """
        通过回调将消息发送给客户端
        """
        if self.message_callback:
            try:
                await self.message_callback(message)
            except Exception as e:
                logger.error(f"[{self.session_id}] 发送 WebSocket 消息失败: {e}", exc_info=True)

    async def _send_error(self, error_message: str):
        """
        向客户端发送格式化的错误消息
        """
        await self._send_message({
            "event": "error",
            "message": error_message
        })
