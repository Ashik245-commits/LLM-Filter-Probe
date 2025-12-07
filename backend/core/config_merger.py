"""
配置合并器 - 负责合并多层配置

职责：
  - 按优先级合并配置
  - 验证和修复配置
  - 对敏感信息进行掩码
"""
import logging
from typing import Dict, Any, Optional

from core.config_validator import ConfigValidator

logger = logging.getLogger(__name__)


def _mask_key(key: str) -> str:
    """对 API Key 进行掩码处理"""
    if not key:
        return key
    if len(key) <= 6:
        return "***"
    return f"{key[:3]}***{key[-3:]}"


class ConfigMerger:
    """配置合并器 - 合并多层配置"""
    
    @staticmethod
    def merge_configs(
        default_config: Dict[str, Any],
        user_config: Dict[str, Any],
        credentials: Dict[str, Any],
        rules: Dict[str, Any],
        algorithm_config: Dict[str, Any],
        runtime_overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        按优先级合并配置（洋葱模型）
        
        优先级（从低到高）：
        1. 默认配置 (config/settings/default.json)
        2. 用户配置 (config/settings/user.json)
        3. 凭证 (config/API/credentials.json)
        4. 预设规则 (config/presets/{preset}.json)
        5. 系统级算法配置 (config/algorithm/default.json)
        6. 运行时覆盖 (API 请求参数)
        
        Args:
            default_config: 默认配置
            user_config: 用户配置
            credentials: 凭证
            rules: 规则
            algorithm_config: 算法配置
            runtime_overrides: 运行时覆盖
        
        Returns:
            合并后的完整配置字典
        """
        logger.debug("[ConfigMerger] 开始合并配置")
        
        # Step 1: 合并设置
        logger.debug("[ConfigMerger] Step 1: 合并设置")
        merged = dict(default_config)
        merged.update(user_config)
        logger.debug(f"[ConfigMerger]   → 合并了 {len(merged)} 个设置项")
        
        # Step 2: 合并凭证
        logger.debug("[ConfigMerger] Step 2: 合并凭证")
        merged.update(credentials)
        logger.debug(f"[ConfigMerger]   → 合并了 {len(credentials)} 个凭证项")
        
        # Step 3: 合并规则
        logger.debug("[ConfigMerger] Step 3: 合并规则")
        merged.update(rules)
        logger.debug(f"[ConfigMerger]   → 合并了 {len(rules)} 个规则项")
        
        # Step 4: 合并算法配置
        logger.debug("[ConfigMerger] Step 4: 合并算法配置")
        if algorithm_config:
            merged["algorithm"] = algorithm_config
            logger.debug(f"[ConfigMerger]   → 加载了算法配置 ({len(algorithm_config)} 个字段)")
        
        # Step 5: 应用运行时覆盖
        if runtime_overrides:
            logger.debug(f"[ConfigMerger] Step 5: 应用运行时覆盖 ({len(runtime_overrides)} 个字段)")
            merged.update(runtime_overrides)
            logger.debug(f"[ConfigMerger]   → 运行时覆盖了 {len(runtime_overrides)} 个字段")
        
        # Step 6: 验证和修复配置
        logger.debug("[ConfigMerger] Step 6: 验证和修复配置")
        merged = ConfigMerger._validate_and_fix_config(merged)
        
        # 记录最终配置（掩码敏感信息）
        config_summary = {k: v for k, v in merged.items() if k not in {'api_key', 'api_url'}}
        logger.info(f"[ConfigMerger] 配置合并完成 (共 {len(merged)} 个字段)")
        logger.debug(f"[ConfigMerger] 配置摘要: {config_summary}")
        
        return merged
    
    @staticmethod
    def _validate_and_fix_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证和修复配置
        
        关键修复：当 algorithm_mode 为 "hybrid" 时，强制 min_granularity = 1
        这是为了确保二分查找能够正确交接到 PrecisionScanner
        
        Args:
            config: 配置字典
        
        Returns:
            修复后的配置字典
        """
        # 获取算法模式
        algorithm_mode = config.get("algorithm_mode", "hybrid")
        min_granularity = config.get("min_granularity", 30)
        
        # 【关键修复】如果是混合模式，强制 min_granularity = 1
        if algorithm_mode == "hybrid":
            if min_granularity != 1:
                logger.warning(
                    f"[ConfigMerger] 【关键修复】检测到混合模式下 min_granularity={min_granularity}，"
                    f"强制覆盖为 1 以确保正确的交接逻辑"
                )
                config["min_granularity"] = 1
        
        # 验证其他关键参数
        if config.get("overlap_size", 0) < 0:
            logger.warning("[ConfigMerger] overlap_size 不能为负数，已重置为 10")
            config["overlap_size"] = 10
        
        if config.get("chunk_size", 0) <= 0:
            logger.warning("[ConfigMerger] chunk_size 必须大于 0，已重置为 50000")
            config["chunk_size"] = 50000
        
        if config.get("concurrency", 0) <= 0:
            logger.warning("[ConfigMerger] concurrency 必须大于 0，已重置为 5")
            config["concurrency"] = 5
        
        return config
    
    @staticmethod
    def mask_sensitive_info(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        对配置中的敏感信息进行掩码
        
        Args:
            config: 配置字典
        
        Returns:
            掩码后的配置字典
        """
        masked = dict(config)
        masked["api_key"] = _mask_key(masked.get("api_key", ""))
        return masked
    
    @staticmethod
    def split_config(config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        将完整配置拆分为不同的部分
        
        Args:
            config: 完整配置字典
        
        Returns:
            拆分后的配置字典 {credentials, settings, rules, algorithm}
        """
        from core.config_loader import CREDENTIAL_KEYS, SETTINGS_KEYS, RULE_KEYS
        
        credentials = {}
        settings = {}
        rules = {}
        algorithm = {}
        
        for key, value in config.items():
            if key in CREDENTIAL_KEYS:
                credentials[key] = value
            elif key in SETTINGS_KEYS:
                settings[key] = value
            elif key in RULE_KEYS:
                rules[key] = value
            elif key == "algorithm":
                algorithm = value
        
        return {
            "credentials": credentials,
            "settings": settings,
            "rules": rules,
            "algorithm": algorithm
        }

