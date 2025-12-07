"""
全局错误处理中间件 (Global Error Handler Middleware)

该中间件捕获应用中所有未被处理的异常，记录错误日志，并向客户端返回一个标准化的 JSON 错误响应。
这可以防止应用因意外错误而崩溃，并为前端提供一致的错误处理体验。
"""
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """全局错误处理中间件"""

    async def dispatch(self, request: Request, call_next):
        """
        处理所有传入的请求，捕获在请求处理链中发生的任何异常。

        Args:
            request: 传入的请求对象。
            call_next: 调用下一个中间件或路由处理程序的函数。

        Returns:
            一个标准的 FastAPI 响应对象，如果发生异常，则返回一个 JSONResponse。
        """
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"未处理的异常: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": str(e)
                }
            )
