"""
数据模型 (Models)

包含所有 Pydantic 数据模型
"""

from .request import SettingsPayload, ScanRequest
from .response import SettingsResponse, ScanResponse, ErrorResponse

__all__ = [
    "SettingsPayload",
    "ScanRequest",
    "SettingsResponse",
    "ScanResponse",
    "ErrorResponse"
]

