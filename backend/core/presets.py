"""
预设管理模块
定义 Preset 配置模型和预设管理器
从 config/presets/ 目录加载预设配置
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class Preset(BaseModel):
    """
    扫描预设配置模型
    
    包含规则相关字段和性能参数。
    性能参数可从配置文件覆盖，但在预设中保留以保持向后兼容性。
    """
    
    name: str = Field(..., description="预设名称")
    display_name: str = Field(default="", description="预设显示名称")
    description: str = Field(default="", description="预设描述")
    api_url: str = Field(default="", description="API 基础地址")
    api_key: str = Field(default="", description="API 密钥")
    model: str = Field(default="", description="模型名称")
    request_template: str = Field(
        default='{"model": "{{MODEL}}", "messages": [{"role": "user", "content": "{{TEXT}}"}]}',
        description="请求模板"
    )
    block_status_codes: List[int] = Field(
        default=[],
        description="触发'已阻止'的状态码"
    )
    block_keywords: List[str] = Field(
        default=[],
        description="触发'已阻止'的关键词（用户定义）"
    )
    retry_status_codes: List[int] = Field(
        default=[429, 502, 503, 504],
        description="触发重试的状态码"
    )
    # ============ 性能参数（从 config/settings/default.json 读取默认值） ============
    concurrency: int = Field(
        default=15,
        ge=1,
        le=50,
        description="最大并发数"
    )
    chunk_size: int = Field(
        default=30000,
        ge=10,
        le=100000,
        description="分块大小（字符数）"
    )
    max_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="最大重试次数"
    )
    timeout: float = Field(
        default=30.0,
        ge=1.0,
        le=120.0,
        description="请求超时（秒）"
    )
    delimiter: str = Field(
        default="\n",
        description="文本分割符"
    )
    token_limit: int = Field(
        default=20,
        ge=1,
        le=1000,
        description="最大估计 token 数"
    )
    jitter: float = Field(
        default=0.5,
        ge=0.0,
        le=5.0,
        description="重试抖动因子（秒）"
    )
    use_system_proxy: bool = Field(
        default=True,
        description="是否使用系统代理环境变量"
    )
    min_granularity: int = Field(
        default=1,
        ge=1,
        le=1000,
        description="二分查找最小粒度（字符数）"
    )
    overlap_size: int = Field(
        default=15,
        ge=0,
        le=500,
        description="重叠分割大小（字符数）"
    )
    algorithm_mode: str = Field(
        default="hybrid",
        description="算法模式（hybrid/binary）"
    )
    
    class Config:
        """Pydantic 配置"""
        json_schema_extra = {
            "example": {
                "name": "custom",
                "api_url": "https://api.openai.com/v1/",
                "api_key": "sk-...",
                "model": "gpt-4o-mini",
                "concurrency": 5,
                "chunk_size": 1000,
                "max_retries": 3,
                "timeout": 20.0,
                "delimiter": "\n",
                "token_limit": 10,
                "jitter": 0.1,
                "min_granularity": 30,
                "overlap_size": 10
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class PresetManager:
    """预设管理器 - 从 config/presets/ 目录加载预设"""
    
    # 默认预设（备用）
    # 注意：所有高级参数（concurrency, chunk_size 等）应该从 config/settings/default.json 读取
    # 这里仅保留预设特定的字段（name, display_name, description, block_status_codes, retry_status_codes）
    DEFAULT_PRESETS = {
        "relay": {
            "name": "relay",
            "display_name": "Third-Party / OneAPI Relay",
            "description": "专为检测 OneAPI 或第三方中转网关的关键词字典拦截而设计。",
            "api_url": "https://api.openai.com/v1/",
            "api_key": "",
            "model": "gpt-4o-mini",
            "block_status_codes": [400, 403, 412, 422, 500, 502],
            "retry_status_codes": [429, 503, 504],
            # 性能参数（从 default.json 读取）
            "concurrency": 15,
            "chunk_size": 30000,
            "max_retries": 3,
            "timeout": 30.0,
            "delimiter": "\n",
            "token_limit": 20,
            "jitter": 0.5,
            "use_system_proxy": True,
            "min_granularity": 1,
            "overlap_size": 12,
            "algorithm_mode": "hybrid",
        },
        "official": {
            "name": "official",
            "display_name": "Official API",
            "description": "直接连接官方 API 接口进行测试。",
            "api_url": "https://api.openai.com/v1/",
            "api_key": "",
            "model": "gpt-4",
            "block_status_codes": [400, 401, 403, 500],
            "retry_status_codes": [429, 502, 503, 504],
            # 性能参数（从 default.json 读取）
            "concurrency": 15,
            "chunk_size": 30000,
            "max_retries": 3,
            "timeout": 30.0,
            "delimiter": "\n",
            "token_limit": 20,
            "jitter": 0.5,
            "use_system_proxy": True,
            "min_granularity": 1,
            "overlap_size": 12,
            "algorithm_mode": "hybrid",
        },
        "custom": {
            "name": "custom",
            "display_name": "Custom",
            "description": "用户自定义配置，所有参数均可调整。",
            "api_url": "",
            "api_key": "",
            "model": "",
            "block_status_codes": [],
            "retry_status_codes": [429, 502, 503, 504],
            # 性能参数（从 default.json 读取）
            "concurrency": 15,
            "chunk_size": 30000,
            "max_retries": 3,
            "timeout": 30.0,
            "delimiter": "\n",
            "token_limit": 20,
            "jitter": 0.5,
            "use_system_proxy": True,
            "min_granularity": 1,
            "overlap_size": 12,
            "algorithm_mode": "hybrid",
        }
    }
    
    @staticmethod
    def _get_presets_dir() -> Path:
        """获取预设目录路径（pathlib.Path）"""
        project_root = Path(__file__).resolve().parents[2]
        presets_dir = project_root / "config" / "presets"
        return presets_dir
    
    @staticmethod
    def _load_preset_from_file(preset_name: str) -> Optional[Dict[str, Any]]:
        """从文件加载预设配置"""
        presets_dir = PresetManager._get_presets_dir()
        preset_file = presets_dir / f"{preset_name}.json"
        
        try:
            if preset_file.exists():
                with open(preset_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                logger.warning(f"预设文件不存在: {preset_file}")
                return None
        except Exception as e:
            logger.error(f"加载预设文件失败 [{preset_name}]: {str(e)}")
            return None
    
    @classmethod
    def get_preset(cls, name: str) -> Optional[Preset]:
        """获取预设配置"""
        # 首先尝试从文件加载
        preset_data = cls._load_preset_from_file(name)
        
        # 如果文件不存在，使用默认预设
        if preset_data is None:
            if name not in cls.DEFAULT_PRESETS:
                logger.warning(f"预设不存在: {name}")
                return None
            preset_data = cls.DEFAULT_PRESETS[name]
        
        try:
            return Preset(**preset_data)
        except Exception as e:
            logger.error(f"加载预设失败 [{name}]: {str(e)}")
            return None
    
    @classmethod
    def list_presets(cls) -> List[Dict[str, Any]]:
        """列出所有可用的预设，按分类组织"""
        presets = []
        preset_names = ["relay", "official", "custom"]
        
        for name in preset_names:
            preset_instance = cls.get_preset(name)
            if preset_instance:
                # 获取显示名称和描述
                preset_data = cls._load_preset_from_file(name) or cls.DEFAULT_PRESETS.get(name, {})
                
                # 确定分类
                if name == "custom":
                    category = "预设"
                    group = "custom"
                else:
                    category = "预设"
                    group = "builtin"
                
                presets.append({
                    "name": name,
                    "display_name": preset_data.get("display_name", name.capitalize()),
                    "description": preset_data.get("description", f"Preset: {name}"),
                    "category": category,
                    "group": group,  # "custom" 或 "builtin"
                    "config": preset_instance.to_dict()
                })
        return presets

    @classmethod
    def create_from_config(cls, config: Dict[str, Any]) -> Preset:
        """从配置字典创建预设实例"""
        required_fields = ["name", "api_url", "api_key", "model"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"缺少必要字段: {field}")
        
        default_preset = cls.get_preset("relay")
        merged_config = default_preset.to_dict()
        merged_config.update(config)
        
        return Preset(**merged_config)
