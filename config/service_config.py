"""
服务配置管理

提供统一的服务配置管理，支持环境变量配置和行为控制。
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DatabaseConfig:
    """数据库配置"""
    path: str = "data/admin_divisions.db"
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 缓存过期时间（秒）


@dataclass
class CoordinateServiceConfig:
    """坐标服务配置"""
    enabled: bool = True
    auto_init: bool = True
    health_check_interval: int = 300  # 健康检查间隔（秒）
    max_retries: int = 3
    timeout: int = 10  # 超时时间（秒）
    database: DatabaseConfig = field(default_factory=DatabaseConfig)


@dataclass
class WeatherServiceConfig:
    """天气服务配置"""
    enabled: bool = True
    api_key: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    cache_enabled: bool = True
    cache_ttl: int = 600  # 缓存过期时间（秒）


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    debug_logging: bool = False
    log_to_file: bool = True
    log_file_path: str = "logs/app.log"
    max_log_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


@dataclass
class ServiceConfig:
    """服务配置总览"""
    coordinate_service: CoordinateServiceConfig = field(default_factory=CoordinateServiceConfig)
    weather_service: WeatherServiceConfig = field(default_factory=WeatherServiceConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    @classmethod
    def from_env(cls) -> 'ServiceConfig':
        """从环境变量创建配置"""
        config = cls()

        # 坐标服务配置
        if os.getenv('COORDINATE_SERVICE_ENABLED'):
            config.coordinate_service.enabled = os.getenv('COORDINATE_SERVICE_ENABLED').lower() == 'true'
        if os.getenv('COORDINATE_DB_PATH'):
            config.coordinate_service.database.path = os.getenv('COORDINATE_DB_PATH')
        if os.getenv('COORDINATE_CACHE_TTL'):
            config.coordinate_service.database.cache_ttl = int(os.getenv('COORDINATE_CACHE_TTL'))
        if os.getenv('COORDINATE_HEALTH_CHECK_INTERVAL'):
            config.coordinate_service.health_check_interval = int(os.getenv('COORDINATE_HEALTH_CHECK_INTERVAL'))

        # 天气服务配置
        if os.getenv('WEATHER_SERVICE_ENABLED'):
            config.weather_service.enabled = os.getenv('WEATHER_SERVICE_ENABLED').lower() == 'true'
        if os.getenv('CAIYUN_API_KEY'):
            config.weather_service.api_key = os.getenv('CAIYUN_API_KEY')
        if os.getenv('WEATHER_CACHE_TTL'):
            config.weather_service.cache_ttl = int(os.getenv('WEATHER_CACHE_TTL'))

        # 日志配置
        if os.getenv('DEBUG_LOGGING'):
            config.logging.debug_logging = os.getenv('DEBUG_LOGGING').lower() == 'true'
        if os.getenv('LOG_LEVEL'):
            config.logging.level = os.getenv('LOG_LEVEL').upper()
        if os.getenv('LOG_FILE_PATH'):
            config.logging.log_file_path = os.getenv('LOG_FILE_PATH')

        return config

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'coordinate_service': {
                'enabled': self.coordinate_service.enabled,
                'auto_init': self.coordinate_service.auto_init,
                'health_check_interval': self.coordinate_service.health_check_interval,
                'max_retries': self.coordinate_service.max_retries,
                'timeout': self.coordinate_service.timeout,
                'database': {
                    'path': self.coordinate_service.database.path,
                    'cache_enabled': self.coordinate_service.database.cache_enabled,
                    'cache_ttl': self.coordinate_service.database.cache_ttl,
                }
            },
            'weather_service': {
                'enabled': self.weather_service.enabled,
                'timeout': self.weather_service.timeout,
                'max_retries': self.weather_service.max_retries,
                'cache_enabled': self.weather_service.cache_enabled,
                'cache_ttl': self.weather_service.cache_ttl,
                'api_key_configured': bool(self.weather_service.api_key),
            },
            'logging': {
                'level': self.logging.level,
                'debug_logging': self.logging.debug_logging,
                'log_to_file': self.logging.log_to_file,
                'log_file_path': self.logging.log_file_path,
                'max_log_size': self.logging.max_log_size,
                'backup_count': self.logging.backup_count,
            }
        }

    def ensure_directories(self):
        """确保必要的目录存在"""
        # 确保数据库目录存在
        db_path = Path(self.coordinate_service.database.path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # 确保日志目录存在
        if self.logging.log_to_file:
            log_path = Path(self.logging.log_file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)


# 全局配置实例
_global_config: Optional[ServiceConfig] = None


def get_service_config() -> ServiceConfig:
    """
    获取全局服务配置实例

    Returns:
        ServiceConfig: 服务配置实例
    """
    global _global_config
    if _global_config is None:
        _global_config = ServiceConfig.from_env()
        _global_config.ensure_directories()
    return _global_config


def reload_config() -> ServiceConfig:
    """
    重新加载配置

    Returns:
        ServiceConfig: 新的配置实例
    """
    global _global_config
    _global_config = ServiceConfig.from_env()
    _global_config.ensure_directories()
    return _global_config


def get_config_value(key: str, default: Any = None) -> Any:
    """
    通过点分隔的键获取配置值

    Args:
        key: 配置键，例如 'coordinate_service.enabled'
        default: 默认值

    Returns:
        配置值
    """
    config = get_service_config()
    keys = key.split('.')

    value = config
    for k in keys:
        if hasattr(value, k):
            value = getattr(value, k)
        elif isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default

    return value