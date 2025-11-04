#!/usr/bin/env python3
"""
运行同步版本的天气工具 - 解决模块导入问题
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.langchain_weather_tools_sync import (
    query_current_weather,
    query_weather_by_date,
    query_weather_by_datetime,
    query_hourly_forecast
)

def main():
    """主函数"""
    print("🌤️  同步版本天气工具测试")
    print("=" * 50)

    # 测试当前天气
    print("\n1. 测试查询当前天气...")
    try:
        result = query_current_weather.invoke({'place': '杭州'})
        print(f"✅ 成功: {result}")
    except Exception as e:
        print(f"❌ 失败: {e}")

    # 测试钓鱼推荐
    print("\n2. 测试钓鱼时间推荐...")
    try:
        from tools.langchain_weather_tools_sync import query_fishing_recommendation
        result = query_fishing_recommendation.invoke({'location': '富阳区', 'date': '2025-11-06'})
        print(f"✅ 成功: {result[:200]}..." if len(result) > 200 else f"✅ 成功: {result}")
    except Exception as e:
        print(f"❌ 失败: {e}")

    print("\n🎉 测试完成！")

if __name__ == "__main__":
    main()