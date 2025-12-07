"""
HTTP 请求构建器 (Request Builder)

职责：
- 构建 LLM API 请求
- 处理模板替换
- 验证请求格式
"""
import json
import logging
from typing import Tuple, Dict, Any
from ..presets import Preset

logger = logging.getLogger(__name__)


class RequestBuilder:
    """HTTP 请求构建器"""
    
    def __init__(self, preset: Preset, engine_id: str = ""):
        """
        初始化请求构建器
        
        Args:
            preset: 预设配置
            engine_id: 引擎 ID（用于日志追踪）
        """
        self.preset = preset
        self.engine_id = engine_id or "default"
    
    def build(self, text_segment: str) -> Tuple[str, Dict[str, Any]]:
        """
        构建 HTTP 请求
        
        Args:
            text_segment: 文本片段
        
        Returns:
            (URL, 请求体)
        
        Raises:
            ValueError: 如果请求模板无效
        """
        # 使用 json.dumps 转义文本，然后去掉外层引号
        escaped_text = json.dumps(text_segment)[1:-1]
        
        # 替换模板中的占位符
        template = self.preset.request_template
        template = template.replace("{{TEXT}}", escaped_text)
        template = template.replace("{{MODEL}}", self.preset.model)
        
        # 解析请求体
        try:
            request_body = json.loads(template)
        except json.JSONDecodeError as e:
            logger.error(f"[{self.engine_id}] 请求模板解析失败: {str(e)}")
            logger.error(f"[{self.engine_id}] 模板内容: {template[:200]}")
            raise ValueError(f"Invalid request template: {str(e)}")
        
        # 设置 max_tokens 以避免因 Token 上限导致的错误
        request_body["max_tokens"] = 10
        
        # 构建 URL
        api_url = self.preset.api_url
        if not api_url.endswith("/"):
            api_url += "/"
        
        url = f"{api_url}chat/completions"
        
        logger.debug(f"[{self.engine_id}] 请求已构建: {url}")
        
        return url, request_body

