#!/usr/bin/env python3
"""
基于 LangChain 1.0+ 最新 API 的智能体示例
使用 create_agent 函数和现代工具集成
"""

import os
from typing import List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

# 导入增强的天气工具
from tools.langchain_weather_tools import (
    get_weather_tools,
    create_weather_tool_system_prompt
)

# 使用最新的 @tool 装饰器定义工具
@tool
def get_current_time() -> str:
    """获取当前时间和日期"""
    now = datetime.now()
    return f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')} ({now.strftime('%A')})"

@tool
def calculate(expression: str) -> str:
    """
    计算数学表达式

    Args:
        expression: 要计算的数学表达式，如 "2+3*4"
    """
    try:
        # 安全的数学表达式计算
        allowed_chars = set('0123456789+-*/().** ')
        if not all(c in allowed_chars for c in expression):
            return "错误: 表达式包含不允许的字符，只支持数字和基本运算符"

        result = eval(expression)
        return f"计算结果: {expression} = {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"


@tool
def search_information(query: str) -> str:
    """
    搜索信息（模拟搜索功能）

    Args:
        query: 搜索查询词
    """
    # 模拟知识库
    knowledge_base = {
        "langchain": "LangChain 是一个用于构建 LLM 应用的开源框架，提供了链、代理、记忆等功能，简化了 AI 应用的开发。",
        "python": "Python 是一种高级编程语言，以简洁的语法和强大的库生态系统著称，广泛用于 AI/ML 开发。",
        "人工智能": "人工智能 (AI) 是计算机科学的分支，致力于创造能够执行需要人类智能的任务的系统。",
        "机器学习": "机器学习是 AI 的子集，使计算机能够从数据中学习并改进性能，无需显式编程。",
        "大语言模型": "大语言模型 (LLM) 是经过大量文本训练的深度学习模型，能够理解和生成人类语言。"
    }

    query_lower = query.lower()
    for keyword, info in knowledge_base.items():
        if keyword in query_lower:
            return f"搜索结果: {info}"

    return f"关于 '{query}' 的信息: 这是一个模拟搜索功能。在实际应用中，您可以集成真实的搜索引擎 API 来获取更全面的信息。"

class ModernLangChainAgent:
    """使用 LangChain 1.0+ 的现代智能体实现"""

    def __init__(self, model_provider: str = "anthropic"):
        """
        初始化智能体

        Args:
            model_provider: 模型提供商 ("anthropic" 或 "openai")
        """
        self.model_provider = model_provider
        self.model = self._initialize_model()
        # 使用增强的天气工具集，包含钓鱼推荐功能
        weather_tools = get_weather_tools()
        self.tools = [get_current_time, calculate, search_information] + weather_tools
        self.agent = self._create_agent()

    def _initialize_model(self):
        """初始化语言模型"""
        if self.model_provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("请设置 ANTHROPIC_API_KEY 环境变量")
            # 使用 Claude Sonnet 4.5 最新模型
            return ChatAnthropic(
                model="claude-sonnet-4-5-20250929",
                api_key=api_key
            )

        elif self.model_provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("请设置 OPENAI_API_KEY 环境变量")
            # 使用 GPT-4o-mini
            return ChatOpenAI(
                model="gpt-4o-mini",
                api_key=api_key
            )
        elif self.model_provider == "zhipu":
            api_key =  os.getenv("ANTHROPIC_AUTH_TOKEN")
            if not api_key:
                raise ValueError("")
            return init_chat_model(
                model="glm-4.6",
                model_provider="openai",
                base_url="https://open.bigmodel.cn/api/paas/v4/",
                api_key= api_key,
            )

        else:
            raise ValueError(f"不支持的模型提供商: {self.model_provider}")

    def _create_agent(self):
        """使用最新的 create_agent API 创建智能体"""
        # 使用增强的天气工具系统提示词，包含钓鱼专业知识
        weather_system_prompt = create_weather_tool_system_prompt()

        system_prompt = f"""你是一个智能助手，具备多种实用工具来帮助用户完成任务。

你的基础工具包括:
1. get_current_time - 获取当前时间和日期
2. calculate - 计算数学表达式
3. search_information - 搜索和获取信息

你的专业天气工具包括:
4. query_current_weather - 查询当前天气
5. query_weather_by_date - 查询指定日期天气
6. query_weather_by_datetime - 查询指定时间段天气
7. query_hourly_forecast - 查询小时级预报
8. query_time_period_weather - 查询指定日期和时间段的天气
9. query_fishing_recommendation - 钓鱼时间推荐和天气分析

使用指南:
- 你是路亚钓鱼专家，擅长根据天气、时间、地点等信息给出钓鱼建议
- 当用户问钓鱼相关问题时(如"明天钓鱼合适吗"、"什么时候钓鱼好")，使用query_fishing_recommendation工具
- 当用户问天气问题时，根据查询内容选择合适的天气工具
- 根据用户问题选择最合适的工具
- 可以组合使用多个工具来解决复杂问题
- 用中文回答，保持友好和专业的语调
- 如果工具无法解决问题，会告知用户并提供替代建议

钓鱼专业知识:
- 最佳钓鱼温度: 15-25°C
- 理想天气条件: 多云、阴天或小雨天气
- 最佳钓鱼时段: 早上(5-9点)和傍晚(18-21点)
- 应避免的条件: 强风(>15km/h)、暴雨、极端温度

{weather_system_prompt}

示例交互:
- 用户问时间 → 使用 get_current_time
- 用户问计算 → 使用 calculate
- 用户问"明天钓鱼合适吗？" → 使用 query_fishing_recommendation
- 用户问"明天上午天气" → 使用 query_weather_by_datetime
- 用户问知识 → 使用 search_information"""

    # 使用 LangChain 1.0+ 的 create_agent 函数
        agent = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=system_prompt
        )

        return agent

    def run(self, user_input: str) -> str:
        """
        运行智能体

        Args:
            user_input: 用户输入的文本

        Returns:
            智能体的回复
        """
        try:
            # 使用 LangChain 1.0+ 的标准调用格式
            result = self.agent.invoke({
                "messages": [
                    {"role": "user", "content": user_input}
                ]
            })

            # 提取回复内容
            if isinstance(result, dict) and "messages" in result:
                # 获取最后一条消息
                messages = result["messages"]
                if messages and len(messages) > 0:
                    last_message = messages[-1]
                    if hasattr(last_message, 'content'):
                        return last_message.content
                    elif isinstance(last_message, dict) and "content" in last_message:
                        return last_message["content"]

            # 备用处理
            return str(result)

        except Exception as e:
            return f"智能体执行出错: {str(e)}"

    def interactive_chat(self):
        """启动交互式聊天"""
        print("🤖 欢迎使用 LangChain 1.0+ 智能体!")
        print(f"📋 当前使用模型: {self.model_provider}")
        print("🛠️  可用工具: 时间查询、数学计算、天气查询、信息搜索")
        print("💡 输入 'quit' 或 'exit' 退出程序\n")

        while True:
            try:
                user_input = input("👤 您: ").strip()

                if user_input.lower() in ['quit', 'exit', '退出', 'q']:
                    print("👋 感谢使用，再见!")
                    break

                if not user_input:
                    continue

                print("🤔 智能体思考中...")
                response = self.run(user_input)
                print(f"🤖 智能体: {response}\n")

            except KeyboardInterrupt:
                print("\n👋 程序被中断，再见!")
                break
            except Exception as e:
                print(f"❌ 发生错误: {str(e)}\n")

def demonstrate_agent_capabilities():
    """演示智能体功能"""
    print("🚀 LangChain 1.0+ 智能体功能演示")
    print("=" * 60)

    # 检查 API 密钥
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    zhipu_key = os.getenv("ANTHROPIC_AUTH_TOKEN")

    if not any([anthropic_key, openai_key, zhipu_key]):
        print("❌ 错误: 请设置至少一个 API 密钥")
        print("在 .env 文件中设置 ANTHROPIC_API_KEY 或 OPENAI_API_KEY")
        return

    # 选择可用的模型
    # if anthropic_key:
    #     model_provider = "anthropic"
    #     print("✅ 使用 Anthropic Claude 模型")
    # else:
    #     model_provider = "openai"
    #     print("✅ 使用 OpenAI GPT 模型")
    model_provider = "zhipu"
    try:
        # 创建智能体
        agent = ModernLangChainAgent(model_provider=model_provider)

        # 测试用例
        test_cases = [
            # "现在几点了？",
            # "帮我计算 123 * 456 + 789",
            # "余杭区今天天气怎么样？",
            # "景德镇今天天气怎么样？",
            # "临安今天天气怎么样？",
            "今天什么时候去余杭区钓鱼比较好？",
            # "今天是什么日子？"
        ]

        print(f"\n🧪 运行 {len(test_cases)} 个测试用例:\n")

        for i, test_input in enumerate(test_cases, 1):
            print(f"📝 测试 {i}: {test_input}")
            response = agent.run(test_input)
            print(f"🤖 回复: {response}\n")
            print("-" * 40)

        # # 询问是否进入交互模式
        # choice = input("🎯 是否进入交互聊天模式? (y/n): ").strip().lower()
        # if choice in ['y', 'yes', '是', '']:
        #     agent.interactive_chat()
        # else:
        #     print("👋 演示完成!")

    except Exception as e:
        print(f"❌ 智能体创建或运行失败: {str(e)}")

def main():
    """主函数"""
    print("🎯 LangChain 1.0+ 现代智能体示例")
    print("基于最新 create_agent API 实现")
    print("📚 文档: https://docs.langchain.com")
    print()

    demonstrate_agent_capabilities()

if __name__ == "__main__":
    main()