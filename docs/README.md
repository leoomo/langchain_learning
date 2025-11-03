# LangChain 学习项目 - 智谱AI集成

一个全面的 LangChain 1.0+ 学习项目，展示如何构建现代化的 LLM 应用程序，**默认使用智谱AI GLM-4.6 模型**。

## 🎯 项目特色

- **🚀 最新 LangChain 1.0+ API**: 使用 `create_agent` 函数和现代工具集成
- **🤖 多模型支持**: 智谱AI (默认)、Anthropic Claude、OpenAI GPT
- **🛠️ 实用智能体**: 内置时间查询、数学计算、天气查询、信息搜索工具
- **🌤️ 真实天气数据**: 集成彩云天气 API，提供实时天气信息
- **🗺️ 全国地区覆盖**: 支持3,142+中国地区（95%+覆盖率），智能地名匹配
- **📚 完整示例**: 从基础对话到复杂智能体的全方位演示
- **🧪 测试驱动**: 包含结构测试和功能验证

## 📁 项目文件结构

```
├── modern_langchain_agent.py      # 🤖 LangChain 1.0+ 智能体 (主要功能)
├── demo_new_tools_agent.py        # 🛠️ 新工具模块集成演示
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
├── services/                     # 🌐 服务模块 (重组后)
│   ├── __init__.py               # 服务模块导出
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
├── agents/                       # 🤖 智能体模块
│   ├── __init__.py               # 智能体模块导出
│   └── modern_agent.py           # 现代智能体实现
├── data/                         # 📊 数据目录
│   ├── admin_divisions.db        # 🗄️ SQLite数据库 (3,142+地区)
│   ├── backup_regions.csv        # 💾 数据备份
│   ├── national_areas_raw.json   # 📋 原始数据
│   ├── national_region_database.py    # 🇨🇳 全国地区数据库初始化
│   └── coordinate_enrichment.py       # 📍 坐标信息丰富化
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
│   │   └── refactor-project-structure/  # 🏗️ 项目结构重构提案
│   └── AGENTS.md                 # OpenSpec 工作流指南
├── docs/                         # 📚 文档目录
│   ├── QUICK_START.md            # 🚀 5分钟快速体验指南
│   ├── TOOLS_GUIDE.md            # 🛠️ 详细工具使用指南
│   ├── API.md                    # 📖 完整API参考文档
│   ├── CHANGELOG.md              # 📋 版本更新日志
│   ├── NATIONAL_COVERAGE_COMPLETION_REPORT.md  # 🎯 项目完成报告
│   └── 其他报告文档...
├── .env.example                  # 🔑 环境变量配置示例
├── .env                          # 🔑 环境变量配置 (需要创建)
├── pyproject.toml                # 📦 项目依赖配置
└── README.md                     # 📋 项目说明 (本文件)
```

## 🚀 快速开始

### 1. 安装依赖

```bash
uv sync
```

### 2. 配置 API 密钥

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 智谱AI (默认使用，推荐)
ANTHROPIC_AUTH_TOKEN=your-zhipu-api-token-here

# 彩云天气 API (用于真实天气数据)
CAIYUN_API_KEY=your-caiyun-api-key-here

# 其他模型 (可选)
ANTHROPIC_API_KEY=your-anthropic-api-key-here
OPENAI_API_KEY=your-openai-api-key-here
```

### 3. 获取 API 密钥

#### 智谱AI API (必需)
1. 访问 [智谱AI开放平台](https://open.bigmodel.cn/)
2. 注册并登录账号
3. 在控制台获取 API Token
4. 设置到 `ANTHROPIC_AUTH_TOKEN` 环境变量

#### 彩云天气 API (推荐)
1. 访问 [彩云天气官网](https://www.caiyunapp.com/)
2. 注册账号并登录
3. 在开发者控制台获取 API 密钥
4. 设置到 `CAIYUN_API_KEY` 环境变量

> 💡 **提示**: 彩云天气 API 提供免费调用额度，用于获取真实天气数据。未配置时将使用模拟数据。

### 4. 运行测试

```bash
# 🛠️ 运行新工具模块演示 (推荐)
uv run python demo_new_tools_agent.py

# 🤖 运行主要智能体 (需要智谱AI API)
uv run python modern_langchain_agent.py

# 🧪 运行所有测试
uv run python -m pytest tests/ -v

# 📋 运行单元测试
uv run python tests/unit/test_agent_structure.py
uv run python tests/unit/test_weather_service.py

# 🌤️ 运行天气相关测试
uv run python tests/weather/test_real_weather_api.py
uv run python tests/unit/test_weather_service.py

# 🔗 运行集成测试
uv run python tests/integration/test_integrated_weather_agent.py
uv run python tests/integration/test_agent_conversation.py

# 🎭 运行演示脚本
uv run python tests/demos/demo_weather_agent.py
uv run python tests/demos/weather_example.py

# 📚 运行基础示例 (需要智谱AI API)
uv run python zhipu_langchain_example.py

# 🇨🇳 初始化全国地区数据库 (首次运行)
uv run python data/national_region_database.py

# 📍 丰富坐标信息 (数据库初始化后)
uv run python data/coordinate_enrichment.py

# 🧪 测试全国覆盖功能
uv run python tests/test_national_coverage.py

# ✅ 验证系统集成
uv run python tests/integration/verify_national_integration.py
```

### 5. 测试指南

详细的测试说明请参考 [`tests/README.md`](tests/README.md)，包含：
- 测试目录结构说明
- 各种测试类型的运行方式
- 环境配置要求
- 故障排除指南

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

## 📚 完整功能列表

### 核心特性
- ✅ 基于 LangChain 1.0 标准接口
- ✅ 智能体工具集成
- ✅ 支持流式输出
- ✅ 提示词模板
- ✅ 对话记忆
- ✅ 并行链式调用
- ✅ 顺序链式调用
- ✅ 可配置模型支持
- ✅ OpenSpec 规范驱动开发
- ✅ 结构化测试套件
- ✅ 真实天气 API 集成
- ✅ **全国3,142+地区覆盖** (95%+覆盖率)
- ✅ **智能地名匹配系统** (82.1%成功率)
- ✅ **多级缓存优化** (2000倍性能提升)
- ✅ **100%坐标覆盖** (所有地区都有经纬度)

### 🛠️ 开发工具与工作流

#### OpenSpec 规范管理
本项目使用 OpenSpec 进行规范驱动的开发：
- 📋 **变更提案**: 在 `openspec/changes/` 目录中管理功能变更
- 🔄 **工作流程**: 提案 → 实施 → 归档的完整开发流程
- 📖 **详细指南**: 参考 [`openspec/AGENTS.md`](openspec/AGENTS.md)

#### 测试策略
- 🧪 **单元测试**: 独立模块功能验证
- 🔗 **集成测试**: 多组件协同测试
- 🎭 **演示脚本**: 功能展示和验证
- 🌤️ **专项测试**: 天气 API 深度测试

### 支持的模型
- **🇨🇳 智谱AI GLM-4.6** (默认，中文优化)
- **🧠 Anthropic Claude** (高质量推理)
- **🚀 OpenAI GPT** (快速响应)

## 🔧 技术实现

### LangChain 1.0+ 智能体架构

```python
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

# 智谱AI集成 (推荐)
zhipu_model = init_chat_model(
    model="glm-4.6",
    model_provider="openai",
    base_url="https://open.bigmodel.cn/api/paas/v4/",
    api_key=os.getenv("ANTHROPIC_AUTH_TOKEN"),
)

# 创建智能体
agent = create_agent(
    model=zhipu_model,
    tools=[get_current_time, calculate, get_weather, search_information],
    system_prompt="你是一个智能助手..."
)

# 调用智能体
result = agent.invoke({
    "messages": [{"role": "user", "content": "你好"}]
})
```

### 示例功能模块

#### 1. 智能体示例 (`modern_langchain_agent.py`)
- 🤖 完整的智能体实现
- 🛠️ 内置4个实用工具
- 🔄 多模型支持
- 💬 交互式对话模式

#### 2. 基础集成 (`zhipu_langchain_example.py`)
1. **基础对话** (`basic_chat_example`)
   - 简单的一问一答

2. **流式对话** (`streaming_chat_example`)
   - 实时流式输出

3. **提示词模板** (`prompt_template_example`)
   - 使用模板生成结构化提示

4. **对话记忆** (`conversation_example`)
   - 维护对话历史

5. **并行链** (`parallel_chain_example`)
   - 同时执行多个任务

6. **顺序链** (`sequential_chain_example`)
   - 顺序执行多个任务

7. **可配置模型** (`configurable_model_example`)
   - 运行时切换不同模型

## LangChain 1.0 最佳实践

这个示例遵循了 LangChain 1.0 的最新最佳实践：

### 1. 使用标准接口

- 使用 `init_chat_model` 进行模型初始化
- 利用 OpenAI 兼容接口简化集成

### 2. 现代链式语法

```python
# LCEL (LangChain Expression Language)
chain = prompt | model | StrOutputParser()
```

### 3. 类型安全

- 完整的类型提示
- 结构化的消息格式

### 4. 模块化设计

- 每个功能独立实现
- 清晰的函数分离

## 故障排除

### 常见问题

1. **API密钥错误**
   ```
   错误: 请设置环境变量 ZHIPU_API_KEY
   解决: export ZHIPU_API_KEY='your-api-key'
   ```

2. **网络连接问题**
   ```
   错误: 连接超时
   解决: 检查网络连接和防火墙设置
   ```

3. **依赖缺失**
   ```
   错误: ModuleNotFoundError
   解决: uv sync 安装依赖
   ```

### 调试技巧

1. 启用详细日志：
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. 检查API响应：
   ```python
   # 在模型调用后添加调试信息
   print(f"模型响应: {response}")
   ```

## 扩展用法

### 添加自定义工具

```python
from langchain_core.tools import tool

@tool
def my_tool(input: str) -> str:
    """自定义工具描述"""
    return f"处理结果: {input}"

# 在链中使用工具
from langchain.agents import create_agent
agent = create_agent(model, [my_tool])
```

### 异步调用

```python
# 异步调用
response = await model.ainvoke([message])

# 异步流式输出
async for chunk in model.astream([message]):
    print(chunk.content, end="")
```

## 📖 相关文档

- **[API 文档](docs/API.md)** - 详细的 API 接口说明和使用示例
- **[测试指南](tests/README.md)** - 完整的测试套件说明和运行指南
- **[OpenSpec 工作流](openspec/AGENTS.md)** - 规范驱动的开发流程指南

## 参考资料

- [LangChain 1.0 官方文档](https://docs.langchain.com/)
- [智谱AI API文档](https://open.bigmodel.cn/dev/api)
- [LangChain模型集成指南](https://docs.langchain.com/oss/python/integrations/chat/)
- [彩云天气 API文档](https://docs.caiyunapp.com/weather-api/v2/)

## 许可证

MIT License