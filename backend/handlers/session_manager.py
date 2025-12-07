"""
会话管理器 (Session Manager) - 重构版

职责：
- 创建和销毁扫描会话 (ScanSession)
- 为每个会话初始化 ScanService
- 管理会话的生命周期
"""
import uuid
import logging
from typing import Dict, Optional
from datetime import datetime

from core.presets import Preset
from core.config_manager import get_config_manager
from core.config_normalizer import ConfigNormalizer
from services.scan_service import ScanService
from handlers.websocket_handler import WebSocketHandler

logger = logging.getLogger(__name__)

class ScanSession:
    """代表一个独立的扫描会话"""

    def __init__(self, session_id: str, preset: Preset):
        self.session_id = session_id
        self.preset = preset
        self.created_at = datetime.now()
        self.scan_service: Optional[ScanService] = None
        self.websocket_handler: Optional[WebSocketHandler] = None

    async def initialize(self, event_callback=None):
        """
        初始化会话所需的服务
        
        Args:
            event_callback: 可选的事件回调函数，用于推送实时事件
        """
        try:
            logger.info(f"[{self.session_id}] Initializing session with preset '{self.preset.name}'.")
            self.scan_service = ScanService(preset=self.preset, session_id=self.session_id)
            await self.scan_service.initialize(event_callback=event_callback)

            self.websocket_handler = WebSocketHandler(session_id=self.session_id, scan_service=self.scan_service)
            logger.info(f"[{self.session_id}] Session initialized successfully.")
        except Exception as e:
            logger.error(f"[{self.session_id}] Session initialization failed: {e}", exc_info=True)
            await self.close()
            raise

    async def close(self):
        """清理会话资源"""
        if self.scan_service:
            await self.scan_service.cleanup()
        logger.info(f"[{self.session_id}] Session closed.")

    def get_info(self) -> Dict:
        """获取会话的基本信息"""
        return {
            "session_id": self.session_id,
            "preset_name": self.preset.name,
            "created_at": self.created_at.isoformat(),
            "uptime": (datetime.now() - self.created_at).total_seconds(),
        }

class SessionManager:
    """管理所有活动的 ScanSession"""

    def __init__(self):
        self.sessions: Dict[str, ScanSession] = {}
        self.config_manager = get_config_manager()

    async def create_session(self, runtime_overrides: Optional[Dict] = None) -> str:
        """
        创建一个新的扫描会话

        Args:
            runtime_overrides: 来自 API 请求的运行时配置覆盖

        Returns:
            新的会话 ID
        """
        session_id = str(uuid.uuid4())
        logger.info(f"[{session_id}] Creating new session...")

        try:
            # 加载配置，应用运行时覆盖
            final_config = await self.config_manager.load(runtime_overrides)
            
            # 规范化配置字段（统一处理别名和类型转换）
            final_config = ConfigNormalizer.normalize(final_config, session_id)
            
            # 验证必需字段
            if not ConfigNormalizer.validate_preset_fields(final_config, session_id):
                raise ValueError("配置缺少必需字段")
            
            logger.debug(f"[{session_id}] 配置规范化完成")
            logger.debug(f"[{session_id}] 配置字段映射信息: {ConfigNormalizer.get_field_mapping_info()}")
            
            preset = Preset(**final_config)

            session = ScanSession(session_id=session_id, preset=preset)
            await session.initialize()

            self.sessions[session_id] = session
            logger.info(f"[{session_id}] Session created successfully. Total sessions: {len(self.sessions)}.")
            return session_id
        except Exception as e:
            logger.error(f"[{session_id}] Failed to create session: {e}", exc_info=True)
            raise

    async def delete_session(self, session_id: str):
        """删除一个会话并清理其资源"""
        session = self.sessions.pop(session_id, None)
        if session:
            await session.close()
            logger.info(f"[{session_id}] Session deleted. Total sessions: {len(self.sessions)}.")
        else:
            logger.warning(f"Attempted to delete non-existent session: {session_id}")

    def get_session(self, session_id: str) -> Optional[ScanSession]:
        """通过 ID 获取一个活动的会话"""
        return self.sessions.get(session_id)

    def list_sessions(self) -> Dict[str, Dict]:
        """列出所有活动会话的信息"""
        return {sid: sess.get_info() for sid, sess in self.sessions.items()}

    async def cleanup(self):
        """清理所有会话"""
        logger.info(f"Cleaning up all {len(self.sessions)} sessions...")
        for session_id in list(self.sessions.keys()):
            await self.delete_session(session_id)
        logger.info("All sessions cleaned up.")

# 全局单例管理器
_session_manager: Optional[SessionManager] = None

def get_session_manager() -> SessionManager:
    """获取全局 SessionManager 单例"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
