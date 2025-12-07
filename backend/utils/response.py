"""
API 响应格式化工具

本模块提供了一组帮助函数，用于生成标准化的 API 响应格式，
确保所有从应用返回的成功和错误响应都具有一致的结构。
"""
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional

def success_response(data: Any = None, message: str = "操作成功") -> Dict[str, Any]:
    """
    生成一个标准的成功响应。

    Args:
        data: 响应中包含的数据。
        message: 描述操作结果的消息。

    Returns:
        一个包含 status, message, data 的字典。
    """
    return {
        "status": "ok",
        "message": message,
        "data": data
    }

def error_response(message: str, status_code: int = 400, error_type: Optional[str] = None) -> JSONResponse:
    """
    生成一个标准的错误响应并作为 JSONResponse 返回。

    Args:
        message: 错误信息。
        status_code: HTTP 状态码。
        error_type: 错误的类型标识符（可选）。

    Returns:
        一个包含错误信息的 JSONResponse 对象。
    """
    content = {
        "status": "error",
        "message": message,
    }
    if error_type:
        content["error_type"] = error_type
        
    return JSONResponse(
        status_code=status_code,
        content=content
    )

def raise_http_error(message: str, status_code: int = 500, error_type: Optional[str] = None):
    """
    直接抛出一个带有标准错误格式的 HTTPException。
    这在 FastAPI 的依赖项或路由处理程序中非常有用，可以中断执行并立即返回一个错误响应。

    Args:
        message: 错误信息。
        status_code: HTTP 状态码。
        error_type: 错误的类型标识符（可选）。
    """
    detail = {
        "status": "error",
        "message": message,
    }
    if error_type:
        detail["error_type"] = error_type
    
    raise HTTPException(
        status_code=status_code,
        detail=detail
    )
