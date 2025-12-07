"""
异步 HTTP 客户端 (AsyncHttpClient)

封装 httpx，提供一个可复用的、高性能的异步 HTTP 客户端，
并统一处理超时、重试、keep-alive、代理和日志记录等功能。
"""
import httpx
import asyncio
import time
import json as json_module
from typing import Dict, Any, Optional, Tuple
import uuid
import logging

logger = logging.getLogger(__name__)

# 导入常量，如果失败则使用备用值
try:
    from core.constants import (
        DEFAULT_TIMEOUT_SECONDS,
        DEFAULT_HTTP_KEEP_ALIVE,
        DEFAULT_HTTP_VERIFY_SSL,
        DEFAULT_HTTP_MAX_KEEPALIVE_CONNECTIONS,
        DEFAULT_HTTP_MAX_CONNECTIONS,
        DEFAULT_USE_SYSTEM_PROXY,
    )
except ImportError:
    DEFAULT_TIMEOUT_SECONDS = 20
    DEFAULT_HTTP_KEEP_ALIVE = True
    DEFAULT_HTTP_VERIFY_SSL = True
    DEFAULT_HTTP_MAX_KEEPALIVE_CONNECTIONS = 10
    DEFAULT_HTTP_MAX_CONNECTIONS = 100
    DEFAULT_USE_SYSTEM_PROXY = True


class AsyncHttpClient:
    """异步 HTTP 客户端"""

    def __init__(
        self,
        timeout: int = None,
        max_retries: int = 0,
        keep_alive: bool = None,
        verify_ssl: bool = None,
        max_keepalive_connections: int = None,
        max_connections: int = None,
        use_system_proxy: bool = None
    ):
        self.timeout = timeout if timeout is not None else DEFAULT_TIMEOUT_SECONDS
        self.max_retries = max_retries
        self.keep_alive = keep_alive if keep_alive is not None else DEFAULT_HTTP_KEEP_ALIVE
        self.verify_ssl = verify_ssl if verify_ssl is not None else DEFAULT_HTTP_VERIFY_SSL
        self.max_keepalive_connections = max_keepalive_connections if max_keepalive_connections is not None else DEFAULT_HTTP_MAX_KEEPALIVE_CONNECTIONS
        self.max_connections = max_connections if max_connections is not None else DEFAULT_HTTP_MAX_CONNECTIONS
        self.use_system_proxy = use_system_proxy if use_system_proxy is not None else DEFAULT_USE_SYSTEM_PROXY
        self.client: Optional[httpx.AsyncClient] = None
        self.request_id_map: Dict[str, Dict[str, Any]] = {}  # 追踪 Request ID 和性能数据
        self.request_count = 0
        self.total_bytes_sent = 0
        self.total_bytes_received = 0

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def connect(self):
        """创建并配置 httpx.AsyncClient 实例。"""
        limits = httpx.Limits(
            max_keepalive_connections=self.max_keepalive_connections if self.keep_alive else 0,
            max_connections=self.max_connections
        )

        client_kwargs = {
            "timeout": self.timeout,
            "limits": limits,
            "verify": self.verify_ssl,
            "http2": False,
            "trust_env": bool(self.use_system_proxy),
        }

        if not self.use_system_proxy:
            logger.info("HTTP 客户端已禁用系统代理 (trust_env=False)")
        else:
            logger.info("HTTP 客户端使用系统代理设置 (trust_env=True)")

        self.client = httpx.AsyncClient(**client_kwargs)
        logger.info(f"HTTP 客户端已连接 (timeout={self.timeout}s, keep_alive={self.keep_alive}, use_system_proxy={self.use_system_proxy})")

    async def close(self):
        """关闭 httpx.AsyncClient 实例。"""
        if self.client:
            await self.client.aclose()
            self.client = None

    def _generate_request_id(self) -> str:
        """生成一个唯一的请求 ID。"""
        return str(uuid.uuid4())

    async def post(
        self,
        url: str,
        json_data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        track_request_id: bool = True
    ) -> Tuple[int, Dict[str, Any], str]:
        """
        发送一个 POST 请求。

        Args:
            url: 请求的 URL。
            json_data: 要发送的 JSON 数据。
            headers: 可选的请求头。
            track_request_id: 是否生成并添加 X-Request-ID 请求头。

        Returns:
            一个元组，包含 (状态码, 响应 JSON, 请求 ID)。
        """
        if not self.client:
            await self.connect()

        request_id = self._generate_request_id()
        start_time = time.time()

        request_headers = headers or {}
        if track_request_id:
            request_headers["X-Request-ID"] = request_id

        try:
            response = await self.client.post(
                url,
                json=json_data,
                headers=request_headers
            )

            bytes_received = len(response.content)
            response_time = time.time() - start_time

            self.request_count += 1
            self.total_bytes_sent += len(json_module.dumps(json_data).encode())
            self.total_bytes_received += bytes_received

            try:
                response_json = response.json()
            except json_module.JSONDecodeError:
                response_json = {"error": {"message": response.text or "无法解析响应体"}}

            logger.debug(f"POST {url} -> {response.status_code} ({response_time:.3f}s, {bytes_received} 字节)")
            return response.status_code, response_json, request_id

        except httpx.TimeoutException as e:
            logger.warning(f"POST {url} -> 超时 ({self.timeout}s): {str(e)}")
            return 408, {"error": {"message": f"请求超时: {str(e)}"}}, request_id
        except httpx.RequestError as e:
            logger.error(f"HTTP 请求失败: {e.__class__.__name__} - {str(e)}")
            return 500, {"error": {"message": f"HTTP 请求失败: {str(e)}"}}, request_id
        except Exception as e:
            logger.error(f"POST {url} -> 未知异常: {str(e)}", exc_info=True)
            return 500, {"error": {"message": f"发生未知错误: {str(e)}"}}, request_id
