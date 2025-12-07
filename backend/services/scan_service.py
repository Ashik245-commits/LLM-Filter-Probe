"""
扫描服务层 (Scan Service)

本模块定义了 `ScanService`，这是一个高级服务类，作为文本扫描功能的主要入口点。
它负责协调底层的探测引擎 (`ProbeEngine`) 和文本扫描器 (`TextScanner`)，
为上层应用（如 API 路由）提供一个简洁、统一的接口来执行扫描、验证凭证和管理扫描生命周期。
"""
import logging
from typing import List, Callable, Dict, Any, Optional

from core.engine.probe_engine import ProbeEngine
from core.scanner import TextScanner, SensitiveSegment
from core.presets import Preset
from utils.http_client import AsyncHttpClient

logger = logging.getLogger(__name__)

async def get_scan_service() -> "ScanService":
    """
    FastAPI 依赖项工厂函数。

    在某些不需要完整会话的场景下（例如，在保存配置前进行 API 凭证验证），
    此函数会创建一个临时的、轻量级的 `ScanService` 实例。
    这样可以复用服务中的独立逻辑（如 `verify_credentials`），而无需创建完整的用户会话。

    Returns:
        一个用于执行独立操作的 ScanService 实例。
    """
    # 最小可用的 Preset（仅需 name，其余字段有默认值）
    preset = Preset(name="verify")
    return ScanService(preset=preset, session_id="verify")

class ScanService:
    """
    封装了完整扫描流程的高级服务。
    """

    def __init__(self, preset: Preset, session_id: str):
        """
        初始化扫描服务

        Args:
            preset: 包含所有配置的预设对象
            session_id: 当前会话的 ID，用于日志和追踪
        """
        self.session_id = session_id
        self.preset = preset
        self.engine: ProbeEngine = None
        self.scanner: TextScanner = None
        self.is_initialized = False

        logger.info(f"[{self.session_id}] ScanService created for preset '{preset.name}'.")

    async def initialize(self, event_callback: Optional[Callable] = None):
        """
        初始化底层的 ProbeEngine 和 TextScanner。
        
        Args:
            event_callback: 可选的事件回调函数，用于推送实时事件
        """
        if self.is_initialized:
            return

        try:
            logger.info(f"[{self.session_id}] Initializing ScanService...")
            self.engine = ProbeEngine(preset=self.preset, engine_id=self.session_id)
            await self.engine.initialize()
            
            self.scanner = TextScanner(engine=self.engine, session_id=self.session_id)
            
            # 将 scanner 的 event_emitter 传递给 engine
            if self.scanner.emitter:
                await self.engine.set_event_emitter(self.scanner.emitter)

            # 如果提供了外部的 event_callback，也设置它（用于日志等）
            if event_callback:
                await self.scanner.emitter.set_callback(event_callback)
            self.is_initialized = True
            logger.info(f"[{self.session_id}] ScanService initialized successfully.")
        except Exception as e:
            logger.error(f"[{self.session_id}] Failed to initialize ScanService: {e}", exc_info=True)
            # 在失败时进行清理
            await self.cleanup()
            raise

    async def _reload_config_and_reinitialize(self, event_callback: Optional[Callable] = None):
        """在每次扫描前重新加载配置并重新初始化服务。"""
        from core.config_manager import get_config_manager
        from core.config_normalizer import ConfigNormalizer

        logger.info(f"[{self.session_id}] Reloading configuration for new scan...")
        config_manager = get_config_manager()
        latest_config = await config_manager.load()
        
        # 规范化配置
        normalized_config = ConfigNormalizer.normalize(latest_config, self.session_id)
        if not ConfigNormalizer.validate_preset_fields(normalized_config, self.session_id):
            raise ValueError("重新加载的配置缺少必需字段")

        # 使用最新的、规范化的配置更新 self.preset
        self.preset = Preset(**normalized_config)

        # 重新初始化引擎和扫描器
        # 注意：initialize 方法会使用更新后的 self.preset
        await self.initialize(event_callback=event_callback)

        # 直接从完整的配置字典中获取 API 信息用于日志记录
        api_url = normalized_config.get('api_url', '(未配置)')
        api_key = normalized_config.get('api_key', '')
        api_model = normalized_config.get('model', '(未配置)')
        masked_key = f"{api_key[:4]}...{api_key[-4:]}" if api_key and len(api_key) > 8 else "(未提供或过短)"
        
        if self.scanner and self.scanner.emitter:
            await self.scanner.emitter.log_message(
                "info",
                f"▶️ 当前扫描配置 | API 地址: {api_url} | 模型: {api_model} | 密钥: {masked_key}"
            )

    async def scan_text(self, text: str, event_callback: Callable) -> List[SensitiveSegment]:
        """
        执行文本扫描

        Args:
            text: 待扫描的文本
            event_callback: 用于接收实时事件（如进度、日志）的异步回调函数
            stop_flag: 停止标志的引用，用于中止扫描

        Returns:
            一个包含所有已发现敏感片段的列表
        """
        # 在每次扫描开始时，都强制重新加载配置
        await self._reload_config_and_reinitialize(event_callback)

        # 确保在每次扫描时，都将最新的回调设置给 emitter
        if event_callback and self.scanner:
            await self.scanner.emitter.set_callback(event_callback)

        logger.info(f"[{self.session_id}] Starting text scan of length {len(text)}.")
        
        # 重置扫描器的停止标志
        if self.scanner:
            self.scanner.should_stop = False
        
        # 将事件回调连接到扫描器
        await self.scanner.set_log_callback(event_callback)
        
        # 将底层引擎的事件回调统一导向扫描器的事件发射器。
        # 这样做可以确保所有来自底层的事件（如 API 错误、网络问题等）
        # 都能被标准化处理，并以统一的格式（如 'log' 事件）发送给前端。
        if self.engine:
            try:
                await self.engine.set_event_callback(self.scanner.emitter._emit)
            except Exception:
                # 在极少数情况下，如果回调设置失败，保留现有回调以确保稳定性。
                pass

        try:
            results = await self.scanner.scan(text)
            logger.info(f"[{self.session_id}] Text scan completed. Found {len(results)} sensitive segments.")
            return results
        except Exception as e:
            logger.error(f"[{self.session_id}] An error occurred during text scan: {e}", exc_info=True)
            # 向客户端发送错误事件
            await event_callback({
                "event": "error",
                "message": f"扫描过程中发生内部错误: {e}"
            })
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取扫描过程的统计数据
        """
        if not self.scanner:
            return {}
        return self.scanner.get_statistics()

    async def stop_scan(self):
        """优雅地停止当前正在进行的扫描。"""
        if self.scanner:
            logger.info(f"[{self.session_id}] 收到停止扫描的请求。")
            self.scanner.should_stop = True

    async def cleanup(self):
        """
        清理并释放资源，如关闭 HTTP 客户端。
        """
        if self.engine:
            await self.engine.cleanup()
        self.is_initialized = False
        logger.info(f"[{self.session_id}] ScanService cleaned up.")

    async def verify_credentials(self, api_url: str, api_key: str, model: str) -> Dict[str, Any]:
        """
        验证提供的 API 凭证（URL、密钥、模型）是否有效。

        此方法会向目标 API 的 `/chat/completions` 端点发送一个最小化的测试请求。
        它不执行任何实际的扫描，仅用于确认网络连接、API 密钥和模型名称是否正确，
        以便在用户保存配置前提供即时反馈。

        Args:
            api_url: 待验证的 API 地址。
            api_key: 待验证的 API 密钥。
            model: 待验证的模型名称。

        Returns:
            一个包含验证结果的字典，格式为:
            {
                "ok": bool,      # 凭证是否有效
                "status": int,   # HTTP 状态码
                "response": Any  # 来自 API 的原始响应体
            }
        """
        target = api_url.rstrip('/') + '/chat/completions'
        payload = {
            "model": (model or '').strip(),
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 10,
            "stream": False
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        logger.info(f"[Verify] Verification Target: {target}")
        logger.info(f"[Verify] Verification Payload: {payload}")
        # 使用系统代理默认值，由 http_client 读取常量
        async with AsyncHttpClient() as http:
            status, resp_json, _rid = await http.post(target, json_data=payload, headers=headers)
        ok = (status == 200)
        return {
            "ok": ok,
            "status": status,
            "response": resp_json
        }

