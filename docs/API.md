# API 文档

本文档描述了 LangChain 智能体项目中的主要 API 接口和使用方法。

## 目录

- [智能体 API](#智能体-api)
- [天气服务 API](#天气服务-api)
- [工具函数 API](#工具函数-api)
- [环境配置](#环境配置)
- [错误处理](#错误处理)
- [使用示例](#使用示例)

## 智能体 API

### ModernLangChainAgent 类

主要的智能体类，提供基于 LangChain 1.0+ 的对话和工具调用功能。

#### 初始化

```python
from modern_langchain_agent import ModernLangChainAgent

# 创建智能体实例
agent = ModernLangChainAgent(model_provider="zhipu")
```

**参数：**
- `model_provider` (str): 模型提供商，支持：
  - `"zhipu"` - 智谱AI GLM-4.6 (默认)
  - `"anthropic"` - Anthropic Claude
  - `"openai"` - OpenAI GPT

#### 方法

##### run(user_input: str) -> str

运行智能体，处理用户输入并返回回复。

**参数：**
- `user_input` (str): 用户输入的文本

**返回：**
- `str`: 智能体的回复

**示例：**
```python
agent = ModernLangChainAgent("zhipu")
response = agent.run("现在几点了？")
print(response)  # 输出当前时间信息
```

##### interactive_chat()

启动交互式聊天模式，支持持续对话。

**示例：**
```python
agent = ModernLangChainAgent("zhipu")
agent.interactive_chat()
```

## 天气服务 API

### CaiyunWeatherService 类

彩云天气 API 服务类，提供实时天气数据获取功能。

#### 初始化

```python
from weather_service import CaiyunWeatherService

# 自动从环境变量读取 API 密钥
service = CaiyunWeatherService()

# 手动指定 API 密钥
service = CaiyunWeatherService(api_key="your-api-key")
```

#### 方法

##### get_weather(city: str) -> tuple[WeatherData, str]

获取指定城市的天气信息。

**参数：**
- `city` (str): 城市名称，支持中文城市名

**返回：**
- `tuple[WeatherData, str]`:
  - `WeatherData`: 天气数据对象
  - `str`: 数据来源说明

**WeatherData 对象属性：**
- `temperature` (float): 温度（摄氏度）
- `apparent_temperature` (float): 体感温度（摄氏度）
- `humidity` (int): 湿度（百分比）
- `pressure` (float): 气压（hPa）
- `wind_speed` (float): 风速（km/h）
- `wind_direction` (float): 风向（度）
- `condition` (str): 天气状况描述

**示例：**
```python
service = CaiyunWeatherService()
weather_data, source = service.get_weather("北京")

print(f"温度: {weather_data.temperature}°C")
print(f"天气: {weather_data.condition}")
print(f"数据来源: {source}")
```

##### get_coordinates(city: str) -> tuple[float, float] | None

获取城市的地理坐标。

**参数：**
- `city` (str): 城市名称

**返回：**
- `tuple[float, float] | None`: (经度, 纬度) 或 None（如果城市不存在）

**支持的城市：**
北京、上海、广州、深圳、杭州、成都、西安、武汉、南京、重庆、天津、苏州、青岛、大连、厦门

### 便捷函数

##### get_weather_info(city: str) -> str

获取格式化的天气信息字符串。

**参数：**
- `city` (str): 城市名称

**返回：**
- `str`: 格式化的天气信息

**示例：**
```python
from weather_service import get_weather_info

weather_info = get_weather_info("上海")
print(weather_info)
# 输出: 上海天气: 多云，温度 25.0°C (体感 26.0°C)，湿度 65%，风速 8.5km/h
# 数据来源: 实时数据（彩云天气 API）
```

## 工具函数 API

### LangChain 工具装饰器

项目中使用 `@tool` 装饰器定义了以下工具函数：

#### get_current_time() -> str

获取当前时间和日期。

**返回：**
- `str`: 格式化的时间信息

**示例：**
```python
from modern_langchain_agent import get_current_time

time_info = get_current_time.invoke({})
print(time_info)
# 输出: 当前时间: 2025-11-03 18:52:53 (星期日)
```

#### calculate(expression: str) -> str

计算数学表达式。

**参数：**
- `expression` (str): 要计算的数学表达式

**返回：**
- `str`: 计算结果

**支持的操作：**
- 基本运算: `+`, `-`, `*`, `/`
- 括号: `()`
- 幂运算: `**`

**示例：**
```python
from modern_langchain_agent import calculate

result = calculate.invoke({"expression": "123 * 456 + 789"})
print(result)
# 输出: 计算结果: 123 * 456 + 789 = 56088
```

#### get_weather(city: str) -> str

查询城市天气信息（LangChain 工具版本）。

**参数：**
- `city` (str): 城市名称

**返回：**
- `str`: 天气信息字符串

**示例：**
```python
from modern_langchain_agent import get_weather

weather = get_weather.invoke({"city": "北京"})
print(weather)
# 输出: 北京天气: 晴天，温度 15.2°C (体感 13.8°C)，湿度 45%，风速 12.3km/h
```

#### search_information(query: str) -> str

搜索信息（模拟搜索功能）。

**参数：**
- `query` (str): 搜索查询词

**返回：**
- `str`: 搜索结果

**知识库包含：**
- LangChain 框架介绍
- Python 编程语言
- 人工智能相关概念
- 机器学习基础
- 大语言模型介绍

## 环境配置

### 必需的环境变量

```bash
# 智谱AI API 密钥（默认使用）
ANTHROPIC_AUTH_TOKEN=your-zhipu-api-token-here

# 彩云天气 API 密钥（用于真实天气数据）
CAIYUN_API_KEY=your-caiyun-api-key-here
```

### 可选的环境变量

```bash
# Anthropic Claude API 密钥
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# OpenAI GPT API 密钥
OPENAI_API_KEY=your-openai-api-key-here

# LangSmith 调试和追踪（可选）
LANGSMITH_API_KEY=your-langsmith-api-key
LANGSMITH_PROJECT=langchain-agent-demo
LANGSMITH_TRACING=true
```

### 环境变量加载

项目使用 `python-dotenv` 自动加载 `.env` 文件中的环境变量：

```python
from dotenv import load_dotenv
load_dotenv()
```

## 错误处理

### 智能体错误

常见错误类型和处理方法：

```python
try:
    agent = ModernLangChainAgent("zhipu")
    response = agent.run("用户输入")
except ValueError as e:
    if "API 密钥" in str(e):
        print("请检查 API 密钥配置")
    else:
        print(f"配置错误: {e}")
except Exception as e:
    print(f"智能体运行错误: {e}")
```

### 天气服务错误

天气服务具有完善的错误处理机制：

1. **API 密钥未配置**: 自动使用模拟数据
2. **网络连接失败**: 自动降级到模拟数据
3. **城市不存在**: 返回模拟数据并说明原因
4. **API 响应异常**: 解析失败时使用备用数据

```python
from weather_service import get_weather_info

# 即使 API 不可用也能正常工作
weather_info = get_weather_info("不存在的城市")
# 输出包含友好的错误提示和模拟数据
```

## 使用示例

### 完整的智能体对话示例

```python
import os
from dotenv import load_dotenv
from modern_langchain_agent import ModernLangChainAgent

# 加载环境变量
load_dotenv()

def main():
    # 创建智能体
    agent = ModernLangChainAgent(model_provider="zhipu")

    # 对话示例
    conversations = [
        "现在几点了？",
        "帮我计算 123 * 456",
        "北京天气怎么样？",
        "介绍一下 LangChain",
        "上海和北京哪个更暖和？"
    ]

    for user_input in conversations:
        print(f"用户: {user_input}")
        response = agent.run(user_input)
        print(f"智能体: {response}\n")

if __name__ == "__main__":
    main()
```

### 天气服务独立使用示例

```python
from weather_service import CaiyunWeatherService, get_weather_info

def demo_weather_service():
    # 使用便捷函数
    print("=== 便捷函数示例 ===")
    cities = ["北京", "上海", "广州"]

    for city in cities:
        weather_info = get_weather_info(city)
        print(weather_info)

    # 使用服务类
    print("\n=== 服务类示例 ===")
    service = CaiyunWeatherService()

    weather_data, source = service.get_weather("深圳")
    print(f"深圳天气详情:")
    print(f"  温度: {weather_data.temperature}°C")
    print(f"  体感: {weather_data.apparent_temperature}°C")
    print(f"  湿度: {weather_data.humidity}%")
    print(f"  风速: {weather_data.wind_speed} km/h")
    print(f"  天气: {weather_data.condition}")
    print(f"  来源: {source}")

if __name__ == "__main__":
    demo_weather_service()
```

### 集成测试示例

```python
import os
import sys
from dotenv import load_dotenv

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from weather_service import get_weather_info
from modern_langchain_agent import get_weather

def test_integration():
    """测试智能体与天气服务的集成"""

    # 测试直接天气服务调用
    print("1. 直接天气服务调用:")
    direct_result = get_weather_info("北京")
    print(f"   结果: {direct_result}")

    # 测试通过 LangChain 工具调用
    print("\n2. 通过 LangChain 工具调用:")
    tool_result = get_weather.invoke({"city": "北京"})
    print(f"   结果: {tool_result}")

    # 验证结果一致性
    print("\n3. 结果一致性验证:")
    if "北京" in direct_result and "北京" in tool_result:
        print("   ✅ 两种调用方式都返回了北京的天气信息")
    else:
        print("   ❌ 结果不一致")

if __name__ == "__main__":
    load_dotenv()
    test_integration()
```

## API 限制和注意事项

### 智谱AI API
- 需要有效的 API Token
- 有调用频率限制
- 支持中文对话优化

### 彩云天气 API
- 免费版本有调用次数限制
- 支持的天气数据类型：实时天气
- 建议在生产环境中配置付费计划

### 最佳实践
1. **错误处理**: 始终使用 try-catch 包装 API 调用
2. **环境变量**: 不要在代码中硬编码 API 密钥
3. **降级策略**: 天气服务内置了模拟数据降级机制
4. **性能考虑**: 避免频繁的 API 调用，考虑缓存机制

---

**更新时间**: 2025-11-03
**版本**: 1.0.0
**维护者**: LangChain 学习项目