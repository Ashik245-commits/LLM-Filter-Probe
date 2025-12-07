"""
请求数据模型 (Request Models)

本模块使用 Pydantic 定义了所有 API 请求体的结构、类型和验证规则。
这些模型确保了进入应用的数据是有效和类型安全的，并被 FastAPI 用于自动生成 API 文档。
"""
from pydantic import BaseModel, Field
from typing import Optional


class SettingsPayload(BaseModel):
    """
    用于更新各类设置的统一请求体模型。
    这个模型是可选字段的集合，允许客户端只发送需要更新的配置项。
    """
    api_url: Optional[str] = Field(None, description="上游 API 基础地址")
    api_key: Optional[str] = Field(None, description="API 密钥")
    api_model: Optional[str] = Field(None, description="模型名称")
    preset: Optional[str] = Field(None, description="预设名称")
    
    # 高级配置
    concurrency: Optional[int] = Field(None, ge=1, le=100, description="最大并发数")
    timeout_seconds: Optional[int] = Field(None, ge=1, le=120, description="请求超时")
    chunk_size: Optional[int] = Field(None, ge=100, le=1000000, description="文本分块大小")
    min_granularity: Optional[int] = Field(None, ge=1, le=1000, description="最小查找粒度")
    overlap_size: Optional[int] = Field(None, ge=0, le=1000, description="重叠大小")
    max_retries: Optional[int] = Field(None, ge=0, le=10, description="最大重试次数")
    delimiter: Optional[str] = Field(None, description="文本分割符")
    token_limit: Optional[int] = Field(None, ge=1, le=1000, description="Token 上限")
    jitter: Optional[float] = Field(None, ge=0.0, le=5.0, description="重试抖动（秒）")
    use_system_proxy: Optional[bool] = Field(None, description="是否使用系统代理")
    algorithm_mode: Optional[str] = Field(None, description="算法模式 (hybrid/binary)")
    
    # 规则配置
    block_status_codes: Optional[list] = Field(None, description="阻止状态码列表")
    block_keywords: Optional[list] = Field(None, description="阻止关键词列表")
    retry_status_codes: Optional[list] = Field(None, description="重试状态码列表")


class ScanRequest(BaseModel):
    """
    发起文本扫描的请求体模型。
    """
    text: str = Field(..., description="待扫描文本")
    session_id: str = Field(..., description="会话 ID")


class VerifyRequest(BaseModel):
    """
    用于验证 API 凭证的请求体模型。
    """
    api_url: Optional[str] = Field(None, description="上游 API 基础地址，例如 https://api.openai.com/v1/")
    api_key: Optional[str] = Field(None, description="API 密钥，支持掩码格式传入")
    model: Optional[str] = Field(None, alias="api_model", description="模型名称，例如 gpt-4o-mini")
