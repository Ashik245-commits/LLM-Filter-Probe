"""
配置系统 (Configuration System)
管理应用的所有配置参数

============ 关键修复：从配置文件读取所有默认值 ============
所有默认值都应该来自 config/settings/default.json 或 config/system/*.json，
确保单一事实源 (SSOT)
"""
import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# 导入常量
from core.constants import (
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_USE_SYSTEM_PROXY,
    DEFAULT_MIN_GRANULARITY,
    DEFAULT_CONCURRENCY,
    DEFAULT_HTTP_KEEP_ALIVE,
    DEFAULT_HTTP_VERIFY_SSL,
    DEFAULT_HTTP_MAX_KEEPALIVE_CONNECTIONS,
    DEFAULT_HTTP_MAX_CONNECTIONS,
    DEFAULT_CACHE_ENABLED,
    DEFAULT_CACHE_MAX_SIZE,
    DEFAULT_CACHE_DEFAULT_TTL,
    DEFAULT_MONITOR_ENABLED,
    DEFAULT_MONITOR_MAX_HISTORY,
    DEFAULT_MONITOR_COLLECTION_INTERVAL,
    DEFAULT_ERROR_RECOVERY_ENABLED,
    DEFAULT_ERROR_RECOVERY_MAX_RETRIES,
    DEFAULT_ERROR_RECOVERY_INITIAL_BACKOFF,
    DEFAULT_ERROR_RECOVERY_MAX_BACKOFF,
    DEFAULT_DICT_SCANNER_MAX_CHUNK_SIZE,
    MAX_CONCURRENCY,
)


@dataclass
class APIConfig:
    """API 配置"""
    model: str = "gpt-4o-mini"  # 模型名称
    temperature: float = 0.7  # 温度参数
    max_tokens: int = 100  # 最大 token 数
    system_prompt: str = "You are a helpful assistant."  # 系统提示词


@dataclass
class HTTPConfig:
    """HTTP 客户端配置"""
    # ============ 从常量读取默认值 ============
    timeout: int = None
    max_retries: int = 0  # 最大重试次数（由 engine 控制）
    keep_alive: bool = None
    verify_ssl: bool = None
    max_keepalive_connections: int = None
    max_connections: int = None
    use_system_proxy: bool = None
    
    def __post_init__(self):
        """初始化后从常量同步默认值"""
        if self.timeout is None:
            self.timeout = DEFAULT_TIMEOUT_SECONDS
        if self.keep_alive is None:
            self.keep_alive = DEFAULT_HTTP_KEEP_ALIVE
        if self.verify_ssl is None:
            self.verify_ssl = DEFAULT_HTTP_VERIFY_SSL
        if self.max_keepalive_connections is None:
            self.max_keepalive_connections = DEFAULT_HTTP_MAX_KEEPALIVE_CONNECTIONS
        if self.max_connections is None:
            self.max_connections = DEFAULT_HTTP_MAX_CONNECTIONS
        if self.use_system_proxy is None:
            self.use_system_proxy = DEFAULT_USE_SYSTEM_PROXY


@dataclass
class CacheConfig:
    """缓存配置"""
    enabled: bool = None
    max_size: int = None
    default_ttl: int = None
    
    def __post_init__(self):
        """初始化后从常量同步默认值"""
        if self.enabled is None:
            self.enabled = DEFAULT_CACHE_ENABLED
        if self.max_size is None:
            self.max_size = DEFAULT_CACHE_MAX_SIZE
        if self.default_ttl is None:
            self.default_ttl = DEFAULT_CACHE_DEFAULT_TTL


@dataclass
class MonitorConfig:
    """性能监控配置"""
    enabled: bool = None
    max_history: int = None
    collection_interval: int = None
    
    def __post_init__(self):
        """初始化后从常量同步默认值"""
        if self.enabled is None:
            self.enabled = DEFAULT_MONITOR_ENABLED
        if self.max_history is None:
            self.max_history = DEFAULT_MONITOR_MAX_HISTORY
        if self.collection_interval is None:
            self.collection_interval = DEFAULT_MONITOR_COLLECTION_INTERVAL


@dataclass
class ErrorRecoveryConfig:
    """错误恢复配置"""
    enabled: bool = None
    max_retries: int = None
    initial_backoff: float = None
    max_backoff: float = None
    
    def __post_init__(self):
        """初始化后从常量同步默认值"""
        if self.enabled is None:
            self.enabled = DEFAULT_ERROR_RECOVERY_ENABLED
        if self.max_retries is None:
            self.max_retries = DEFAULT_ERROR_RECOVERY_MAX_RETRIES
        if self.initial_backoff is None:
            self.initial_backoff = DEFAULT_ERROR_RECOVERY_INITIAL_BACKOFF
        if self.max_backoff is None:
            self.max_backoff = DEFAULT_ERROR_RECOVERY_MAX_BACKOFF


@dataclass
class ScannerConfig:
    """扫描器配置"""
    # ============ 从常量读取默认值 ============
    text_min_granularity: int = None
    dict_max_chunk_size: int = None
    default_concurrency: int = None
    max_concurrency: int = None
    
    def __post_init__(self):
        """初始化后从常量同步默认值"""
        if self.text_min_granularity is None:
            self.text_min_granularity = DEFAULT_MIN_GRANULARITY
        if self.dict_max_chunk_size is None:
            self.dict_max_chunk_size = DEFAULT_DICT_SCANNER_MAX_CHUNK_SIZE
        if self.default_concurrency is None:
            self.default_concurrency = DEFAULT_CONCURRENCY
        if self.max_concurrency is None:
            self.max_concurrency = MAX_CONCURRENCY


@dataclass
class AppConfig:
    """应用配置"""
    debug: bool = False  # 调试模式
    host: str = os.getenv('API_HOST', '0.0.0.0')  # 服务器主机，从环境变量读取
    port: int = int(os.getenv('API_PORT', '19002'))  # 服务器端口，从环境变量读取
    log_level: str = os.getenv('LOG_LEVEL', 'info')  # 日志级别，从环境变量读取
    
    # 子配置
    api: APIConfig = None
    http: HTTPConfig = None
    cache: CacheConfig = None
    monitor: MonitorConfig = None
    error_recovery: ErrorRecoveryConfig = None
    scanner: ScannerConfig = None
    
    def __post_init__(self):
        """初始化默认子配置"""
        if self.api is None:
            self.api = APIConfig()
        if self.http is None:
            self.http = HTTPConfig()
        if self.cache is None:
            self.cache = CacheConfig()
        if self.monitor is None:
            self.monitor = MonitorConfig()
        if self.error_recovery is None:
            self.error_recovery = ErrorRecoveryConfig()
        if self.scanner is None:
            self.scanner = ScannerConfig()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "debug": self.debug,
            "host": self.host,
            "port": self.port,
            "log_level": self.log_level,
            "api": asdict(self.api),
            "http": asdict(self.http),
            "cache": asdict(self.cache),
            "monitor": asdict(self.monitor),
            "error_recovery": asdict(self.error_recovery),
            "scanner": asdict(self.scanner),
        }


class ConfigManager:
    """配置管理器"""
    
    _instance: Optional['ConfigManager'] = None
    _config: Optional[AppConfig] = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def load_config(
        cls,
        config_file: Optional[str] = None,
        env: str = "development"
    ) -> AppConfig:
        """
        加载配置
        
        Args:
            config_file: 配置文件路径
            env: 环境 (development/production)
        
        Returns:
            AppConfig
        """
        manager = cls()
        
        # 如果已加载，直接返回
        if manager._config is not None:
            return manager._config
        
        # 创建默认配置
        config = AppConfig()
        
        # 如果指定了配置文件，加载它
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_dict = json.load(f)
                    manager._merge_config(config, config_dict)
            except Exception as e:
                print(f"警告: 加载配置文件失败: {e}")
        
        # 根据环境调整配置
        if env == "production":
            config.debug = False
            config.log_level = "warning"
        else:
            config.debug = True
            config.log_level = "debug"
        
        manager._config = config
        return config
    
    @classmethod
    def _merge_config(cls, config: AppConfig, config_dict: Dict[str, Any]):
        """合并配置字典到配置对象"""
        for key, value in config_dict.items():
            if key == "api" and isinstance(value, dict):
                config.api = APIConfig(**value)
            elif key == "http" and isinstance(value, dict):
                config.http = HTTPConfig(**value)
            elif key == "cache" and isinstance(value, dict):
                config.cache = CacheConfig(**value)
            elif key == "monitor" and isinstance(value, dict):
                config.monitor = MonitorConfig(**value)
            elif key == "error_recovery" and isinstance(value, dict):
                config.error_recovery = ErrorRecoveryConfig(**value)
            elif key == "scanner" and isinstance(value, dict):
                config.scanner = ScannerConfig(**value)
            elif hasattr(config, key):
                setattr(config, key, value)
    
    @classmethod
    def get_config(cls) -> AppConfig:
        """获取配置"""
        manager = cls()
        if manager._config is None:
            manager._config = AppConfig()
        return manager._config
    
    @classmethod
    def save_config(cls, config_file: str):
        """保存配置到文件"""
        manager = cls()
        if manager._config is None:
            raise ValueError("配置未加载")
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(manager._config.to_dict(), f, indent=2, ensure_ascii=False)


# 全局配置实例
config = ConfigManager.load_config(env="development")
