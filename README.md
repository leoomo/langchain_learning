# 智谱大模型 LangChain 1.0 集成示例

这个项目展示了如何使用 LangChain 1.0 连接智谱大模型，基于最新的 LangChain 1.0 最佳实践。

## 特性

- ✅ 基于 LangChain 1.0 标准接口
- ✅ 支持流式输出
- ✅ 提示词模板
- ✅ 对话记忆
- ✅ 并行链式调用
- ✅ 顺序链式调用
- ✅ 可配置模型支持

## 环境要求

- Python >= 3.11
- LangChain 1.0+
- 相关依赖包（见 pyproject.toml）

## 安装依赖

```bash
# 安装所有依赖
uv sync

# 或手动安装特定依赖
uv add langchain langchain-openai langchain-core
uv add requests zai-sdk
```

## 环境变量配置

### 智谱大模型（必需）

```bash
export ZHIPU_API_KEY='your-zhipu-api-key-here'
```

### 其他模型（可选，用于可配置模型示例）

```bash
# OpenAI（可选）
export OPENAI_API_KEY='your-openai-api-key'

# Anthropic（可选）
export ANTHROPIC_API_KEY='your-anthropic-api-key'
```

## 获取智谱API密钥

1. 访问 [智谱AI开放平台](https://open.bigmodel.cn/)
2. 注册账号并登录
3. 创建应用并获取API密钥
4. 设置环境变量

## 运行示例

```bash
# 运行完整示例
uv run python zhipu_langchain_example.py
```

## 代码结构

### 核心实现

项目使用 **OpenAI兼容接口** 连接智谱大模型，这是 LangChain 1.0 推荐的方式：

```python
from langchain.chat_models import init_chat_model

# 创建智谱模型
model = init_chat_model(
    model="glm-4",
    model_provider="openai",
    api_key=api_key,
    base_url="https://open.bigmodel.cn/api/paas/v4",
    temperature=0.7
)
```

### 示例功能

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

## 参考资料

- [LangChain 1.0 官方文档](https://docs.langchain.com/)
- [智谱AI API文档](https://open.bigmodel.cn/dev/api)
- [LangChain模型集成指南](https://docs.langchain.com/oss/python/integrations/chat/)

## 许可证

MIT License