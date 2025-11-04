#!/usr/bin/env python3
"""
直接测试智能路由组件
"""

import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / "services"))

from weather.datetime_weather_service import DateTimeWeatherService
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

async def test_direct_router():
    """直接测试DateTimeWeatherService的智能路由功能"""
    print("🚀 直接测试智能路由组件")
    print("=" * 60)

    try:
        # 加载API密钥
        load_dotenv()
        api_key = os.getenv('CAIYUN_API_KEY')
        
        if not api_key:
            print("❌ CAIYUN_API_KEY未设置")
            return

        # 创建服务实例
        weather_service = DateTimeWeatherService(api_key=api_key)
        
        # 测试用例1: 今天
        print("📅 测试1: 今天天气")
        try:
            location_info = {
                'name': '杭州',
                'lng': 120.2,
                'lat': 30.3
            }
            today = datetime.now().strftime("%Y-%m-%d")
            
            weather_data, status_message, error_code = await weather_service.get_forecast_by_range(location_info, today)
            
            if weather_data:
                print(f"✅ 成功: {status_message}")
                print(f"📍 地点: {weather_data.location}")
                print(f"🌡️  温度: {weather_data.temperature}°C")
                print(f"🌤️  天气: {weather_data.condition}")
                print(f"📊 数据源: {weather_data.data_source}")
                print(f"📈 置信度: {weather_data.confidence}")
            else:
                print(f"❌ 失败: {status_message}")
                
        except Exception as e:
            print(f"❌ 异常: {e}")

        print("\n" + "-" * 40 + "\n")

        # 测试用例2: 5天后 (应该使用逐天API)
        print("📅 测试2: 5天后天气")
        try:
            future_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
            
            weather_data, status_message, error_code = await weather_service.get_forecast_by_range(location_info, future_date)
            
            if weather_data:
                print(f"✅ 成功: {status_message}")
                print(f"📍 地点: {weather_data.location}")
                print(f"🌡️  温度: {weather_data.temperature}°C")
                print(f"🌤️  天气: {weather_data.condition}")
                print(f"📊 数据源: {weather_data.data_source}")
                print(f"📈 置信度: {weather_data.confidence}")
            else:
                print(f"❌ 失败: {status_message}")
                
        except Exception as e:
            print(f"❌ 异常: {e}")

        print("\n" + "-" * 40 + "\n")

        # 测试用例3: 10天后 (应该使用模拟数据)
        print("📅 测试3: 10天后天气")
        try:
            far_future_date = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
            
            weather_data, status_message, error_code = await weather_service.get_forecast_by_range(location_info, far_future_date)
            
            if weather_data:
                print(f"✅ 成功: {status_message}")
                print(f"📍 地点: {weather_data.location}")
                print(f"🌡️  温度: {weather_data.temperature}°C")
                print(f"🌤️  天气: {weather_data.condition}")
                print(f"📊 数据源: {weather_data.data_source}")
                print(f"📈 置信度: {weather_data.confidence}")
            else:
                print(f"❌ 失败: {status_message}")
                
        except Exception as e:
            print(f"❌ 异常: {e}")

        print("\n" + "=" * 60)
        print("🎯 路由健康检查:")
        
        # 健康检查
        health_status = weather_service.health_check_router()
        print(f"路由器状态: {health_status.get('status', 'unknown')}")
        
        # 统计信息
        stats = weather_service.get_router_stats()
        print(f"总请求数: {stats.get('total_requests', 0)}")
        print(f"hourly请求: {stats.get('hourly_requests', 0)}")
        print(f"daily请求: {stats.get('daily_requests', 0)}")
        print(f"simulation请求: {stats.get('simulation_requests', 0)}")

    except Exception as e:
        print(f"❌ 初始化失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_direct_router())