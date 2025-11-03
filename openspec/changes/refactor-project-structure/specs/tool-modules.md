# 工具模块规范

## 模块概述
工具模块定义了智能体系统中所有可执行工具的规范和实现。每个工具都是独立的模块，负责特定的功能领域。

## 工具分类

### 1. 时间工具 (TimeTool)

**功能描述**: 提供时间查询和计算功能

**接口定义**:
```python
from datetime import datetime, timedelta
from typing import Optional
from core.interfaces import ITool, ToolMetadata, ToolResult

class TimeTool(ITool):
    """时间工具"""

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="time_tool",
            description="提供时间查询和计算功能",
            version="1.0.0",
            author="langchain-learning",
            tags=["time", "datetime", "utility"]
        )

    def validate_input(self, **kwargs) -> bool:
        """验证输入参数"""
        # 支持的操作类型: current_time, add_time, subtract_time, format_time
        operation = kwargs.get('operation')
        return operation in ['current_time', 'add_time', 'subtract_time', 'format_time']

    async def execute(self, **kwargs) -> ToolResult:
        """执行时间操作"""
        operation = kwargs.get('operation')

        if operation == 'current_time':
            return await self._get_current_time(**kwargs)
        elif operation == 'add_time':
            return await self._add_time(**kwargs)
        elif operation == 'subtract_time':
            return await self._subtract_time(**kwargs)
        elif operation == 'format_time':
            return await self._format_time(**kwargs)

        return ToolResult(
            success=False,
            error=f"Unsupported operation: {operation}"
        )
```

**支持的操作**:
- `current_time`: 获取当前时间
- `add_time`: 时间加法
- `subtract_time`: 时间减法
- `format_time`: 时间格式化

### 2. 数学工具 (MathTool)

**功能描述**: 提供数学计算功能

**接口定义**:
```python
import math
from typing import Union, List
from core.interfaces import ITool, ToolMetadata, ToolResult

class MathTool(ITool):
    """数学计算工具"""

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="math_tool",
            description="提供数学计算功能",
            version="1.0.0",
            author="langchain-learning",
            tags=["math", "calculation", "utility"]
        )

    def validate_input(self, **kwargs) -> bool:
        """验证输入参数"""
        operation = kwargs.get('operation')
        return operation in ['add', 'subtract', 'multiply', 'divide', 'power', 'sqrt', 'sin', 'cos', 'tan']

    async def execute(self, **kwargs) -> ToolResult:
        """执行数学计算"""
        operation = kwargs.get('operation')

        if operation == 'add':
            return await self._add(**kwargs)
        elif operation == 'subtract':
            return await self._subtract(**kwargs)
        elif operation == 'multiply':
            return await self._multiply(**kwargs)
        elif operation == 'divide':
            return await self._divide(**kwargs)
        elif operation == 'power':
            return await self._power(**kwargs)
        elif operation == 'sqrt':
            return await self._sqrt(**kwargs)
        elif operation == 'sin':
            return await self._sin(**kwargs)
        elif operation == 'cos':
            return await self._cos(**kwargs)
        elif operation == 'tan':
            return await self._tan(**kwargs)

        return ToolResult(
            success=False,
            error=f"Unsupported operation: {operation}"
        )
```

**支持的操作**:
- `add`, `subtract`, `multiply`, `divide`: 基础四则运算
- `power`: 幂运算
- `sqrt`: 平方根
- `sin`, `cos`, `tan`: 三角函数

### 3. 天气工具 (WeatherTool)

**功能描述**: 提供天气查询功能

**接口定义**:
```python
from typing import Dict, Any, Optional
from core.interfaces import ITool, ToolMetadata, ToolResult

class WeatherTool(ITool):
    """天气查询工具"""

    def __init__(self):
        from services.weather_service import WeatherService
        self.weather_service = WeatherService()

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="weather_tool",
            description="提供天气查询功能",
            version="1.0.0",
            author="langchain-learning",
            tags=["weather", "forecast", "api"],
            dependencies=["weather_service"]
        )

    def validate_input(self, **kwargs) -> bool:
        """验证输入参数"""
        location = kwargs.get('location')
        return isinstance(location, str) and len(location.strip()) > 0

    async def execute(self, **kwargs) -> ToolResult:
        """查询天气信息"""
        location = kwargs.get('location')

        try:
            weather_data = await self.weather_service.get_weather(location)
            return ToolResult(
                success=True,
                data=weather_data,
                metadata={"location": location}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Weather query failed: {str(e)}"
            )
```

**支持的操作**:
- 基于地点的天气查询
- 支持地名智能匹配
- 缓存机制优化

### 4. 搜索工具 (SearchTool)

**功能描述**: 提供信息搜索功能

**接口定义**:
```python
from typing import List, Dict, Any
from core.interfaces import ITool, ToolMetadata, ToolResult

class SearchTool(ITool):
    """信息搜索工具"""

    def __init__(self):
        from services.search_service import SearchService
        self.search_service = SearchService()

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="search_tool",
            description="提供信息搜索功能",
            version="1.0.0",
            author="langchain-learning",
            tags=["search", "information", "api"],
            dependencies=["search_service"]
        )

    def validate_input(self, **kwargs) -> bool:
        """验证输入参数"""
        query = kwargs.get('query')
        return isinstance(query, str) and len(query.strip()) > 0

    async def execute(self, **kwargs) -> ToolResult:
        """执行信息搜索"""
        query = kwargs.get('query')
        max_results = kwargs.get('max_results', 5)

        try:
            search_results = await self.search_service.search(query, max_results)
            return ToolResult(
                success=True,
                data=search_results,
                metadata={"query": query, "max_results": max_results}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Search failed: {str(e)}"
            )
```

**支持的操作**:
- 通用信息搜索
- 可配置返回结果数量
- 支持多种搜索源

## 工具注册机制

### 1. 工具注册器 (ToolRegistry)

```python
from typing import Dict, List, Type
from core.interfaces import ITool

class ToolRegistry:
    """工具注册器"""

    def __init__(self):
        self._tools: Dict[str, ITool] = {}
        self._tool_classes: Dict[str, Type[ITool]] = {}

    def register(self, tool: ITool) -> None:
        """注册工具实例"""
        self._tools[tool.metadata.name] = tool

    def register_class(self, tool_class: Type[ITool]) -> None:
        """注册工具类"""
        # 创建临时实例获取元数据
        temp_instance = tool_class()
        self._tool_classes[temp_instance.metadata.name] = tool_class

    def get_tool(self, name: str) -> Optional[ITool]:
        """获取工具实例"""
        if name in self._tools:
            return self._tools[name]
        elif name in self._tool_classes:
            # 动态创建实例
            tool = self._tool_classes[name]()
            self._tools[name] = tool
            return tool
        return None

    def list_tools(self) -> List[ToolMetadata]:
        """列出所有工具"""
        tools = list(self._tools.values())
        classes = list(self._tool_classes.values())

        all_tools = tools + [cls() for cls in classes]
        return [tool.metadata for tool in all_tools]

    def unregister(self, name: str) -> bool:
        """注销工具"""
        removed = False
        if name in self._tools:
            del self._tools[name]
            removed = True
        if name in self._tool_classes:
            del self._tool_classes[name]
            removed = True
        return removed
```

### 2. 自动发现机制

```python
import importlib
import pkgutil
from typing import List

class ToolDiscovery:
    """工具自动发现"""

    @staticmethod
    def discover_tools(package_name: str) -> List[Type[ITool]]:
        """自动发现指定包中的工具"""
        tools = []

        try:
            package = importlib.import_module(package_name)

            for _, module_name, _ in pkgutil.iter_modules(package.__path__):
                module = importlib.import_module(f"{package_name}.{module_name}")

                # 查找模块中的工具类
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and
                        issubclass(attr, ITool) and
                        attr != ITool):
                        tools.append(attr)

        except ImportError as e:
            print(f"Failed to discover tools in {package_name}: {e}")

        return tools
```

## 工具配置规范

### 1. 工具配置文件格式

```yaml
# tools_config.yaml
tools:
  time_tool:
    enabled: true
    config:
      timezone: "Asia/Shanghai"
      date_format: "%Y-%m-%d %H:%M:%S"

  math_tool:
    enabled: true
    config:
      precision: 10

  weather_tool:
    enabled: true
    config:
      api_key: "${WEATHER_API_KEY}"
      cache_ttl: 300
      max_requests_per_hour: 100

  search_tool:
    enabled: true
    config:
      search_engine: "default"
      max_results: 10
      timeout: 30
```

### 2. 配置加载机制

```python
import yaml
import os
from typing import Dict, Any

class ToolConfigLoader:
    """工具配置加载器"""

    def __init__(self, config_path: str = "tools_config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not os.path.exists(self.config_path):
            return {"tools": {}}

        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def get_tool_config(self, tool_name: str) -> Dict[str, Any]:
        """获取工具配置"""
        tools_config = self.config.get("tools", {})
        return tools_config.get(tool_name, {})

    def is_tool_enabled(self, tool_name: str) -> bool:
        """检查工具是否启用"""
        tool_config = self.get_tool_config(tool_name)
        return tool_config.get("enabled", True)
```

## 测试要求

### 1. 单元测试结构

```python
import pytest
from tools.time_tool import TimeTool

class TestTimeTool:
    """时间工具测试"""

    def setup_method(self):
        """测试前准备"""
        self.tool = TimeTool()

    @pytest.mark.asyncio
    async def test_get_current_time(self):
        """测试获取当前时间"""
        result = await self.tool.execute(operation="current_time")
        assert result.success
        assert result.data is not None

    def test_validate_input(self):
        """测试输入验证"""
        # 有效输入
        assert self.tool.validate_input(operation="current_time")

        # 无效输入
        assert not self.tool.validate_input(operation="invalid")

    @pytest.mark.asyncio
    async def test_add_time(self):
        """测试时间加法"""
        result = await self.tool.execute(
            operation="add_time",
            hours=1,
            minutes=30
        )
        assert result.success
        assert "1小时30分钟" in result.data
```

### 2. 集成测试

```python
import pytest
from core.registry import ToolRegistry
from tools.time_tool import TimeTool
from tools.math_tool import MathTool

class TestToolIntegration:
    """工具集成测试"""

    def setup_method(self):
        """测试前准备"""
        self.registry = ToolRegistry()
        self.registry.register_class(TimeTool)
        self.registry.register_class(MathTool)

    def test_tool_registration(self):
        """测试工具注册"""
        time_tool = self.registry.get_tool("time_tool")
        assert time_tool is not None

        math_tool = self.registry.get_tool("math_tool")
        assert math_tool is not None

    @pytest.mark.asyncio
    async def test_tool_execution(self):
        """测试工具执行"""
        time_tool = self.registry.get_tool("time_tool")
        result = await time_tool(operation="current_time")
        assert result.success
```

## 部署要求

### 1. 依赖管理
- 每个工具必须明确定义依赖关系
- 支持依赖版本约束
- 提供依赖冲突检测

### 2. 资源限制
- 工具执行必须有资源使用限制
- 支持超时控制
- 监控内存和CPU使用

### 3. 安全控制
- 工具必须有权限控制机制
- 支持输入输出过滤
- 记录工具执行日志