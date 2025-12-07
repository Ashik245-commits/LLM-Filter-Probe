"""
配置验证器 - 验证配置的有效性和检测冲突

职责：
  - 验证 API 配置的有效性
  - 验证设置配置的有效性
  - 检测配置之间的冲突
  - 提供详细的错误信息
"""
from typing import Dict, Any, Tuple, List
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class ConfigValidator:
    """配置验证器"""
    
    @staticmethod
    def validate_api_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证 API 配置
        
        Args:
            config: API 配置字典
        
        Returns:
            (是否有效, 错误列表)
        """
        errors = []
        
        # 必填字段检查
        if not config.get('api_url'):
            errors.append("api_url 不能为空")
        else:
            # URL 格式检查
            try:
                result = urlparse(config['api_url'])
                if not all([result.scheme, result.netloc]):
                    errors.append("api_url 格式不正确，必须是有效的 URL")
            except Exception:
                errors.append("api_url 格式不正确")
        
        if not config.get('api_key'):
            errors.append("api_key 不能为空")
        
        if not config.get('api_model'):
            errors.append("api_model 不能为空")
        
        # 数值范围检查
        try:
            concurrency = config.get('concurrency', 20)
            if not isinstance(concurrency, int) or concurrency <= 0 or concurrency > 100:
                errors.append("concurrency 必须是 1-100 之间的整数")
        except (TypeError, ValueError):
            errors.append("concurrency 必须是整数")
        
        try:
            timeout = config.get('timeout_seconds', 30)
            if not isinstance(timeout, int) or timeout <= 0 or timeout > 300:
                errors.append("timeout_seconds 必须是 1-300 秒之间的整数")
        except (TypeError, ValueError):
            errors.append("timeout_seconds 必须是整数")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_settings_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证设置配置
        
        Args:
            config: 设置配置字典
        
        Returns:
            (是否有效, 错误列表)
        """
        errors = []
        
        # 验证预设名称
        valid_presets = ['official', 'relay', 'custom']
        if config.get('preset') and config.get('preset') not in valid_presets:
            errors.append(f"preset 必须是以下之一: {', '.join(valid_presets)}")
        
        # 验证并发数
        try:
            concurrency = config.get('concurrency', 15)
            if not isinstance(concurrency, int) or concurrency <= 0 or concurrency > 100:
                errors.append("concurrency 必须是 1-100 之间的整数")
        except (TypeError, ValueError):
            errors.append("concurrency 必须是整数")
        
        # 验证超时时间
        try:
            timeout = config.get('timeout_seconds', 30)
            if not isinstance(timeout, int) or timeout <= 0 or timeout > 300:
                errors.append("timeout_seconds 必须是 1-300 秒之间的整数")
        except (TypeError, ValueError):
            errors.append("timeout_seconds 必须是整数")
        
        # 验证块大小
        try:
            chunk_size = config.get('chunk_size', 30000)
            if not isinstance(chunk_size, int) or chunk_size <= 0:
                errors.append("chunk_size 必须大于 0")
        except (TypeError, ValueError):
            errors.append("chunk_size 必须是整数")
        
        # 验证最大重试次数
        try:
            max_retries = config.get('max_retries', 3)
            if not isinstance(max_retries, int) or max_retries < 0:
                errors.append("max_retries 必须是非负整数")
        except (TypeError, ValueError):
            errors.append("max_retries 必须是整数")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def detect_conflicts(old_config: Dict[str, Any], new_config: Dict[str, Any]) -> List[str]:
        """
        检测配置冲突
        
        Args:
            old_config: 旧配置
            new_config: 新配置
        
        Returns:
            冲突列表
        """
        conflicts = []
        
        # 检查关键字段变化
        if old_config.get('api_url') != new_config.get('api_url'):
            conflicts.append("API URL 已更改，可能影响现有会话")
        
        if old_config.get('api_key') != new_config.get('api_key'):
            conflicts.append("API Key 已更改，可能影响现有会话")
        
        if old_config.get('api_model') != new_config.get('api_model'):
            conflicts.append("模型已更改，可能影响扫描结果")
        
        if old_config.get('preset') != new_config.get('preset'):
            conflicts.append("预设已更改，可能影响扫描规则")
        
        return conflicts

