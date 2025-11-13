#!/usr/bin/env python3
"""
基于 LangChain 1.0+ 最新 API 的智能体示例
使用 create_agent 函数和现代工具集成
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatTongyi
from langchain_core.tools import tool

# 导入同步版本的天气工具
from tools.langchain_weather_tools_sync import (
    get_weather_tools_sync,
    create_weather_tool_system_prompt
)

# 导入日志中间件
from services.middleware import AgentLoggingMiddleware, MiddlewareConfig
from services.middleware.integrated_middleware import IntegratedMiddlewareManager

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
    """使用 LangChain 1.0+ 的现代智能体实现（集成增强版）"""

    def __init__(self, model_provider: str = "anthropic", enable_logging: bool = True,
                 enable_intent_enhancement: bool = True,
                 middleware_config: Optional[MiddlewareConfig] = None):
        """
        初始化智能体

        Args:
            model_provider: 模型提供商 ("anthropic" 或 "openai")
            enable_logging: 是否启用日志中间件
            enable_intent_enhancement: 是否启用意图增强功能
            middleware_config: 自定义中间件配置
        """
        self.model_provider = model_provider
        self.enable_logging = enable_logging
        self.enable_intent_enhancement = enable_intent_enhancement
        self.middleware_config = middleware_config or MiddlewareConfig.from_env()

        self.model = self._initialize_model()
        # 使用同步版本的天气工具集，包含钓鱼推荐功能
        weather_tools = get_weather_tools_sync()
        self.tools = [get_current_time, calculate, search_information] + weather_tools

        # 初始化集成中间件管理器
        self.integrated_middleware = None
        self.logging_middleware = None

        if self.enable_logging:
            try:
                self.integrated_middleware = IntegratedMiddlewareManager(
                    config=self.middleware_config,
                    enable_intent_enhancement=self.enable_intent_enhancement
                )
                self.logging_middleware = self.integrated_middleware.logging_middleware

                print(f"📝 已启用集成中间件管理器")
                print(f"   日志记录: {self.enable_logging}")
                print(f"   意图增强: {self.enable_intent_enhancement}")

            except Exception as e:
                print(f"⚠️  集成中间件初始化失败，使用基础模式: {e}")
                self.enable_logging = False
                self.enable_intent_enhancement = False

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
        elif self.model_provider == "qwen":
            api_key = os.getenv("DASHSCOPE_API_KEY")
            
            return ChatTongyi(
                model="qwen-plus",
                api_key=api_key,
            )
        elif self.model_provider == "doubao":
            api_key = os.getenv("ARK_API_KEY")
            return ChatOpenAI(
                # model="gpt-4o-mini",
                base_url="https://ark.cn-beijing.volces.com/api/v3",
                api_key=api_key,
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
- 你是路亚钓鱼专家，擅长根据天气、时间、地点等信息给出钓鱼建议, 注意：只需要路亚，不需要提供其他类型钓鱼建议
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

        # 准备中间件列表
        middleware_list = []
        if self.integrated_middleware:
            # 使用集成中间件管理器获取所有中间件
            middleware_list = self.integrated_middleware.get_middleware_list()
            if middleware_list:
                print(f"📝 已启用集成中间件 (共 {len(middleware_list)} 个)")
                if self.logging_middleware:
                    print(f"   日志中间件会话: {self.logging_middleware.session_id[:8]}...")
        elif self.enable_logging and self.logging_middleware:
            # 兼容旧版本
            middleware_list.append(self.logging_middleware)
            print(f"📝 已启用传统日志中间件 (session: {self.logging_middleware.session_id[:8]}...)")

        # 使用 LangChain 1.0+ 的 create_agent 函数
        create_kwargs = {
            "model": self.model,
            "tools": self.tools,
            "system_prompt": system_prompt
        }

        # 只有当中间件列表不为空时才添加middleware参数
        if middleware_list:
            create_kwargs["middleware"] = middleware_list

        agent = create_agent(**create_kwargs)

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
            # 开始请求追踪
            if self.logging_middleware:
                self.logging_middleware.start_request_tracking(user_input)

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
            response = str(result)

            # 结束请求追踪
            if self.logging_middleware:
                self.logging_middleware.end_request_tracking()

            return response

        except Exception as e:
            error_msg = f"智能体执行出错: {str(e)}"
            if self.logging_middleware:
                self.logging_middleware.logger.error(f"💥 智能体执行异常: {error_msg}")
                self.logging_middleware.end_request_tracking()
            return error_msg

    def get_execution_summary(self) -> Optional[Dict[str, Any]]:
        """
        获取当前会话的执行摘要（增强版）

        Returns:
            包含执行统计、工具调用记录、意图分析等信息的字典，如果未启用日志则返回None
        """
        if self.integrated_middleware:
            # 使用集成中间件管理器获取综合统计
            summary = self.integrated_middleware.get_execution_summary()
            return summary
        elif self.logging_middleware:
            # 兼容传统日志中间件
            return self.logging_middleware.get_execution_summary()
        return None

    def reset_session_metrics(self):
        """重置当前会话的指标统计"""
        if self.integrated_middleware:
            self.integrated_middleware.reset_all_stats()
            if self.logging_middleware:
                print(f"📊 所有中间件指标已重置 (session: {self.logging_middleware.session_id[:8]}...)")
            else:
                print("📊 所有中间件指标已重置")
        elif self.logging_middleware:
            self.logging_middleware.reset_metrics()
            print(f"📊 会话指标已重置 (session: {self.logging_middleware.session_id[:8]}...)")

    def get_intent_stats(self) -> Optional[Dict[str, Any]]:
        """
        获取意图分析统计信息

        Returns:
            意图统计信息，如果未启用意图增强则返回None
        """
        if self.integrated_middleware and self.integrated_middleware.intent_middleware:
            return self.integrated_middleware.intent_middleware.get_intent_stats()
        return None

    def configure_middleware(self, enable_intent_enhancement: Optional[bool] = None,
                           enable_logging: Optional[bool] = None,
                           log_level: Optional[str] = None):
        """
        动态配置中间件

        Args:
            enable_intent_enhancement: 是否启用意图增强
            enable_logging: 是否启用日志记录
            log_level: 日志级别
        """
        if enable_intent_enhancement is not None:
            self.enable_intent_enhancement = enable_intent_enhancement

        if enable_logging is not None:
            self.enable_logging = enable_logging

        if log_level is not None and self.integrated_middleware:
            self.integrated_middleware.set_log_level(log_level)

        # 重新初始化agent以应用新配置
        print("🔄 正在重新配置智能体...")
        self.agent = self._create_agent()
        print("✅ 智能体配置更新完成")

    def interactive_chat(self):
        """启动交互式聊天"""
        print("🤖 欢迎使用 LangChain 1.0+ 智能体!")
        print(f"📋 当前使用模型: {self.model_provider}")
        print("🛠️  可用工具: 时间查询、数学计算、天气查询、信息搜索")

        if self.enable_logging:
            print(f"📝 日志记录: 已启用")
            if self.logging_middleware:
                print(f"   会话ID: {self.logging_middleware.session_id[:8]}...")
            if self.enable_intent_enhancement:
                print("   意图增强: 已启用")
            print("📊 输入 'stats' 查看执行统计, 'reset' 重置指标")
            if self.enable_intent_enhancement:
                print("🧠 输入 'intent' 查看意图统计")
        else:
            print("📝 日志记录: 未启用")

        print("💡 输入 'quit' 或 'exit' 退出程序\n")

        while True:
            try:
                user_input = input("👤 您: ").strip()

                if user_input.lower() in ['quit', 'exit', '退出', 'q']:
                    print("👋 感谢使用，再见!")
                    break

                # 处理统计命令
                if user_input.lower() == 'stats' and self.enable_logging:
                    summary = self.get_execution_summary()
                    if summary:
                        print("\n📊 执行统计:")
                        if 'session_id' in summary:
                            print(f"   会话ID: {summary['session_id'][:8]}...")
                        if 'metrics' in summary:
                            metrics = summary['metrics']
                            print(f"   总耗时: {metrics.get('total_duration_ms', 0):.2f}ms")
                            print(f"   模型调用次数: {metrics.get('model_calls_count', 0)}")
                            print(f"   工具调用次数: {metrics.get('tool_calls_count', 0)}")
                            print(f"   错误次数: {metrics.get('errors_count', 0)}")
                            print(f"   Token使用: {metrics.get('token_usage', 'N/A')}")
                        if 'intent_stats' in summary:
                            intent_stats = summary['intent_stats']
                            print(f"   意图增强次数: {intent_stats.get('tool_selection_enhancements', 0)}")
                            most_common = intent_stats.get('most_common_intent')
                            if most_common:
                                print(f"   最常见意图: {most_common}")
                        print()
                    else:
                        print("❌ 无法获取执行统计\n")
                    continue

                # 处理意图统计命令
                if user_input.lower() == 'intent' and self.enable_intent_enhancement:
                    intent_stats = self.get_intent_stats()
                    if intent_stats:
                        print("\n🧠 意图分析统计:")
                        print(f"   总调用次数: {intent_stats.get('total_calls', 0)}")
                        print(f"   工具选择增强次数: {intent_stats.get('tool_selection_enhancements', 0)}")

                        intent_distribution = intent_stats.get('intent_distribution', {})
                        if intent_distribution:
                            print("   意图分布:")
                            for intent, count in sorted(intent_distribution.items(), key=lambda x: x[1], reverse=True):
                                print(f"     {intent}: {count}次")

                        most_common = intent_stats.get('most_common_intent')
                        if most_common:
                            print(f"   最常见意图: {most_common}")
                        print()
                    else:
                        print("❌ 意图增强未启用或无统计数据\n")
                    continue

                # 处理重置命令
                if user_input.lower() == 'reset' and self.enable_logging:
                    self.reset_session_metrics()
                    continue

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
    # model_provider = "zhipu"
    model_provider = "qwen"
    # model_provider = "doubao"
    try:
        # 创建智能体
        agent = ModernLangChainAgent(model_provider=model_provider)

        # 测试用例
        test_cases = [
            # "现在几点了？",
            # "帮我计算 123 * 456 + 789",
            # "余杭区今天天气怎么样？",
            # "景德镇明天天气怎么样？",
            # "临安今天天气怎么样？",
            "今天什么时段去杭州市余杭区钓鱼比较好？",
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