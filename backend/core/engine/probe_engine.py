"""
核心探针引擎 (Probe Engine)

职责：
- 协调请求构建、响应分析、重试处理
- 管理 HTTP 客户端生命周期
- 提供统一的探测接口
"""
import asyncio
import logging
import json
import random
from typing import Dict, Any, Optional, List, Set

# 动态导入 ScanEventEmitter 以避免循环依赖
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..scanner.event_emitter import ScanEventEmitter

from ..presets import Preset
from utils.http_client import AsyncHttpClient
from .request_builder import RequestBuilder
from .response_analyzer import ResponseAnalyzer, ScanStatus, ProbeResult
from .retry_handler import RetryHandler
from ..constants import DEFAULT_ERROR_RECOVERY_MAX_BACKOFF

logger = logging.getLogger(__name__)


class ProbeEngine:
    """
    核心探针引擎，负责与外部 API 进行所有交互。

    核心逻辑：
    - **SAFE**: API 响应成功（例如，HTTP 状态码 200 OK）。
    - **BLOCKED**: API 响应表明请求被拦截。这基于以下任一条件：
        1. 响应的 HTTP 状态码在 `block_status_codes` 列表中。
        2. 响应体内容包含 `block_keywords` 列表中的任何关键字。
    - **RETRY**: API 响应表明这是一个临时性错误，应进行重试（例如，HTTP 状态码 429 或 502）。
    """

    def __init__(self, preset: Preset, engine_id: str = ""):
        """
        初始化探针引擎

        Args:
            preset: 预设配置
            engine_id: 引擎 ID（用于日志追踪）
        """
        self.preset = preset
        self.engine_id = engine_id or "default"

        # 初始化子模块
        self.request_builder = RequestBuilder(preset, engine_id)
        self.response_analyzer = ResponseAnalyzer(preset, engine_id)
        self.retry_handler = RetryHandler(preset, engine_id)

        # HTTP 客户端
        self.http_client: Optional[AsyncHttpClient] = None

        # 统计数据
        self.request_count = 0
        self.blocked_count = 0
        self.safe_count = 0
        self.error_count = 0
        self.unknown_status_codes: Set[int] = set()
        self.reported_unknown_codes: Set[int] = set()  # 跟踪已报告的未知状态码，避免重复推送

        # 事件发射器和回调
        self.event_emitter: Optional['ScanEventEmitter'] = None
        self.event_callback = None
        self.mask_patterns: Set[str] = set()

        logger.info(
            f"[{self.engine_id}] 探针引擎已初始化 | "
            f"preset={preset.name} | concurrency={preset.concurrency} | timeout={preset.timeout}s"
        )

    async def set_event_emitter(self, emitter: 'ScanEventEmitter'):
        """
        设置事件发射器实例。
        为实现解耦，引擎不直接调用发射器的方法，而是通过一个通用的回调接口。
        """
        self.event_emitter = emitter
        if emitter:
            self.event_callback = emitter._emit
        logger.info(f"[{self.engine_id}] 事件发射器已设置")

    def set_mask_patterns(self, patterns: Set[str]):
        """设置用于在探测前屏蔽已知敏感词的正则表达式模式。"""
        self.mask_patterns = patterns

    async def initialize(self):
        """初始化 HTTP 客户端"""
        if self.http_client is None:
            self.http_client = AsyncHttpClient(
                timeout=self.preset.timeout,
                max_retries=self.preset.max_retries,
                keep_alive=True,
                max_keepalive_connections=self.preset.concurrency,
                max_connections=self.preset.concurrency,
                use_system_proxy=self.preset.use_system_proxy
            )
            await self.http_client.connect()
            logger.info(f"[{self.engine_id}] HTTP 客户端已初始化")

    async def cleanup(self):
        """清理资源"""
        if self.http_client:
            await self.http_client.close()
            self.http_client = None
            logger.info(f"[{self.engine_id}] HTTP 客户端已关闭")

    def _mask_text(self, text: str) -> str:
        """使用已知的敏感词模式屏蔽文本。"""
        if not self.mask_patterns:
            return text
        
        masked_text = text
        for pattern in self.mask_patterns:
            masked_text = masked_text.replace(pattern, "[MASK]")
        return masked_text

    async def probe(self, text_segment: str) -> ProbeResult:
        """
        探测文本片段

        Args:
            text_segment: 文本片段

        Returns:
            ProbeResult 对象
        """
        if not self.http_client:
            await self.initialize()

        # 在探测前应用动态屏蔽
        masked_segment = self._mask_text(text_segment)
        if not masked_segment.strip():
            return ProbeResult(ScanStatus.MASKED, 200, "")

        self.request_count += 1

        try:
            url, request_body = self.request_builder.build(masked_segment)
        except Exception as e:
            logger.error(f"[{self.engine_id}] 构建请求失败: {str(e)}")
            self.error_count += 1
            return ProbeResult(ScanStatus.ERROR, 0, str(e))

        headers = {
            "Authorization": f"Bearer {self.preset.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Connection": "keep-alive",
        }

        for attempt in range(self.preset.max_retries):
            try:
                text_hash = hash(text_segment) & 0xffff
                logger.debug(
                    f"[{self.engine_id}] 正在探测 | 长度: {len(text_segment)} | "
                    f"Hash: {text_hash:04x} | 尝试: {attempt + 1}/{self.preset.max_retries}"
                )
                logger.debug(f"[{self.engine_id}] 请求体: {json.dumps(request_body, ensure_ascii=False)[:500]}")

                status_code, response_json, request_id = await self.http_client.post(
                    url,
                    request_body,
                    headers=headers
                )

                response_text = json.dumps(response_json, ensure_ascii=False)
                logger.info(
                    f"[{self.engine_id}] 响应接收 | 状态码: {status_code} | "
                    f"大小: {len(response_text)} 字节 | 长度: {len(text_segment)} | RequestID: {request_id}"
                )
                logger.debug(f"[{self.engine_id}] 响应体: {response_text[:500]}")

                if status_code in self.preset.retry_status_codes:
                    if attempt < self.preset.max_retries - 1:
                        base_backoff = 2 ** attempt
                        jitter = random.uniform(0, self.preset.jitter)
                        backoff = base_backoff + jitter
                        if backoff > DEFAULT_ERROR_RECOVERY_MAX_BACKOFF:
                            backoff = DEFAULT_ERROR_RECOVERY_MAX_BACKOFF
                        logger.warning(
                            f"[{self.engine_id}] 收到重试状态码 {status_code}，"
                            f"等待 {backoff:.2f}s 后重试... (尝试 {attempt + 1}/{self.preset.max_retries})"
                        )
                        await asyncio.sleep(backoff)
                        continue
                    else:
                        logger.error(f"[{self.engine_id}] 重试次数已用尽，状态码: {status_code}")
                        self.error_count += 1
                        return ProbeResult(ScanStatus.ERROR, status_code, response_text)

                result = self.response_analyzer.analyze(status_code, response_text)

                if result.status == ScanStatus.BLOCKED:
                    logger.error(
                        f"[{self.engine_id}] 触发阻断 | 状态码: {status_code} | "
                        f"原因: {result.block_reason} | 响应体: {response_text[:1000]}"
                    )

                if result.is_unknown_error_code:
                    self.unknown_status_codes.add(status_code)
                    logger.warning(
                        f"[{self.engine_id}] 检测到未知的错误状态码: {status_code} | "
                        f"响应体: {response_text[:200]}"
                    )
                    if status_code not in self.reported_unknown_codes:
                        self.reported_unknown_codes.add(status_code)
                        if self.event_emitter:
                            try:
                                await self.event_emitter.unknown_status_code_found(status_code, response_text)
                            except Exception as e:
                                logger.error(f"[{self.engine_id}] 推送未知状态码事件失败: {e}", exc_info=True)

                if result.status == ScanStatus.BLOCKED:
                    self.blocked_count += 1
                elif result.status == ScanStatus.SAFE:
                    self.safe_count += 1
                elif result.status == ScanStatus.ERROR and status_code not in self.unknown_status_codes:
                    self.error_count += 1

                return result

            except asyncio.TimeoutError:
                logger.error(f"[{self.engine_id}] 请求超时 (尝试 {attempt + 1}/{self.preset.max_retries})")
                if attempt < self.preset.max_retries - 1:
                    backoff = 2 ** attempt + random.uniform(0, self.preset.jitter)
                    await asyncio.sleep(backoff)
                    continue
                else:
                    self.error_count += 1
                    return ProbeResult(ScanStatus.ERROR, 0, "Request Timeout")

            except Exception as e:
                logger.error(f"[{self.engine_id}] 请求异常 (尝试 {attempt + 1}/{self.preset.max_retries}): {str(e)}")
                if attempt < self.preset.max_retries - 1:
                    backoff = 2 ** attempt + random.uniform(0, self.preset.jitter)
                    await asyncio.sleep(backoff)
                    continue
                else:
                    self.error_count += 1
                    return ProbeResult(ScanStatus.ERROR, 0, str(e))

        self.error_count += 1
        return ProbeResult(ScanStatus.ERROR, 0, "Max Retries Exceeded")

    async def probe_batch(self, texts: List[str]) -> List[ProbeResult]:
        """
        批量探测文本片段

        Args:
            texts: 文本片段列表

        Returns:
            ProbeResult 对象列表
        """
        if not texts:
            return []

        logger.info(f"[{self.engine_id}] 开始批量探测 | 文本数: {len(texts)}")
        tasks = [self.probe(text) for text in texts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"[{self.engine_id}] 批量探测异常: {str(result)}")
                processed_results.append(ProbeResult(ScanStatus.ERROR, 0, str(result)))
            else:
                processed_results.append(result)

        logger.info(
            f"[{self.engine_id}] 批量探测完成 | "
            f"总数: {len(texts)} | "
            f"安全: {sum(1 for r in processed_results if r.status == ScanStatus.SAFE)} | "
            f"阻止: {sum(1 for r in processed_results if r.status == ScanStatus.BLOCKED)} | "
            f"错误: {sum(1 for r in processed_results if r.status == ScanStatus.ERROR)}"
        )

        return processed_results

    def reset_masking(self):
        """重置动态掩码，清除所有已知的敏感词模式。"""
        self.mask_patterns = set()
        if self.response_analyzer:
            # 【修复】直接更新属性，而不是调用不存在的方法
            self.response_analyzer.mask_patterns = self.mask_patterns
        logger.info(f"[{self.engine_id}] 动态掩码已重置.")

    def reset_masking(self):
        """重置动态掩码，清除所有已知的敏感词模式。"""
        self.mask_patterns = set()
        if self.response_analyzer:
            self.response_analyzer.mask_patterns = self.mask_patterns
        logger.info(f"[{self.engine_id}] 动态掩码已重置.")

    def reset_statistics(self):
        """重置引擎的统计数据，确保每次扫描的计数都是独立的。"""
        self.request_count = 0
        self.blocked_count = 0
        self.safe_count = 0
        self.error_count = 0
        logger.info(f"[{self.engine_id}] 引擎统计数据已重置.")

    def get_statistics(self) -> Dict[str, int]:
        """获取统计数据"""
        return {
            "request_count": self.request_count,
            "blocked_count": self.blocked_count,
            "safe_count": self.safe_count,
            "error_count": self.error_count
        }
