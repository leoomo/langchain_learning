#!/usr/bin/env python3
"""
新工具模块集成演示

展示如何将新创建的工具模块集成到LangChain智能体中。
"""

import asyncio
from typing import Dict, Any
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

# 导入我们的新工具模块
from tools import TimeTool, MathTool, WeatherTool, SearchTool

# 加载环境变量
load_dotenv()

# 创建工具实例
time_tool = TimeTool()
math_tool = MathTool()
weather_tool = WeatherTool()
search_tool = SearchTool()

# 将工具包装为LangChain兼容的工具函数
@tool
def get_current_time() -> str:
    """获取当前时间，包括日期、时间和时区信息"""
    result = asyncio.run(time_tool.execute(operation='current_time'))
    if result.success:
        data = result.data
        return f"当前时间: {data['formatted']} ({data['timezone']})"
    else:
        return f"获取时间失败: {result.error}"

@tool
def calculate_math(expression: str) -> str:
    """执行数学计算，支持加减乘除、幂运算、三角函数等

    Args:
        expression: 数学表达式，如 "123 + 456" 或 "sqrt(144)"
    """
    # 简单的表达式解析
    try:
        if '+' in expression:
            a, b = map(float, expression.split('+'))
            result = asyncio.run(math_tool.execute(operation='add', a=a, b=b))
        elif '-' in expression:
            a, b = map(float, expression.split('-'))
            result = asyncio.run(math_tool.execute(operation='subtract', a=a, b=b))
        elif '*' in expression:
            a, b = map(float, expression.split('*'))
            result = asyncio.run(math_tool.execute(operation='multiply', a=a, b=b))
        elif '/' in expression:
            a, b = map(float, expression.split('/'))
            result = asyncio.run(math_tool.execute(operation='divide', a=a, b=b))
        elif 'sqrt' in expression:
            num = float(expression.replace('sqrt(', '').replace(')', ''))
            result = asyncio.run(math_tool.execute(operation='sqrt', number=num))
        else:
            return f"不支持的表达式: {expression}"

        if result.success:
            return result.data['formatted']
        else:
            return f"计算失败: {result.error}"
    except Exception as e:
        return f"表达式解析错误: {str(e)}"

@tool
def get_weather_info(location: str) -> str:
    """获取指定地区的天气信息

    Args:
        location: 地区名称，如 "北京"、"上海" 等
    """
    result = asyncio.run(weather_tool.execute(operation='current_weather', location=location))
    if result.success:
        data = result.data
        return (f"{location}天气: {data['condition']}，"
                f"温度 {data['temperature']}°C，"
                f"湿度 {data['humidity']}%，"
                f"风速 {data['wind_speed']:.1f}km/h")
    else:
        return f"获取天气失败: {result.error}"

@tool
def search_knowledge(query: str) -> str:
    """在知识库中搜索信息

    Args:
        query: 搜索关键词或问题
    """
    result = asyncio.run(search_tool.execute(operation='knowledge_search', query=query))
    if result.success and result.data['results']:
        top_result = result.data['results'][0]
        return (f"找到相关信息: {top_result['topic']} ({top_result['category']})\n"
                f"描述: {top_result['description']}")
    else:
        return f"未找到相关信息: {query}"

@tool
def get_math_average(numbers: str) -> str:
    """计算数字列表的平均值

    Args:
        numbers: 用逗号分隔的数字，如 "1,2,3,4,5"
    """
    try:
        num_list = [float(x.strip()) for x in numbers.split(',')]
        result = asyncio.run(math_tool.execute(operation='average', numbers=num_list))
        if result.success:
            return f"平均值 {result.data['formatted']}"
        else:
            return f"计算失败: {result.error}"
    except Exception as e:
        return f"数字解析错误: {str(e)}"

class SimpleAgent:
    """简化的智能体实现，用于演示工具集成"""

    def __init__(self, model_provider: str = "anthropic"):
        self.model_provider = model_provider
        self.tools = [get_current_time, calculate_math, get_weather_info, search_knowledge, get_math_average]
        self.model = self._create_model()

    def _create_model(self):
        """创建模型实例"""
        if self.model_provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                print("⚠️ 未找到 ANTHROPIC_API_KEY，使用模拟模式")
                return None
            return ChatAnthropic(model="claude-3-sonnet-20240229", api_key=api_key)
        elif self.model_provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("⚠️ 未找到 OPENAI_API_KEY，使用模拟模式")
                return None
            return ChatOpenAI(model="gpt-3.5-turbo", api_key=api_key)
        else:
            print(f"⚠️ 不支持的模型提供商: {self.model_provider}")
            return None

    def run_with_tools(self, query: str) -> str:
        """使用工具运行查询"""
        if not self.model:
            return self._simulate_response(query)

        try:
            # 绑定工具到模型
            model_with_tools = self.model.bind_tools(self.tools)

            # 调用模型
            response = model_with_tools.invoke([
                HumanMessage(content=query)
            ])

            # 如果有工具调用，执行工具
            if hasattr(response, 'tool_calls') and response.tool_calls:
                tool_results = []
                for tool_call in response.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']

                    # 查找并执行工具
                    for tool in self.tools:
                        if tool.name == tool_name:
                            result = tool.invoke(tool_args)
                            tool_results.append(f"{tool.name}: {result}")
                            break

                if tool_results:
                    return "\n".join(tool_results)

            return response.content

        except Exception as e:
            # 如果API调用失败，回退到模拟模式
            print(f"⚠️ API调用失败: {str(e)}，使用模拟模式")
            return self._simulate_response(query)

    def _simulate_response(self, query: str) -> str:
        """模拟响应（当没有API密钥时）"""
        query_lower = query.lower()

        # 根据关键词选择合适的工具
        if any(word in query_lower for word in ['时间', '几点', '现在']):
            return get_current_time.invoke({})
        elif any(word in query_lower for word in ['计算', '加', '减', '乘', '除', '数学']):
            # 提取数字和运算符
            if '+' in query:
                try:
                    a, b = query.split('+')
                    a = float(''.join(filter(str.isdigit, a.strip())))
                    b = float(''.join(filter(str.isdigit, b.strip())))
                    return calculate_math.invoke({"expression": f"{a}+{b}"})
                except:
                    return "模拟数学计算结果: 42"
            return "模拟数学计算结果: 42"
        elif any(word in query_lower for word in ['天气', '气温', '下雨']):
            # 提取城市名
            for city in ['北京', '上海', '广州', '深圳', '杭州', '成都']:
                if city in query:
                    return get_weather_info.invoke({"location": city})
            return get_weather_info.invoke({"location": "北京"})
        elif any(word in query_lower for word in ['搜索', '查找', '什么']):
            return search_knowledge.invoke({"query": query})
        else:
            return f"模拟智能体响应: 我理解了您的问题 '{query}'，但由于缺少API密钥，我无法提供完整的智能回复。"

def demo_agent():
    """演示智能体功能"""
    print("🤖 新工具模块集成演示")
    print("=" * 50)

    # 创建智能体
    agent = SimpleAgent(model_provider="anthropic")

    # 测试用例
    test_cases = [
        "现在几点了？",
        "帮我计算 123 + 456",
        "北京今天天气怎么样？",
        "搜索一下python编程语言的信息",
        "计算 1,2,3,4,5 的平均值",
        "帮我计算 sqrt(144)",
        "上海天气如何？"
    ]

    print(f"🧪 测试 {len(test_cases)} 个用例:")
    print()

    for i, query in enumerate(test_cases, 1):
        print(f"📝 测试 {i}: {query}")
        response = agent.run_with_tools(query)
        print(f"🤖 回复: {response}")
        print("-" * 50)

    print("\n✅ 演示完成!")
    print("\n💡 说明:")
    print("- 如果配置了有效的API密钥，智能体会进行真正的推理")
    print("- 如果没有API密钥，会使用基于关键词的模拟响应")
    print("- 所有工具都来自新创建的工具模块")

if __name__ == "__main__":
    demo_agent()