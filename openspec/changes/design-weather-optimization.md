# 天气优化全国覆盖 - 设计文档

## 系统架构设计

### 整体架构图

```
用户查询 → 智能体 → get_weather工具 → 增强的天气服务 → 天气API
                    ↓
            地名解析器 → 坐标数据库 → 缓存层 → 彩云天气API
                    ↓
            天气数据 ← 数据格式化 ← 错误处理 ← 降级机制
```

### 核心组件设计

#### 1. CityCoordinateDB 类

```python
class CityCoordinateDB:
    """中国行政区划坐标数据库查询类"""

    def __init__(self, db_path: str = "data/admin_divisions.db"):
        self.db_path = db_path
        self.connection = None
        self._init_connection()

    def get_coordinates(self, place_name: str) -> tuple[float, float] | None:
        """
        获取地名对应的经纬度坐标

        Args:
            place_name: 地名（支持省、市、县、乡各级）

        Returns:
            (经度, 纬度) 或 None
        """

    def search_place(self, place_name: str, limit: int = 10) -> list[dict]:
        """
        搜索匹配的地名

        Returns:
            匹配结果列表，包含坐标和行政区划信息
        """

    def get_administrative_info(self, place_name: str) -> dict | None:
        """
        获取行政区划详细信息

        Returns:
            包含省、市、县、乡层级信息的字典
        """
```

#### 2. 智能地名匹配器

```python
class PlaceNameMatcher:
    """智能地名匹配器"""

    def __init__(self, coordinate_db: CityCoordinateDB):
        self.db = coordinate_db
        self.cache = {}  # 简单内存缓存

    def match_place(self, place_name: str) -> dict | None:
        """
        智能匹配地名，支持多种匹配策略

        1. 精确匹配
        2. 模糊匹配（编辑距离）
        3. 层级匹配
        4. 别名匹配
        """

    def _exact_match(self, place_name: str) -> dict | None:
        """精确匹配"""

    def _fuzzy_match(self, place_name: str, threshold: float = 0.8) -> dict | None:
        """模糊匹配"""

    def _hierarchical_match(self, place_name: str) -> dict | None:
        """层级匹配"""

    def _alias_match(self, place_name: str) -> dict | None:
        """别名匹配"""
```

#### 3. 增强的天气服务

```python
class EnhancedCaiyunWeatherService(CaiyunWeatherService):
    """增强的彩云天气服务，支持全国地区查询"""

    def __init__(self, api_key: str | None = None):
        super().__init__(api_key)
        self.coordinate_db = CityCoordinateDB()
        self.place_matcher = PlaceNameMatcher(self.coordinate_db)
        self.cache = WeatherCache()

    def get_weather(self, city: str) -> tuple[WeatherData, str]:
        """
        获取天气信息，支持全国地区查询

        Args:
            city: 城市或地区名称（支持各级行政区划）

        Returns:
            (天气数据, 数据来源说明)
        """
        # 1. 检查缓存
        cached_result = self.cache.get(city)
        if cached_result:
            return cached_result

        # 2. 地名匹配和坐标获取
        place_info = self.place_matcher.match_place(city)
        if not place_info:
            # 降级到原有逻辑
            return super().get_weather(city)

        # 3. 调用天气API
        coordinates = place_info['coordinates']
        weather_data = self._fetch_weather_by_coordinates(coordinates)

        # 4. 缓存结果
        self.cache.set(city, (weather_data, place_info['source_description']))

        return weather_data, place_info['source_description']
```

#### 4. 缓存系统设计

```python
class WeatherCache:
    """天气数据缓存系统"""

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self.memory_cache = LRUCache(max_size)
        self.cache_file = "data/weather_cache.json"
        self._load_cache()

    def get(self, key: str) -> Any:
        """获取缓存数据"""

    def set(self, key: str, value: Any):
        """设置缓存数据"""

    def _load_cache(self):
        """从文件加载缓存"""

    def _save_cache(self):
        """保存缓存到文件"""
```

## 数据库设计

### 行政区划数据库表结构

```sql
-- 主要表结构（基于Administrative-divisions-of-China）
CREATE TABLE regions (
    id INTEGER PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,      -- 行政区划代码
    name TEXT NOT NULL,             -- 名称
    parent_code TEXT,               -- 上级行政区划代码
    level INTEGER NOT NULL,         -- 行政级别 (1:省, 2:市, 3:县, 4:乡)
    longitude REAL,                 -- 经度
    latitude REAL,                  -- 纬度
    pinyin TEXT,                    -- 拼音
    aliases TEXT,                   -- 别名（JSON格式）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引优化
CREATE INDEX idx_regions_name ON regions(name);
CREATE INDEX idx_regions_pinyin ON regions(pinyin);
CREATE INDEX idx_regions_parent_code ON regions(parent_code);
CREATE INDEX idx_regions_level ON regions(level);
CREATE INDEX idx_regions_coordinates ON regions(longitude, latitude);
```

### 数据查询示例

```sql
-- 查询某个省份下的所有城市
SELECT * FROM regions
WHERE parent_code = (SELECT code FROM regions WHERE name = '北京市' AND level = 1)
AND level = 2;

-- 模糊搜索地名
SELECT * FROM regions
WHERE name LIKE '%朝阳%'
OR pinyin LIKE '%chaoyang%'
OR aliases LIKE '%朝阳%';

-- 获取完整的行政区划层级
WITH RECURSIVE admin_tree AS (
    SELECT code, name, level, parent_code, longitude, latitude
    FROM regions WHERE name = '朝阳区'
    UNION ALL
    SELECT r.code, r.name, r.level, r.parent_code, r.longitude, r.latitude
    FROM regions r
    JOIN admin_tree a ON r.code = a.parent_code
)
SELECT * FROM admin_tree ORDER BY level;
```

## 匹配算法设计

### 1. 匹配策略优先级

```
1. 精确匹配（权重: 1.0）
   - 完全相同的地名
   - 考虑行政区划层级

2. 拼音匹配（权重: 0.9）
   - 拼音完全匹配
   - 支持声调

3. 模糊匹配（权重: 0.8）
   - 编辑距离计算
   - 相似度阈值: 0.8

4. 包含匹配（权重: 0.7）
   - 地名包含查询词
   - 查询词包含地名

5. 别名匹配（权重: 0.9）
   - 预定义别名表
   - 常见简称和俗称
```

### 2. 智能匹配流程

```python
def smart_match_place(place_name: str) -> dict | None:
    """智能地名匹配主流程"""

    # 1. 预处理
    normalized_name = normalize_place_name(place_name)

    # 2. 缓存检查
    cached_result = check_cache(normalized_name)
    if cached_result:
        return cached_result

    # 3. 多策略匹配
    candidates = []

    # 精确匹配
    exact_results = exact_match(normalized_name)
    candidates.extend([(r, 1.0) for r in exact_results])

    # 拼音匹配
    pinyin_results = pinyin_match(normalized_name)
    candidates.extend([(r, 0.9) for r in pinyin_results])

    # 模糊匹配
    fuzzy_results = fuzzy_match(normalized_name, threshold=0.8)
    candidates.extend([(r, 0.8 * r['similarity']) for r in fuzzy_results])

    # 别名匹配
    alias_results = alias_match(normalized_name)
    candidates.extend([(r, 0.9) for r in alias_results])

    # 4. 结果排序和选择
    best_match = select_best_match(candidates)

    # 5. 缓存结果
    if best_match:
        cache_result(normalized_name, best_match)

    return best_match
```

### 3. 层级解析设计

```python
def parse_hierarchical_place(place_name: str) -> list[dict]:
    """解析层级地名"""

    # 示例: "北京市朝阳区三里屯"
    # 解析为: [北京市, 朝阳区, 三里屯]

    # 1. 分词处理
    segments = segment_place_name(place_name)

    # 2. 逐级匹配
    results = []
    current_context = None

    for segment in segments:
        # 在当前上下文中查找
        if current_context:
            match = find_in_context(segment, current_context)
        else:
            match = find_nationally(segment)

        if match:
            results.append(match)
            current_context = match
        else:
            # 无法匹配的段落，尝试模糊匹配
            fuzzy_match = fuzzy_find_in_context(segment, current_context)
            if fuzzy_match:
                results.append(fuzzy_match)

    return results
```

## 性能优化设计

### 1. 缓存策略

```python
# 多级缓存架构
class MultiLevelCache:
    def __init__(self):
        self.l1_cache = {}      # 内存缓存 (最快)
        self.l2_cache = {}      # 进程缓存 (快)
        self.l3_cache = FileCache()  # 文件缓存 (中等)

    def get(self, key: str):
        # L1 -> L2 -> L3 -> Database -> API
        pass

    def set(self, key: str, value: Any):
        # 写入所有级别
        pass
```

### 2. 数据库查询优化

```sql
-- 使用预编译语句
PREPARE get_coordinates AS
SELECT longitude, latitude FROM regions
WHERE name = ? OR pinyin = ? LIMIT 1;

-- 批量查询优化
SELECT * FROM regions
WHERE name IN (?, ?, ?, ?)
ORDER BY level, name;
```

### 3. 并发处理设计

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncWeatherService:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)

    async def get_weather_batch(self, places: list[str]) -> list[WeatherData]:
        """批量并发查询天气"""
        tasks = [
            self.get_weather_async(place)
            for place in places
        ]
        return await asyncio.gather(*tasks)

    async def get_weather_async(self, place: str) -> WeatherData:
        """异步查询天气"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self.get_weather_sync, place
        )
```

## 错误处理设计

### 1. 分层错误处理

```python
class WeatherServiceError(Exception):
    """天气服务基础异常"""
    pass

class CoordinateNotFoundError(WeatherServiceError):
    """坐标未找到异常"""
    pass

class APIQuotaExceededError(WeatherServiceError):
    """API配额超限异常"""
    pass

class NetworkError(WeatherServiceError):
    """网络连接异常"""
    pass

# 错误处理策略
def handle_weather_query_error(error: Exception, place: str) -> tuple[WeatherData, str]:
    """统一错误处理策略"""

    if isinstance(error, CoordinateNotFoundError):
        # 降级到原有15个城市
        return fallback_to_major_cities(place)

    elif isinstance(error, APIQuotaExceededError):
        # 使用模拟数据
        return generate_mock_weather_data(place)

    elif isinstance(error, NetworkError):
        # 检查缓存
        cached = check_cache(place)
        if cached:
            return cached
        else:
            return generate_mock_weather_data(place)

    else:
        # 未知错误，使用模拟数据
        log_error(error)
        return generate_mock_weather_data(place)
```

### 2. 降级机制设计

```python
class FallbackStrategy:
    """降级策略实现"""

    def __init__(self):
        self.major_cities = [
            "北京", "上海", "广州", "深圳", "杭州",
            "成都", "西安", "武汉", "南京", "重庆",
            "天津", "苏州", "青岛", "大连", "厦门"
        ]

    def fallback_to_major_city(self, place: str) -> tuple[WeatherData, str]:
        """降级到主要城市"""
        # 1. 尝试省份匹配
        province_match = self._match_province(place)
        if province_match:
            return self._get_major_city_weather(province_match)

        # 2. 模糊匹配主要城市
        fuzzy_match = self._fuzzy_match_major_city(place)
        if fuzzy_match:
            return self._get_major_city_weather(fuzzy_match)

        # 3. 默认返回北京天气
        return self._get_major_city_weather("北京")

    def generate_mock_data(self, place: str) -> tuple[WeatherData, str]:
        """生成模拟天气数据"""
        import random
        return WeatherData(
            temperature=random.uniform(-10, 35),
            apparent_temperature=random.uniform(-12, 37),
            humidity=random.randint(30, 90),
            pressure=random.uniform(990, 1020),
            wind_speed=random.uniform(0, 30),
            wind_direction=random.uniform(0, 360),
            condition="模拟数据"
        ), "模拟数据（降级机制）"
```

## 测试策略设计

### 1. 测试金字塔

```
E2E测试 (10%)
├── 完整的智能体天气查询流程
└── 真实API调用测试

集成测试 (30%)
├── 天气服务集成测试
├── 数据库集成测试
├── 缓存集成测试
└── 错误处理集成测试

单元测试 (60%)
├── CityCoordinateDB测试
├── PlaceNameMatcher测试
├── 缓存系统测试
├── 匹配算法测试
└── 工具函数测试
```

### 2. 性能测试设计

```python
class PerformanceTest:
    """性能测试套件"""

    def test_query_latency(self):
        """测试查询延迟"""
        places = ["北京市", "上海市", "广州市", "深圳市", "杭州市"]

        for place in places:
            start_time = time.time()
            result = self.weather_service.get_weather(place)
            end_time = time.time()

            assert end_time - start_time < 2.0, f"{place}查询超时"

    def test_concurrent_queries(self):
        """测试并发查询"""
        import concurrent.futures

        places = [f"城市{i}" for i in range(100)]

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(self.weather_service.get_weather, place)
                for place in places
            ]

            results = [f.result() for f in futures]
            assert len(results) == 100

    def test_cache_hit_rate(self):
        """测试缓存命中率"""
        # 预热缓存
        places = ["北京市", "上海市", "广州市"]
        for place in places:
            self.weather_service.get_weather(place)

        # 测试缓存命中
        hits = 0
        for _ in range(100):
            place = random.choice(places)
            result = self.weather_service.get_weather(place)
            if "缓存" in result[1]:
                hits += 1

        hit_rate = hits / 100
        assert hit_rate > 0.8, f"缓存命中率过低: {hit_rate}"
```

这个设计文档详细描述了天气优化全国覆盖功能的完整技术方案，包括系统架构、核心组件设计、数据库设计、匹配算法、性能优化、错误处理和测试策略等各个方面。