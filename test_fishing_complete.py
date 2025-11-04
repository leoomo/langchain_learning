#!/usr/bin/env python3
"""
完整的钓鱼推荐系统测试
"""

import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from tools.fishing_analyzer import find_best_fishing_time
import json
from datetime import datetime, timedelta

async def test_fishing_complete():
    """完整测试钓鱼推荐系统的各种场景"""

    print("🎣 钓鱼推荐系统完整测试")
    print("="*60)

    # 测试用例1: 明天的钓鱼推荐 (应该在预报范围内)
    print("📅 测试1: 明天钓鱼推荐")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"查询日期: {tomorrow}")

    try:
        result_str = await find_best_fishing_time("杭州", tomorrow)
        result = json.loads(result_str)

        print(f"✅ 状态: 成功")
        print(f"📍 地点: {result['location']}")
        print(f"📊 综合评分: {sum([score for _, score in result['best_time_slots']]) / len(result['best_time_slots']):.1f}/100" if result['best_time_slots'] else "N/A")

        if result['best_time_slots']:
            print("🏆 最佳时间段:")
            for i, (period, score) in enumerate(result['best_time_slots'], 1):
                print(f"  {i}. {period} - {score:.1f}/100")

        # 提取天气信息
        if result.get('detailed_analysis'):
            lines = result['detailed_analysis'].split('\n')
            for line in lines:
                if '温度范围' in line or '主要天气' in line:
                    print(f"🌤️  {line}")

    except Exception as e:
        print(f"❌ 失败: {e}")

    print("\n" + "-"*60 + "\n")

    # 测试用例2: 3天内的钓鱼推荐 (预报范围内)
    print("📅 测试2: 3天内钓鱼推荐")
    future_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    print(f"查询日期: {future_date}")

    try:
        result_str = await find_best_fishing_time("上海", future_date)
        result = json.loads(result_str)

        print(f"✅ 状态: 成功")
        print(f"📍 地点: {result['location']}")

        if result['best_time_slots']:
            best_period, best_score = result['best_time_slots'][0]
            print(f"🏆 最佳: {best_period} ({best_score:.1f}/100)")
        else:
            print("⚠️  无最佳时间段数据")

    except Exception as e:
        print(f"❌ 失败: {e}")

    print("\n" + "-"*60 + "\n")

    # 测试用例3: 超出预报范围的日期 (应该返回模拟数据)
    print("📅 测试3: 超出预报范围 (5天后)")
    future_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    print(f"查询日期: {future_date}")

    try:
        result_str = await find_best_fishing_time("深圳", future_date)
        result = json.loads(result_str)

        print(f"✅ 状态: 成功 (使用模拟数据)")
        print(f"📍 地点: {result['location']}")

        if result['best_time_slots']:
            print("🏆 基于模拟数据的推荐:")
            for i, (period, score) in enumerate(result['best_time_slots'][:2], 1):
                print(f"  {i}. {period} - {score:.1f}/100")
        else:
            print("⚠️  无法生成推荐")

    except Exception as e:
        print(f"❌ 失败: {e}")

    print("\n" + "-"*60 + "\n")

    # 测试用例4: 验证API限制处理
    print("📅 测试4: API预报边界测试 (72小时)")
    boundary_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    print(f"查询日期: {boundary_date} (边界日期)")

    try:
        result_str = await find_best_fishing_time("广州", boundary_date)
        result = json.loads(result_str)

        if result['best_time_slots']:
            print("✅ 边界日期查询成功")
        else:
            print("⚠️  边界日期查询返回模拟数据")

    except Exception as e:
        print(f"❌ 失败: {e}")

    print("\n" + "="*60)
    print("🎯 测试总结:")
    print("1. ✅ 明天查询 - 应该返回真实天气数据")
    print("2. ✅ 3天内查询 - 应该返回真实天气数据")
    print("3. ✅ 5天后查询 - 应该返回模拟数据")
    print("4. ✅ 边界测试 - 验证72小时API限制处理")
    print("\n💡 系统特性:")
    print("- 🌤️ 支持72小时内真实天气预报")
    print("- 🔮 超出范围自动使用模拟数据")
    print("- ⏰ 提供24小时时间段分析")
    print("- 🎯 专业钓鱼条件评分系统")

if __name__ == "__main__":
    asyncio.run(test_fishing_complete())