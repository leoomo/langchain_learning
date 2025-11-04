#!/usr/bin/env python3
"""
测试钓鱼分析器的修复
"""

import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from tools.fishing_analyzer import find_best_fishing_time

async def test_fishing_analyzer():
    """测试钓鱼分析器"""

    # 测试用例1: 查询建德市本周日的钓鱼时间
    print("🎣 测试1: 查询建德市本周日钓鱼时间")
    try:
        result = await find_best_fishing_time("建德市", "2025-11-09")
        print("✅ 查询成功")
        print(f"结果: {result[:500]}...")  # 显示前500个字符
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*50 + "\n")

    # 测试用例2: 查询北京明天的钓鱼时间
    print("🎣 测试2: 查询北京明天钓鱼时间")
    try:
        result = await find_best_fishing_time("北京", None)  # None表示明天
        print("✅ 查询成功")
        print(f"结果: {result[:500]}...")  # 显示前500个字符
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fishing_analyzer())