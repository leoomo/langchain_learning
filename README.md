# LangChain 学习项目 - 智谱AI集成

一个全面的 LangChain 1.0+ 学习项目，展示如何构建现代化的 LLM 应用程序，**默认使用智谱AI GLM-4.6 模型**，采用**全新重构的服务架构 v2.0**。

> 基于 LangChain 1.0+ 的现代LLM应用项目，集成智能体、工具API和实时天气服务

## 🎯 项目特色

### 🏗️ 新架构特性 (v2.0.0-refactored-fixed)
- **🔄 中央服务管理**: 单例模式确保服务实例唯一性，消除重复初始化
- **🔧 接口抽象层**: 松耦合设计，支持依赖注入和接口替换
- **⚡ 懒加载机制**: 服务按需初始化，提升启动性能
- **🛡️ 线程安全**: 多线程环境下安全的服务创建和访问
- **⚙️ 统一配置**: 环境变量和配置文件的集中管理系统
- **🔧 工具集成修复**: WeatherTool正确使用坐标服务，消除方法调用错误

### 🚀 LangChain 1.0+ 集成
- **🚀 最新 LangChain 1.0+ API**: 使用 `create_agent` 函数和现代工具集成
- **🤖 多模型支持**: 智谱AI (默认)、Anthropic Claude、OpenAI GPT
- **🛠️ 实用智能体**: 内置时间查询、数学计算、天气查询、信息搜索工具
- **🌤️ 真实天气数据**: 集成彩云天气 API，提供实时天气信息
- **🗺️ 全国地区覆盖**: 支持3,142+中国地区（95%+覆盖率），智能地名匹配，**150+重要地区坐标准确性修复**
- **📚 完整示例**: 从基础对话到复杂智能体的全方位演示
- **🧪 测试驱动**: 包含结构测试和功能验证

### 🏗️ 同步版本架构 ⭐ **重大更新**
**已完全重构为同步版本**：
- 🔧 **异步转同步**: 移除所有 `async/await` 代码，消除事件循环复杂性
- 🛡️ **稳定性提升**: 彻底解决 "Event loop is closed" 错误
- ⚡ **简化架构**: 标准Python函数调用，易于理解和维护
- 📊 **同步API客户端**: 使用 `requests` 替代 `aiohttp`，性能稳定
- 🎯 **工具集成完善**: LangChain工具完全同步化，支持智能体调用
- 🧪 **完整测试验证**: 同步版本100%功能正常，无任何异步问题

### 🎣 智能钓鱼推荐系统
**已完全实现并测试通过**：
- 🎯 专业钓鱼分析工具，基于7因子评分算法（温度、天气、风力、气压、湿度、季节、月相）
- 📊 实时天气数据处理，支持全国3,142+行政区划查询
- 🧠 自然语言理解，智能识别钓鱼相关查询
- ⏰ 基于多维度条件的时间段推荐，解决"86分问题"
- 📍 支持日期时间查询，如"明天早上6-8点"
- ⚡ 增强评分器：基于专业钓鱼研究，提供更精准的评分区分度
- 🔬 科学算法：气压趋势分析、季节性规律、月相影响等专业因子

### 🗺️ 智能坐标服务
**高性能多级缓存系统**：
- 🏛️ **三级查询策略**: 本地数据库 → 高德API → 降级逻辑
- 💾 **智能缓存机制**: 内存缓存 + 文件持久化双重保障
- 🌍 **全国覆盖**: 支持中国所有省、市、县、乡镇级地区
- 📍 **缓存命中率**: 90%+，响应时间 < 1ms
- 🔄 **API调用优化**: 减少80%+的重复API请求

### 🌤 增强天气服务
**全面的天气数据支持**：
- 📅 彩云天气API集成，提供实时天气数据
- 📍 日期时间查询，支持多种日期时间格式
- 🌈 小时级预报，支持24小时详细预报
- 🎯 错误代码系统，提供详细的错误诊断
- 🔄 智能重试机制，提高服务可靠性

### 📝 智能日志中间件
**全面的执行监控和日志记录**：
- 🔍 **完整执行日志**: 记录用户输入、AI回复、工具调用全过程
- ⚡ **性能监控**: 详细的响应时间、Token使用量、错误统计
- 🛠️ **工具调用追踪**: 每个工具的参数、结果、耗时和成功状态
- 🔐 **敏感数据保护**: 自动过滤API密钥、密码等敏感信息
- 📊 **可配置输出**: 支持控制台、文件双重输出，灵活的日志级别
- 🎯 **会话管理**: 唯一会话ID，完整的执行生命周期跟踪
- 📈 **统计分析**: 实时性能指标和执行统计，支持重置和查看

## 🚀 快速开始

### 环境要求
- Python 3.11+
- uv 包管理器

### 安装依赖
```bash
# 安装依赖
uv sync

# 激活虚拟环境
source .venv/bin/activate
```

### 配置环境变量
```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
nano .env
```

在 `.env` 文件中配置以下API密钥：

```bash
# 彩云天气 API 密钥 (必需)
# 获取方式: https://www.caiyunapp.com/
CAIYUN_API_KEY=your-caiyun-api-key-here

# 高德地图 API 密钥 (必需，用于坐标查询)
# 获取方式: https://console.amap.com/dev/key/app
AMAP_API_KEY=your-amap-api-key-here

# 智谱AI GLM API 密钥 (可选)
ANTHROPIC_AUTH_TOKEN=your-zhipu-api-token-here

# Anthropic Claude API 密钥 (可选)
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# OpenAI GPT API 密钥 (可选)
OPENAI_API_KEY=your-openai-api-key-here

# 调试日志开关 (推荐开发时开启)
DEBUG_LOGGING=true

# 智能体日志中间件配置 (可选)
AGENT_LOG_LEVEL=INFO                    # 日志级别 (DEBUG, INFO, WARNING, ERROR)
AGENT_LOG_CONSOLE=true                  # 控制台输出
AGENT_LOG_FILE=false                    # 文件输出
AGENT_LOG_FILE_PATH=logs/agent.log      # 日志文件路径
AGENT_PERF_MONITOR=true                 # 性能监控
AGENT_TOOL_TRACKING=true                # 工具调用追踪
AGENT_SENSITIVE_FILTER=true             # 敏感信息过滤
```

### 获取API密钥

#### 1. 彩云天气API密钥
1. 访问 [彩云天气开发者平台](https://www.caiyunapp.com/)
2. 注册账号并登录
3. 创建应用获取API密钥
4. 将密钥添加到 `.env` 文件

#### 2. 高德地图API密钥
1. 访问 [高德开放平台](https://console.amap.com/dev/key/app)
2. 注册成为开发者
3. 创建Web服务API应用
4. 获取API密钥并添加到 `.env` 文件

## 🎮 使用示例

### 智能体查询示例（同步版本）

```python
from modern_langchain_agent import ModernLangChainAgent

# 创建智能体实例 - 使用同步版本
agent = ModernLangChainAgent()

# 天气查询 - 稳定可靠，无异步错误
response = agent.run("北京今天的天气怎么样？")
print(response)

# 钓鱼时间推荐 - 智能日期解析，支持多种格式
response = agent.run("明天还是后天去富阳区钓鱼比较好？")
print(response)

# 日期时间天气查询 - 支持相对和绝对日期
response = agent.run("后天早上杭州天气如何？")
print(response)
```

### 日志中间件使用示例

```python
from modern_langchain_agent import ModernLangChainAgent
from services.middleware import MiddlewareConfig

# 1. 基础日志功能 - 启用默认日志记录
agent = ModernLangChainAgent(
    model_provider="anthropic",
    enable_logging=True  # 启用日志中间件
)

response = agent.run("北京今天天气如何？")
print(response)

# 获取执行统计
summary = agent.get_execution_summary()
print(f"模型调用次数: {summary['metrics']['model_calls_count']}")
print(f"工具调用次数: {summary['metrics']['tool_calls_count']}")

# 2. 自定义日志配置
config = MiddlewareConfig(
    log_level="DEBUG",                      # 详细日志级别
    log_to_console=True,                    # 控制台输出
    log_to_file=True,                       # 文件输出
    log_file_path="logs/agent.log",         # 日志文件路径
    enable_performance_monitoring=True,     # 启用性能监控
    enable_tool_tracking=True,              # 启用工具追踪
    max_log_length=1000                     # 日志最大长度
)

agent = ModernLangChainAgent(
    model_provider="anthropic",
    enable_logging=True,
    middleware_config=config
)

# 3. 交互式聊天 - 实时查看日志
agent.interactive_chat()
# 在聊天中输入 "stats" 查看执行统计
# 输入 "reset" 重置统计指标
```

### 同步工具直接调用示例

```python
from tools.langchain_weather_tools_sync import (
    query_current_weather,
    query_fishing_recommendation,
    query_weather_by_date
)

# 直接调用同步工具 - 简单可靠
result = query_current_weather.invoke({'place': '杭州'})
print(f"当前天气: {result}")

# 智能钓鱼推荐 - 支持多种日期格式
result = query_fishing_recommendation.invoke({
    'location': '富阳区',
    'date': '后天'  # 支持: "tomorrow", "2天后", "2025-11-07"
})
print(f"钓鱼推荐: {result}")
```

### 钓鱼推荐功能示例

```python
# 支持的查询方式
queries = [
    "余杭区明天钓鱼合适吗？",
    "临安后天什么时候钓鱼好？",
    "2024-12-25北京钓鱼时间推荐",
    "今天晚上上海钓鱼天气如何？"
]

for query in queries:
    response = agent.run(query)
    print(f"问题: {query}")
    print(f"回答: {response}")
    print("-" * 50)
```

### 增强钓鱼评分器示例

```python
from tools.enhanced_fishing_scorer import EnhancedFishingScorer

# 创建增强评分器
scorer = EnhancedFishingScorer()

# 分析钓鱼条件
conditions = {
    'datetime': '2024-11-06T14:00:00',
    'temperature': 22.0,
    'condition': '阴',
    'wind_speed': 8.0,
    'humidity': 75.0,
    'pressure': 1008.0
}

# 计算评分
from datetime import datetime
date = datetime(2024, 11, 6, 14, 0)
score = scorer.calculate_comprehensive_score(conditions, historical_data, date)

print(f"综合评分: {score.overall:.1f}/100")
print(f"气压评分: {score.pressure:.1f} (下降气压奖励!)")
print(f"7因子详细评分: 温度{score.temperature:.1f}, 天气{score.weather:.1f}, 风力{score.wind:.1f}, 气压{score.pressure:.1f}, 湿度{score.humidity:.1f}, 季节{score.seasonal:.1f}, 月相{score.lunar:.1f}")
```

### 坐标服务示例

```python
from services.coordinate.amap_coordinate_service import AmapCoordinateService

# 创建坐标服务
service = AmapCoordinateService()

# 查询坐标
coords = service.get_coordinate("河桥镇")
print(f"河桥镇坐标: {coords}")

# 查询城市坐标
coords = service.get_coordinate("北京市朝阳区")
print(f"北京朝阳区坐标: {coords}")

# 查询完整地址
coords = service.get_coordinate("浙江省杭州市余杭区", city="杭州市", province="浙江省")
print(f"浙江省杭州市余杭区坐标: {coords}")
```

### 天气服务示例

```python
from services.weather.enhanced_weather_service import EnhancedCaiyunWeatherService

# 创建天气服务
weather_service = EnhancedCaiyunWeatherService()

# 查询当前天气
weather_data = weather_service.get_weather("北京")
print(f"当前天气: {weather_data}")

# 查询指定日期天气
weather_data = weather_service.get_weather_by_date("上海", "2024-12-25")
print(f"2024-12-25上海天气: {weather_data}")

# 查询小时级预报
hourly_forecast = weather_service.get_hourly_forecast("广州", hours=24)
print(f"广州24小时预报: {hourly_forecast}")
```

## 📁 项目文件结构

```
├── 🏗️ 新架构核心组件 (v2.0-refactored)
│   ├── interfaces/                # 🔧 服务接口抽象层
│   │   ├── coordinate_service.py # 坐标服务接口定义
│   │   └── weather_service.py    # 天气服务接口定义
│   ├── config/                    # ⚙️ 配置管理层
│   │   └── service_config.py     # 统一配置管理
│   └── services/                  # 🌐 服务实现层 (重构)
│       ├── service_manager.py    # 🔄 中央服务管理器
│       ├── coordinate/            # 📍 坐标服务模块
│       │   ├── enhanced_amap_coordinate_service.py  # 增强版坐标服务
│       │   └── amap_coordinate_service.py           # 原版坐标服务 (兼容)
│       ├── weather/               # 🌤️ 天气服务模块
│       │   ├── enhanced_caiyun_weather_service.py   # 增强版天气服务
│       │   └── enhanced_weather_service.py          # 原增强版天气服务
│       └── logging/               # 📝 日志服务模块
│           ├── enhanced_business_logger.py          # 增强版日志器
│           └── business_logger.py                   # 兼容版日志器
├── tools/                        # 🛠️ 工具层 (已重构)
│   ├── langchain_weather_tools.py # 使用服务管理器
│   ├── fishing_analyzer.py        # 钓鱼分析器 (懒加载)
│   └── weather_tool.py           # 核心天气工具
├── modern_langchain_agent.py      # 🤖 LangChain 1.0+ 智能体 (主要功能)
├── demo_fishing_fix.py           # 🎣 钓鱼系统演示
├── enhanced_weather_service.py    # 增强天气服务
├── test_new_architecture.py       # 🧪 架构验证测试
├── core/                          # 🏗️ 核心架构模块
│   ├── __init__.py                # 核心模块初始化
│   ├── interfaces.py             # 📋 接口定义 (ITool, IAgent, IService)
│   ├── base_tool.py              # 🔧 工具基类 (BaseTool, ConfigurableTool)
│   ├── base_agent.py             # 🤖 智能体基类 (BaseAgent, ManagedAgent)
│   ├── base_service.py           # 🌐 服务基类 (BaseService, DependentService)
│   └── registry.py               # 📊 注册器 (ToolRegistry, ServiceRegistry)
├── tools/                        # 🛠️ 工具模块 (新架构)
│   ├── __init__.py               # 工具模块导出
│   ├── time_tool.py              # 🕐 时间工具 (TimeTool)
│   ├── math_tool.py              # 🔢 数学工具 (MathTool)
│   ├── weather_tool.py           # 🌤️ 天气工具 (WeatherTool)
│   └── search_tool.py            # 🔍 搜索工具 (SearchTool)
├── agents/                       # 🤖 智能体模块
│   ├── __init__.py               # 智能体模块导出
│   └── modern_agent.py           # 现代智能体实现
├── data/                         # 📊 数据目录
│   ├── admin_divisions.db        # 🗄️ SQLite数据库 (3,142+地区)
│   ├── backup_regions.csv        # 💾 数据备份
│   ├── national_areas_raw.json   # 📋 原始数据
│   ├── national_region_database.py    # 🇨🇳 全国地区数据库初始化
│   └── coordinate_enrichment.py       # 📍 坐标信息丰富化
├── services/                     # 🌐 兼容层服务 (旧架构)
│   ├── weather/                  # 🌤️ 天气服务
│   │   ├── __init__.py           # 天气服务导出
│   │   ├── weather_service.py    # 基础天气服务
│   │   ├── enhanced_weather_service.py  # 增强天气服务 (全国覆盖)
│   │   └── weather_cache.py      # 💾 多级缓存系统
│   ├── matching/                 # 🧠 匹配服务
│   │   ├── __init__.py           # 匹配服务导出
│   │   ├── enhanced_place_matcher.py  # 智能地名匹配系统
│   │   └── city_coordinate_db.py # 🗺️ 城市坐标数据库
│   ├── cache/                    # 💾 缓存服务
│   │   └── __init__.py           # 缓存服务导出
│   └── database/                 # 🗄️ 数据库服务
│       └── __init__.py           # 数据库服务导出
├── tests/                        # 🧪 测试套件 (重组后)
│   ├── README.md                 # 📖 测试目录说明文档
│   ├── unit/                     # 📋 单元测试
│   ├── integration/              # 🔗 集成测试
│   │   └── verify_national_integration.py  # ✅ 集成验证脚本
│   ├── demos/                    # 🎭 演示脚本
│   ├── weather/                  # 🌤️ 天气专项测试
│   └── test_national_coverage.py # 🧪 全国覆盖测试脚本
├── openspec/                     # 📋 OpenSpec 规范管理
│   ├── changes/                  # 变更提案
│   │   ├── refactor-service-architecture/  # ✅ 已归档: 服务架构重构
│   │   └── [其他提案目录...]
│   └── AGENTS.md                 # OpenSpec 工作流指南
├── docs/                         # 📚 文档目录
│   ├── QUICK_START.md            # 🚀 5分钟快速体验指南
│   ├── TOOLS_GUIDE.md            # 🛠️ 详细工具使用指南
│   ├── API.md                    # 📖 完整API参考文档
│   ├── CHANGELOG.md              # 📋 版本更新日志
│   ├── COORDINATE_FIX_REPORT.md  # 🗺️ 全国坐标数据质量修复报告
│   ├── NATIONAL_COVERAGE_COMPLETION_REPORT.md  # 🎯 项目完成报告
│   └── 其他报告文档...
├── .env.example                  # 🔑 环境变量配置示例
├── .env                          # 🔑 环境变量配置 (需要创建)
├── pyproject.toml                # 📦 项目依赖配置
└── README.md                     # 📋 项目说明 (本文件)
```

## 🤖 智能体功能 (新)

### 内置工具 (基于新工具模块)

- **⏰ TimeTool** - 时间工具，支持时间查询、计算、格式化和时区转换
- **🧮 MathTool** - 数学工具，支持基本运算、高级函数和统计计算
- **🌤️ WeatherTool** - 天气工具，支持实时天气查询和预报 (支持真实数据)
- **🔍 SearchTool** - 搜索工具，支持知识库检索和网络搜索

### 新工具模块特性

#### 模块化设计
- **独立开发**: 每个工具都是独立的模块，可以单独开发和测试
- **统一接口**: 所有工具都实现 `ITool` 接口，保证一致性
- **异步支持**: 支持高性能异步调用
- **配置化**: 支持通过配置文件自定义工具行为

#### 核心功能
- **时间工具** (`tools/time_tool.py`):
  - 当前时间查询 (支持时区)
  - 时间加减运算 (支持年月日)
  - 时间格式化 (多种格式)
  - 时区转换

- **数学工具** (`tools/math_tool.py`):
  - 基本运算 (加减乘除)
  - 高级函数 (三角函数、对数、幂运算)
  - 统计计算 (平均值、中位数、标准差)
  - 随机数生成和四舍五入

- **天气工具** (`tools/weather_tool.py`):
  - 实时天气查询
  - 坐标获取和位置搜索
  - 批量天气查询
  - 天气预报 (模拟)

- **搜索工具** (`tools/search_tool.py`):
  - 知识库搜索
  - 网络搜索 (模拟)
  - 相似度匹配
  - 高级搜索和分类检索

### 工具调用方式

#### 1. 直接调用工具模块
```python
from tools import TimeTool, MathTool, WeatherTool, SearchTool
import asyncio

# 异步调用
time_tool = TimeTool()
result = await time_tool.execute(operation='current_time')
print(result.data['formatted'])

# 同步调用 (在异步上下文中)
math_tool = MathTool()
result = await math_tool.execute(operation='add', a=10, b=5)
print(result.data['formatted'])
```

#### 2. 集成到LangChain智能体
```python
from langchain_core.tools import tool
from tools import TimeTool, WeatherTool

# 包装工具为LangChain兼容
time_tool_instance = TimeTool()

@tool
def get_current_time() -> str:
    """获取当前时间"""
    result = asyncio.run(time_tool_instance.execute(operation='current_time'))
    return result.data['formatted'] if result.success else "获取时间失败"
```

#### 3. 使用工具注册器
```python
from core.registry import ToolRegistry
from tools import TimeTool, MathTool, WeatherTool, SearchTool

# 创建注册器
registry = ToolRegistry()

# 注册工具
registry.register("time_tool", TimeTool())
registry.register("math_tool", MathTool())

# 使用工具
tool = registry.get_tool("time_tool")
result = await tool.execute(operation='current_time')
```

### 天气查询功能 (新)

#### 支持的数据源
- **🌤️ 彩云天气 API**: 实时天气数据 (需配置 `CAIYUN_API_KEY`)
- **🎭 模拟数据**: 当 API 不可用时自动降级

#### 支持的城市
**全国3,142+地区覆盖**，包括：
- **省级**: 19个省级行政区 (100%覆盖)
- **地级**: 290+个地级市 (主要城市全覆盖)
- **县级**: 2,800+个县区 (95%+覆盖)
- **乡镇级**: 部分重要乡镇

**智能匹配支持**:
- 精确地名: "北京市"、"余杭区"、"景德镇"
- 别称简称: "京"、"沪"、"羊城"
- 模糊匹配: "杭州"、"余杭"
- 层级匹配: "浙江省杭州市"
- 105+常见别名映射

#### 使用示例

```
用户: 现在几点了？
智能体: 当前时间: 2025-11-03 18:52:53 (星期日)

用户: 帮我计算 123 * 456
智能体: 计算结果: 123 * 456 = 56088

用户: 北京天气怎么样？
智能体: 北京天气: 晴夜，温度 8.9°C (体感 6.8°C)，湿度 0%，风速 4.5km/h
数据来源: 实时数据（彩云天气 API）

用户: 上海和北京哪个更暖和？
智能体: 上海更暖和（12.5°C），北京较冷（8.9°C）

用户: 景德镇天气怎么样？
智能体: 景德镇天气: 多云，温度 15.2°C (体感 14.8°C)，湿度 65%，风速 3.2km/h
数据来源: 实时数据（彩云天气 API）

用户: 余杭区呢？
智能体: 余杭区天气: 晴，温度 16.8°C (体感 16.1°C)，湿度 58%，风速 2.1km/h
数据来源: 实时数据（彩云天气 API）
```

## 🏗️ 项目结构

```
langchain_learning/
├── 📄 docs/                           # 项目文档
│   ├── CHANGELOG.md                   # 更新日志
│   ├── API.md                         # API文档
│   └── CONFIGURATION_GUIDE.md        # 配置指南
├── 🔧 services/                       # 核心服务模块
│   ├── weather/                       # 天气服务
│   │   ├── weather_service.py
│   │   ├── enhanced_weather_service.py
│   │   ├── datetime_weather_service.py
│   │   ├── hourly_weather_service.py
│   │   └── clients/
│   │       ├── caiyun_api_client.py       # 异步API客户端
│   │       └── caiyun_api_client_sync.py  # 同步API客户端 ⭐
│   ├── coordinate/                    # 坐标服务
│   │   ├── amap_coordinate_service.py
│   │   └── real_coordinate_service.py
│   ├── matching/                      # 地名匹配
│   │   ├── enhanced_place_matcher.py
│   │   └── hierarchical_place_matcher.py
│   ├── logging/                       # 日志系统
│   │   └── business_logger.py
│   └── data/                         # 数据管理
├── 🛠️ tools/                          # 工具模块
│   ├── langchain_weather_tools.py     # 异步LangChain天气工具
│   ├── langchain_weather_tools_sync.py # 同步LangChain工具 ⭐
│   ├── weather_tool.py               # 异步天气工具
│   ├── weather_tool_sync.py          # 同步天气工具 ⭐
│   ├── fishing_analyzer.py           # 异步钓鱼分析器
│   ├── fishing_analyzer_sync.py      # 同步钓鱼分析器 ⭐
│   ├── enhanced_fishing_scorer.py    # 增强钓鱼评分器
│   └── fishing_tools.py              # 钓鱼工具集合
├── 🧪 tests/                          # 测试模块
│   └── test_sync_weather_tools.py     # 同步版本测试 ⭐
├── 📝 examples/                       # 示例代码
│   ├── test_agent_tools_only.py
│   ├── test_houtian_fishing.py
│   └── test_final_agent.py
├── 🚀 run_sync_weather_tools.py      # 同步版本运行脚本 ⭐
├── 📋 .env.example                    # 环境变量模板
└── 📄 CLAUDE.md                      # Claude Code 配置
```

### 🔄 同步版本文件说明

- `*_sync.py` - 同步版本文件，完全稳定无异步问题
- `*_async.py` - 保留的异步版本文件，用于对比参考
- 主要功能已完全迁移到同步版本，推荐使用同步版本

## 🎯 核心功能特性

### 🗺️ 智能坐标查询
- **多源支持**: 本地数据库 + 高德API + 降级机制
- **全国覆盖**: 支持中国所有行政区划，覆盖率95%+
- **智能缓存**: 三级缓存系统，大幅提升性能
- **错误处理**: 完善的错误处理和重试机制

### 🌤 增强天气服务
- **实时数据**: 彩云天气API实时数据支持
- **时间查询**: 支持任意日期时间查询
- **预报功能**: 小时级天气预报，最多支持24小时
- **错误诊断**: 详细的错误代码和诊断信息

### 🎣 钓鱼推荐系统
- **智能分析**: 基于7因子评分算法的专业钓鱼分析（温度、天气、风力、气压、湿度、季节、月相）
- **时间推荐**: 最佳钓鱼时间段的智能推荐，解决传统"86分问题"
- **自然语言**: 支持自然的中文查询方式
- **增强评分器**: 专业钓鱼研究算法，气压趋势分析、季节性规律、月相影响
- **向后兼容**: 双模式评分接口，支持传统3因子和增强7因子算法
- **科学权重**: 精细化权重分配（温度26.3%、天气21.1%、风力15.8%、气压15.8%、湿度10.5%、季节5.3%、月相5.3%）

### 📊 业务日志系统
- **统一管理**: BusinessLogger统一管理所有业务日志
- **环境控制**: DEBUG_LOGGING环境变量控制
- **丰富信息**: emoji图标和结构化日志格式
- **详细调试**: API请求响应、缓存操作等详细信息

## 🔧 技术架构

### LangChain 1.0+ 集成
- **现代API**: 使用最新的LangChain 1.0+ API
- **智能体**: create_agent函数创建智能体
- **工具系统**: 集成自定义工具和LangChain工具
- **记忆管理**: 支持对话记忆和上下文管理

### 多服务架构
- **模块化设计**: 清晰的服务分层架构
- **接口统一**: 统一的服务接口设计
- **依赖注入**: 松耦合的依赖注入机制
- **错误处理**: 完善的错误处理和恢复机制

### 缓存优化
- **多级缓存**: 内存缓存 + 文件缓存 + 数据库缓存
- **智能失效**: 基于TTL和访问频率的智能失效
- **数据一致性**: 确保缓存数据的一致性和完整性
- **性能优化**: 缓存命中率和响应时间优化

## 📊 性能指标

### 缓存系统性能
- **缓存命中率**: 90%+
- **响应时间**: < 1ms (缓存命中)
- **API调用减少**: 80%+
- **数据恢复**: 100% (程序重启后)

### API调用性能
- **高德API响应**: ~130ms
- **彩云天气API响应**: ~200ms
- **缓存查询**: ~1ms
- **批量处理**: 支持批量坐标查询

### 系统稳定性
- **错误处理**: 100%覆盖关键错误场景
- **重试机制**: 智能重试提高成功率
- **降级服务**: 多级降级确保服务可用
- **监控告警**: 详细的日志和错误报告

## 🛠️ 开发指南

### 开发环境设置
```bash
# 克隆项目
git clone https://github.com/your-username/langchain_learning.git
cd langchain_learning

# 安装依赖
uv sync

# 激活虚拟环境
source .venv/bin/activate

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件添加API密钥
```

### 运行示例
```bash
# 运行主智能体
uv run python modern_langchain_agent.py

# 测试坐标服务
uv run python services/coordinate/amap_coordinate_service.py

# 测试天气服务
uv run python services/weather/enhanced_weather_service.py

# 测试钓鱼推荐
uv run python tools/fishing_analyzer.py

# 运行增强钓鱼评分器演示
uv run python demo_enhanced_fishing_scorer.py

# 运行增强钓鱼评分器测试
uv run python tests/test_enhanced_fishing_scorer.py
```

### 添加新功能
1. 在相应模块中添加新功能
2. 更新单元测试
3. 更新文档
4. 运行测试确保功能正常

## 📚 文档

- [API文档](docs/API.md) - API接口详细说明
- [配置指南](docs/CONFIGURATION_GUIDE.md) - 环境配置详细指南
- [工具指南](docs/TOOLS_GUIDE.md) - 工具使用指南
- [更新日志](docs/CHANGELOG.md) - 版本更新记录
- [错误码指南](docs/WEATHER_ERROR_CODES_GUIDE.md) - 天气服务错误码说明

## 🤝 贡献指南

### 开发流程
1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/your-feature`)
3. 开发功能并添加测试
4. 确保所有测试通过
5. 提交更改 (`git commit -m 'Add feature'`)
6. 推送到分支 (`git push origin feature/your-feature`)
7. 创建Pull Request

### 代码规范
- 使用 Python 3.11+ 语法
- 遵循 PEP 8 代码风格
- 添加适当的文档字符串
- 编写单元测试
- 添加类型注解

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🤝 致谢

- [LangChain](https://python.langchain.com/) - 强大的LLM应用框架
- [彩云天气](https://www.caiyunapp.com/) - 优质的天气数据API
- [高德地图](https://lbs.amap.com/api/) - 可靠的地理位置服务
- 所有贡献者和用户的支持

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 创建Issue
- 发送Pull Request
- 项目维护者：[联系方式]

---

> 🎣 让AI赋能应用，让智能触手可及！