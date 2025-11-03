# 服务模块规范

## 模块概述
服务模块提供系统所需的底层服务支持，包括天气查询、地名匹配、缓存管理和数据库服务。每个服务都独立运行，支持高并发和高可用性。

## 服务架构

### 1. 天气服务 (WeatherService)

**功能描述**: 提供天气数据查询和缓存功能

**接口定义**:
```python
from typing import Dict, Any, Optional
from core.interfaces import IService, ServiceConfig

class WeatherConfig(ServiceConfig):
    """天气服务配置"""
    api_key: str
    base_url: str = "https://api.openweathermap.org/data/2.5"
    cache_ttl: int = 300  # 5分钟缓存
    max_requests_per_hour: int = 1000
    timeout: int = 10

class WeatherService(IService):
    """天气服务"""

    def __init__(self, config: Optional[WeatherConfig] = None):
        self.config = config or WeatherConfig(name="weather_service")
        self.cache_client = None
        self.http_client = None

    @property
    def config(self) -> ServiceConfig:
        return self._config

    async def initialize(self) -> None:
        """初始化服务"""
        from services.cache.cache_service import CacheService
        import aiohttp

        self.cache_client = CacheService()
        await self.cache_client.initialize()

        self.http_client = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )

    async def cleanup(self) -> None:
        """清理服务"""
        if self.http_client:
            await self.http_client.close()
        if self.cache_client:
            await self.cache_client.cleanup()

    def health_check(self) -> bool:
        """健康检查"""
        return self.http_client is not None and self.cache_client is not None

    async def get_weather(self, location: str) -> Dict[str, Any]:
        """获取天气信息"""
        # 1. 检查缓存
        cache_key = f"weather:{location}"
        cached_data = await self.cache_client.get(cache_key)
        if cached_data:
            return cached_data

        # 2. 地名匹配
        from services.matching.location_service import LocationService
        location_service = LocationService()
        matched_location = await location_service.match_location(location)

        # 3. 调用API
        weather_data = await self._fetch_weather(matched_location)

        # 4. 缓存结果
        await self.cache_client.set(
            cache_key,
            weather_data,
            ttl=self.config.cache_ttl
        )

        return weather_data

    async def _fetch_weather(self, location: Dict[str, Any]) -> Dict[str, Any]:
        """获取天气数据"""
        url = f"{self.config.base_url}/weather"
        params = {
            "q": f"{location['name']},{location['country']}",
            "appid": self.config.api_key,
            "units": "metric",
            "lang": "zh_cn"
        }

        async with self.http_client.get(url, params=params) as response:
            if response.status != 200:
                raise Exception(f"Weather API error: {response.status}")

            data = await response.json()
            return self._format_weather_data(data)

    def _format_weather_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化天气数据"""
        return {
            "location": {
                "name": raw_data["name"],
                "country": raw_data["sys"]["country"]
            },
            "current": {
                "temperature": raw_data["main"]["temp"],
                "feels_like": raw_data["main"]["feels_like"],
                "humidity": raw_data["main"]["humidity"],
                "pressure": raw_data["main"]["pressure"],
                "description": raw_data["weather"][0]["description"],
                "wind_speed": raw_data["wind"]["speed"],
                "wind_direction": raw_data["wind"].get("deg", 0)
            },
            "timestamp": datetime.now().isoformat()
        }
```

### 2. 地名匹配服务 (LocationService)

**功能描述**: 提供智能地名匹配和标准化功能

**接口定义**:
```python
from typing import Dict, Any, List, Optional
from core.interfaces import IService, ServiceConfig

class LocationConfig(ServiceConfig):
    """地名服务配置"""
    database_url: str
    cache_ttl: int = 3600  # 1小时缓存
    fuzzy_threshold: float = 0.8
    max_candidates: int = 5

class LocationService(IService):
    """地名匹配服务"""

    def __init__(self, config: Optional[LocationConfig] = None):
        self.config = config or LocationConfig(name="location_service")
        self.db_connection = None
        self.cache_client = None

    async def initialize(self) -> None:
        """初始化服务"""
        from services.database.db_service import DatabaseService
        from services.cache.cache_service import CacheService

        self.db_connection = DatabaseService(self.config.database_url)
        await self.db_connection.initialize()

        self.cache_client = CacheService()
        await self.cache_client.initialize()

    async def cleanup(self) -> None:
        """清理服务"""
        if self.db_connection:
            await self.db_connection.cleanup()
        if self.cache_client:
            await self.cache_client.cleanup()

    def health_check(self) -> bool:
        """健康检查"""
        return self.db_connection is not None and self.cache_client is not None

    async def match_location(self, query: str) -> Dict[str, Any]:
        """匹配地名"""
        # 1. 标准化查询
        normalized_query = self._normalize_query(query)

        # 2. 检查缓存
        cache_key = f"location:{normalized_query}"
        cached_result = await self.cache_client.get(cache_key)
        if cached_result:
            return cached_result

        # 3. 精确匹配
        exact_match = await self._exact_match(normalized_query)
        if exact_match:
            await self.cache_client.set(cache_key, exact_match, ttl=self.config.cache_ttl)
            return exact_match

        # 4. 模糊匹配
        fuzzy_matches = await self._fuzzy_match(normalized_query)
        if fuzzy_matches:
            best_match = fuzzy_matches[0]
            await self.cache_client.set(cache_key, best_match, ttl=self.config.cache_ttl)
            return best_match

        # 5. 无法匹配
        raise Exception(f"Location not found: {query}")

    def _normalize_query(self, query: str) -> str:
        """标准化查询字符串"""
        # 移除多余空格，转换为小写
        return " ".join(query.strip().lower().split())

    async def _exact_match(self, query: str) -> Optional[Dict[str, Any]]:
        """精确匹配"""
        sql = """
        SELECT name, country, admin1, admin2, latitude, longitude, population
        FROM locations
        WHERE LOWER(name) = ? OR LOWER(name || ', ' || country) = ?
        ORDER BY population DESC
        LIMIT 1
        """
        results = await self.db_connection.fetch_all(sql, [query, query])
        return self._format_location_result(results[0]) if results else None

    async def _fuzzy_match(self, query: str) -> List[Dict[str, Any]]:
        """模糊匹配"""
        sql = """
        SELECT name, country, admin1, admin2, latitude, longitude, population,
               similarity(LOWER(name), ?) as similarity_score
        FROM locations
        WHERE similarity(LOWER(name), ?) > ?
        ORDER BY similarity_score DESC, population DESC
        LIMIT ?
        """
        results = await self.db_connection.fetch_all(
            sql,
            [query, query, self.config.fuzzy_threshold, self.config.max_candidates]
        )
        return [self._format_location_result(row) for row in results]

    def _format_location_result(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """格式化地名结果"""
        return {
            "name": row["name"],
            "country": row["country"],
            "admin1": row.get("admin1"),
            "admin2": row.get("admin2"),
            "coordinates": {
                "latitude": row["latitude"],
                "longitude": row["longitude"]
            },
            "population": row.get("population", 0),
            "confidence": row.get("similarity_score", 1.0)
        }
```

### 3. 缓存服务 (CacheService)

**功能描述**: 提供高性能缓存功能

**接口定义**:
```python
from typing import Any, Optional, List
from core.interfaces import IService, ServiceConfig

class CacheConfig(ServiceConfig):
    """缓存服务配置"""
    redis_url: str
    default_ttl: int = 3600
    max_connections: int = 10
    key_prefix: str = "langchain:"

class CacheService(IService):
    """缓存服务"""

    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig(name="cache_service")
        self.redis_client = None

    async def initialize(self) -> None:
        """初始化服务"""
        import redis.asyncio as redis

        self.redis_client = redis.from_url(
            self.config.redis_url,
            max_connections=self.config.max_connections,
            decode_responses=True
        )

        # 测试连接
        await self.redis_client.ping()

    async def cleanup(self) -> None:
        """清理服务"""
        if self.redis_client:
            await self.redis_client.close()

    def health_check(self) -> bool:
        """健康检查"""
        return self.redis_client is not None

    def _make_key(self, key: str) -> str:
        """生成缓存键"""
        return f"{self.config.key_prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if not self.redis_client:
            return None

        cache_key = self._make_key(key)
        try:
            value = await self.redis_client.get(cache_key)
            if value:
                # 反序列化
                import json
                return json.loads(value)
        except Exception as e:
            print(f"Cache get error for key {key}: {e}")

        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        if not self.redis_client:
            return False

        cache_key = self._make_key(key)
        ttl = ttl or self.config.default_ttl

        try:
            import json
            serialized_value = json.dumps(value, ensure_ascii=False)
            await self.redis_client.setex(cache_key, ttl, serialized_value)
            return True
        except Exception as e:
            print(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        if not self.redis_client:
            return False

        cache_key = self._make_key(key)
        try:
            await self.redis_client.delete(cache_key)
            return True
        except Exception as e:
            print(f"Cache delete error for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        if not self.redis_client:
            return False

        cache_key = self._make_key(key)
        try:
            return bool(await self.redis_client.exists(cache_key))
        except Exception as e:
            print(f"Cache exists error for key {key}: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的缓存"""
        if not self.redis_client:
            return 0

        cache_pattern = self._make_key(pattern)
        try:
            keys = await self.redis_client.keys(cache_pattern)
            if keys:
                return await self.redis_client.delete(*keys)
        except Exception as e:
            print(f"Cache clear pattern error for pattern {pattern}: {e}")

        return 0
```

### 4. 数据库服务 (DatabaseService)

**功能描述**: 提供数据库连接和操作功能

**接口定义**:
```python
from typing import List, Dict, Any, Optional
from core.interfaces import IService, ServiceConfig

class DatabaseConfig(ServiceConfig):
    """数据库服务配置"""
    database_url: str
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30

class DatabaseService(IService):
    """数据库服务"""

    def __init__(self, database_url: str, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig(
            name="database_service",
            database_url=database_url
        )
        self.engine = None
        self.session_factory = None

    async def initialize(self) -> None:
        """初始化服务"""
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

        self.engine = create_async_engine(
            self.config.database_url,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            pool_timeout=self.config.pool_timeout
        )

        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def cleanup(self) -> None:
        """清理服务"""
        if self.engine:
            await self.engine.dispose()

    def health_check(self) -> bool:
        """健康检查"""
        return self.engine is not None and self.session_factory is not None

    async def execute_query(self, query: str, params: Optional[List] = None) -> List[Dict[str, Any]]:
        """执行查询"""
        async with self.session_factory() as session:
            try:
                result = await session.execute(text(query), params or [])
                return [dict(row._mapping) for row in result]
            except Exception as e:
                await session.rollback()
                raise e

    async def execute_non_query(self, query: str, params: Optional[List] = None) -> int:
        """执行非查询操作"""
        async with self.session_factory() as session:
            try:
                result = await session.execute(text(query), params or [])
                await session.commit()
                return result.rowcount
            except Exception as e:
                await session.rollback()
                raise e

    async def fetch_one(self, query: str, params: Optional[List] = None) -> Optional[Dict[str, Any]]:
        """获取单条记录"""
        results = await self.execute_query(query, params)
        return results[0] if results else None

    async def fetch_all(self, query: str, params: Optional[List] = None) -> List[Dict[str, Any]]:
        """获取所有记录"""
        return await self.execute_query(query, params)
```

## 服务编排

### 1. 服务管理器 (ServiceManager)

```python
from typing import Dict, List, Type
from core.interfaces import IService

class ServiceManager:
    """服务管理器"""

    def __init__(self):
        self._services: Dict[str, IService] = {}
        self._service_classes: Dict[str, Type[IService]] = {}

    def register_service(self, name: str, service: IService) -> None:
        """注册服务实例"""
        self._services[name] = service

    def register_service_class(self, name: str, service_class: Type[IService]) -> None:
        """注册服务类"""
        self._service_classes[name] = service_class

    async def initialize_all(self) -> None:
        """初始化所有服务"""
        init_tasks = []

        # 初始化已注册的服务实例
        for service in self._services.values():
            init_tasks.append(service.initialize())

        # 创建并初始化服务类实例
        for name, service_class in self._service_classes.items():
            if name not in self._services:
                service = service_class()
                self._services[name] = service
                init_tasks.append(service.initialize())

        if init_tasks:
            await asyncio.gather(*init_tasks, return_exceptions=True)

    async def cleanup_all(self) -> None:
        """清理所有服务"""
        cleanup_tasks = []
        for service in self._services.values():
            cleanup_tasks.append(service.cleanup())

        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)

    def get_service(self, name: str) -> Optional[IService]:
        """获取服务"""
        return self._services.get(name)

    async def health_check_all(self) -> Dict[str, bool]:
        """检查所有服务健康状态"""
        health_status = {}
        for name, service in self._services.items():
            try:
                health_status[name] = service.health_check()
            except Exception:
                health_status[name] = False
        return health_status
```

### 2. 服务依赖注入

```python
from typing import Any, Dict, Optional

class ServiceContainer:
    """服务容器"""

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, callable] = {}
        self._singletons: Dict[str, bool] = {}

    def register(self, name: str, factory: callable, singleton: bool = True) -> None:
        """注册服务工厂"""
        self._factories[name] = factory
        self._singletons[name] = singleton

    def get(self, name: str) -> Any:
        """获取服务"""
        if name in self._services:
            return self._services[name]

        if name not in self._factories:
            raise ValueError(f"Service not registered: {name}")

        service = self._factories[name]()

        if self._singletons[name]:
            self._services[name] = service

        return service

    def inject(self, service_name: str):
        """依赖注入装饰器"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                service = self.get(service_name)
                return func(service, *args, **kwargs)
            return wrapper
        return decorator
```

## 监控和日志

### 1. 服务监控

```python
import time
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class ServiceMetrics:
    """服务指标"""
    request_count: int = 0
    error_count: int = 0
    avg_response_time: float = 0.0
    last_error: Optional[str] = None
    uptime: float = 0.0

class ServiceMonitor:
    """服务监控器"""

    def __init__(self):
        self._metrics: Dict[str, ServiceMetrics] = {}

    def record_request(self, service_name: str, response_time: float, success: bool, error: Optional[str] = None) -> None:
        """记录请求"""
        if service_name not in self._metrics:
            self._metrics[service_name] = ServiceMetrics()

        metrics = self._metrics[service_name]
        metrics.request_count += 1

        if not success:
            metrics.error_count += 1
            metrics.last_error = error

        # 更新平均响应时间
        total_requests = metrics.request_count
        metrics.avg_response_time = (
            (metrics.avg_response_time * (total_requests - 1) + response_time) / total_requests
        )

    def get_metrics(self, service_name: str) -> Optional[ServiceMetrics]:
        """获取服务指标"""
        return self._metrics.get(service_name)

    def get_all_metrics(self) -> Dict[str, ServiceMetrics]:
        """获取所有服务指标"""
        return self._metrics.copy()
```

## 配置管理

### 1. 服务配置文件

```yaml
# services_config.yaml
services:
  weather_service:
    enabled: true
    config:
      api_key: "${WEATHER_API_KEY}"
      base_url: "https://api.openweathermap.org/data/2.5"
      cache_ttl: 300
      max_requests_per_hour: 1000
      timeout: 10

  location_service:
    enabled: true
    config:
      database_url: "${DATABASE_URL}"
      cache_ttl: 3600
      fuzzy_threshold: 0.8
      max_candidates: 5

  cache_service:
    enabled: true
    config:
      redis_url: "${REDIS_URL}"
      default_ttl: 3600
      max_connections: 10
      key_prefix: "langchain:"

  database_service:
    enabled: true
    config:
      database_url: "${DATABASE_URL}"
      pool_size: 5
      max_overflow: 10
      pool_timeout: 30
```

## 测试要求

### 1. 单元测试

```python
import pytest
from services.weather_service import WeatherService

class TestWeatherService:
    """天气服务测试"""

    @pytest.fixture
    async def service(self):
        """测试服务实例"""
        config = WeatherConfig(
            api_key="test_key",
            cache_ttl=60
        )
        service = WeatherService(config)
        await service.initialize()
        yield service
        await service.cleanup()

    @pytest.mark.asyncio
    async def test_get_weather_success(self, service):
        """测试获取天气成功"""
        with pytest.mock.patch.object(service, '_fetch_weather') as mock_fetch:
            mock_fetch.return_value = {"temperature": 20, "description": "晴天"}

            result = await service.get_weather("北京")
            assert result["temperature"] == 20
            assert result["description"] == "晴天"

    def test_health_check(self, service):
        """测试健康检查"""
        assert service.health_check() is True
```

## 部署要求

### 1. 容器化部署

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY services/ ./services/
COPY core/ ./core/

EXPOSE 8000
CMD ["python", "-m", "services.main"]
```

### 2. 环境变量配置

```bash
# .env
WEATHER_API_KEY=your_weather_api_key
DATABASE_URL=postgresql://user:password@localhost/dbname
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
```