#!/usr/bin/env python3
"""
测试智能天气路由功能
"""

import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from tools.fishing_analyzer import find_best_fishing_time
import json
from datetime import datetime, timedelta

async def test_intelligent_routing():
    """测试智能路由功能"""
    print("🚀 测试智能天气路由功能")
    print("=" * 60)

    # 测试用例1: 今天 (应该使用逐小时API)
    print("📅 测试1: 今天钓鱼推荐")
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        result_json = await find_best_fishing_time("杭州", today)
        result = json.loads(result_json)
        
        print(f"✅ 地点: {result['location']}")
        print(f"📅 日期: {result['date']}")
        print(f"🏆 最佳时间段: {result['best_time_slots'][:3]}")
        print(f"📊 数据源: {result.get('metadata', {}).get('operation', 'unknown')}")
        
    except Exception as e:
        print(f"❌ 失败: {e}")

    print("\n" + "-" * 40 + "\n")

    # 测试用例2: 3天后 (应该使用逐天API)
    print("📅 测试2: 3天后钓鱼推荐")
    try:
        future_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        result_json = await find_best_fishing_time("上海", future_date)
        result = json.loads(result_json)
        
        print(f"✅ 地点: {result['location']}")
        print(f"📅 日期: {result['date']}")
        print(f"🏆 最佳时间段: {result['best_time_slots'][:2]}")
        print(f"📊 数据源: {result.get('metadata', {}).get('operation', 'unknown')}")
        
    except Exception as e:
        print(f"❌ 失败: {e}")

    print("\n" + "-" * 40 + "\n")

    # 测试用例3: 10天后 (应该使用模拟数据)
    print("📅 测试3: 10天后钓鱼推荐")
    try:
        future_date = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
        result_json = await find_best_fishing_time("深圳", future_date)
        result = json.loads(result_json)
        
        print(f"✅ 地点: {result['location']}")
        print(f"📅 日期: {result['date']}")
        print(f"🏆 最佳时间段: {result['best_time_slots'][:2]}")
        print(f"📊 数据源: {result.get('metadata', {}).get('operation', 'unknown')}")
        
    except Exception as e:
        print(f"❌ 失败: {e}")

    print("\n" + "=" * 60)
    print("🎯 测试完成!")

if __name__ == "__main__":
    asyncio.run(test_intelligent_routing())