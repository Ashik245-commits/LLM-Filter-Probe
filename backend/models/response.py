"""
响应数据模型 (Response Models)

本模块使用 Pydantic 定义了所有 API 响应体的结构。
这些模型确保了从应用传出的数据是结构化的，并被 FastAPI 用于自动生成 API 文档。
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class SettingsResponse(BaseModel):
    """
    用于返回当前所有设置的响应模型。
    注意：出于安全考虑，API 密钥等敏感信息在返回前应被掩码处理。
    """
    api_url: str = Field(..., description="API 地址")
    api_key: str = Field(..., description="API 密钥（已掩码）")
    api_model: str = Field(..., description="模型名称")
    preset: str = Field(..., description="预设名称")
    concurrency: int = Field(..., description="并发数")
    timeout_seconds: int = Field(..., description="超时时间")
    chunk_size: int = Field(..., description="分块大小")
    max_retries: int = Field(..., description="最大重试次数")
    block_status_codes: list = Field(..., description="阻止状态码")
    block_keywords: list = Field(..., description="阻止关键词")
    retry_status_codes: list = Field(..., description="重试状态码")


class ScanResponse(BaseModel):
    """
    发起扫描操作后的基本响应模型。
    """
    session_id: str = Field(..., description="会话 ID")
    status: str = Field(..., description="扫描状态")
    message: Optional[str] = Field(None, description="消息")


class ErrorResponse(BaseModel):
    """
    标准化的错误响应模型。
    """
    error: str = Field(..., description="错误信息")
    code: Optional[int] = Field(None, description="错误代码")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
