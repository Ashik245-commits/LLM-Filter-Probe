"""
请求日志中间件 (Request Logging Middleware)

该中间件记录所有传入的 HTTP 请求和它们对应的响应，以便于调试和监控。
为了保持日志的清洁，它会特意过滤掉来自健康检查端点 (`/health`, `/api/health`) 的日志，
因为这些日志通常是高频且低价值的。
"""
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next):
        """
        处理请求和响应，并记录相关信息。

        Args:
            request: 传入的请求对象。
            call_next: 调用下一个中间件或路由处理程序的函数。
        """
        # 过滤掉健康检查端点的日志，以避免日志泛滥
        is_health_check = request.url.path in ["/api/health", "/health"]

        if not is_health_check:
            logger.info(
                f"[请求] {request.method} {request.url.path} | "
                f"来自: {request.client.host if request.client else 'unknown'}"
            )

        try:
            response = await call_next(request)

            if not is_health_check:
                logger.info(
                    f"[响应] {request.method} {request.url.path} | "
                    f"状态: {response.status_code}"
                )

            return response
        except Exception as e:
            # 即使发生异常，也记录下来
            if not is_health_check:
                logger.error(
                    f"[错误] {request.method} {request.url.path} | "
                    f"错误: {str(e)}",
                    exc_info=True
                )
            raise
