# LangChain 学习项目 - 智谱AI集成

一个全面的 LangChain 1.0+ 学习项目，展示如何构建现代化的 LLM 应用程序，**默认使用智谱AI GLM-4.6 模型**。

## 🎯 项目特色

- **🚀 最新 LangChain 1.0+ API**: 使用 `create_agent` 函数和现代工具集成
- **🤖 多模型支持**: 智谱AI (默认)、Anthropic Claude、OpenAI GPT
- **🛠️ 实用智能体**: 内置时间查询、数学计算、天气查询、信息搜索工具
- **🌤️ 真实天气数据**: 集成彩云天气 API，提供实时天气信息
- **📚 完整示例**: 从基础对话到复杂智能体的全方位演示
- **🧪 测试驱动**: 包含结构测试和功能验证

## 📁 项目文件结构

```
├── modern_langchain_agent.py    # 🤖 LangChain 1.0+ 智能体 (主要功能)
├── weather_service.py           # 🌤️ 彩云天气 API 服务模块
├── zhipu_langchain_example.py   # 📚 智谱AI基础集成示例
├── tests/                       # 🧪 测试套件 (重新组织)
│   ├── README.md               # 📖 测试目录说明文档
│   ├── unit/                   # 📋 单元测试
│   │   ├── test_agent_structure.py
│   │   ├── test_weather_service.py
│   │   ├── test_weather_component_only.py
│   │   └── final_weather_component_test.py
│   ├── integration/            # 🔗 集成测试
│   │   ├── test_integrated_weather_agent.py
│   │   ├── test_agent_conversation.py
│   │   └── test_agent_weather_simulation.py
│   ├── demos/                  # 🎭 演示脚本
│   │   ├── demo_weather_agent.py
│   │   └── weather_example.py
│   └── weather/                # 🌤️ 天气专项测试
│       └── test_real_weather_api.py
├── openspec/                   # 📋 OpenSpec 规范管理
│   ├── changes/               # 变更提案
│   └── AGENTS.md              # OpenSpec 工作流指南
├── .env.example               # 🔑 环境变量配置示例
├── .env                       # 🔑 环境变量配置 (需要创建)
├── pyproject.toml             # 📦 项目依赖配置
└── README.md                  # 📋 项目说明 (本文件)
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

# 🤖 运行主要智能体 (需要智谱AI API)
uv run python modern_langchain_agent.py

# 📚 运行基础示例 (需要智谱AI API)
uv run python zhipu_langchain_example.py
```

### 5. 测试指南

详细的测试说明请参考 [`tests/README.md`](tests/README.md)，包含：
- 测试目录结构说明
- 各种测试类型的运行方式
- 环境配置要求
- 故障排除指南

## 🤖 智能体功能 (新)

### 内置工具

- **⏰ get_current_time()** - 获取当前时间和日期
- **🧮 calculate(expression)** - 计算数学表达式
- **🌤️ get_weather(city)** - 查询城市天气信息 (支持真实数据)
- **🔍 search_information(query)** - 搜索信息

### 天气查询功能 (新)

#### 支持的数据源
- **🌤️ 彩云天气 API**: 实时天气数据 (需配置 `CAIYUN_API_KEY`)
- **🎭 模拟数据**: 当 API 不可用时自动降级

#### 支持的城市
北京、上海、广州、深圳、杭州、成都、西安、武汉、南京、重庆、天津、苏州、青岛、大连、厦门

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