#!/usr/bin/env python3
"""
测试钓鱼分析器在正常工作城市的表现
"""

import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from tools.fishing_analyzer import find_best_fishing_time
import json

async def test_fishing_success():
    """测试钓鱼分析器在正常城市的功能"""

    # 测试用例: 查询杭州本周日的钓鱼时间
    print("🎣 测试: 查询杭州本周日钓鱼时间")
    try:
        result_str = await find_best_fishing_time("杭州", "2025-11-09")
        result = json.loads(result_str)

        print("✅ 查询成功")
        print(f"📍 地点: {result['location']}")
        print(f"📅 日期: {result['date']}")

        if result['best_time_slots']:
            print("🏆 最佳时间段:")
            for i, (period, score) in enumerate(result['best_time_slots'], 1):
                print(f"  {i}. {period} - 评分: {score:.1f}/100")

        print(f"\n📊 详细分析:\n{result['detailed_analysis']}")
        print(f"\n💡 建议:\n{result['summary']}")

    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fishing_success())