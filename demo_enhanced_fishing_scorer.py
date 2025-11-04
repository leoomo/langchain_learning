#!/usr/bin/env python3
"""
增强钓鱼评分器演示脚本
展示7因子评分系统相比3因子系统的改进
"""

import sys
import os
from datetime import datetime, timedelta
import asyncio

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__)))

from tools.enhanced_fishing_scorer import EnhancedFishingScorer, FishingScore
from tools.fishing_analyzer import FishingAnalyzer


def demonstrate_enhanced_scoring():
    """演示增强评分系统"""
    print("🎣 增强钓鱼评分器演示")
    print("="*60)

    # 创建评分器
    scorer = EnhancedFishingScorer()
    print(f"📊 权重分配: {scorer.weights}")
    print()

    # 示例1: 理想钓鱼条件
    print("🌟 示例1: 理想钓鱼条件")
    print("-" * 40)
    ideal_conditions = {
        'datetime': '2024-11-06T07:00:00',
        'temperature': 20.0,  # 最佳温度
        'condition': '多云',    # 最佳天气
        'wind_speed': 5.0,     # 最佳风速
        'humidity': 65.0,      # 理想湿度
        'pressure': 1015.0     # 最佳气压
    }

    # 稳定历史数据（最佳条件）
    stable_historical = [
        {'pressure': 1015, 'temperature': 18, 'wind_speed': 4},
        {'pressure': 1015, 'temperature': 19, 'wind_speed': 4.5},
        {'pressure': 1015, 'temperature': 19.5, 'wind_speed': 5},
        {'pressure': 1015, 'temperature': 20, 'wind_speed': 5},
        {'pressure': 1015, 'temperature': 20, 'wind_speed': 5},
        {'pressure': 1015, 'temperature': 19.8, 'wind_speed': 4.8}
    ]

    date = datetime(2024, 11, 6, 7, 0)
    score = scorer.calculate_comprehensive_score(ideal_conditions, stable_historical, date)

    print(f"天气条件: {ideal_conditions['temperature']:.1f}°C, {ideal_conditions['condition']}, 风力{ideal_conditions['wind_speed']}km/h")
    print(f"综合评分: {score.overall:.1f}/100")
    print(f"详细评分:")
    print(f"  温度: {score.temperature:.1f} (权重: {score.breakdown['temperature']:.1%})")
    print(f"  天气: {score.weather:.1f} (权重: {score.breakdown['weather']:.1%})")
    print(f"  风力: {score.wind:.1f} (权重: {score.breakdown['wind']:.1%})")
    print(f"  气压: {score.pressure:.1f} (权重: {score.breakdown['pressure']:.1%})")
    print(f"  湿度: {score.humidity:.1f} (权重: {score.breakdown['humidity']:.1%})")
    print(f"  季节: {score.seasonal:.1f} (权重: {score.breakdown['seasonal']:.1%})")
    print(f"  月相: {score.lunar:.1f} (权重: {score.breakdown['lunar']:.1%})")

    if score.analysis_details:
        print(f"分析详情:")
        print(f"  气压趋势: {score.analysis_details.get('pressure_trend', 'unknown')}")
        print(f"  温度变化: {score.analysis_details.get('temperature_change', 0):.1f}°C")
        print(f"  风速稳定性: {score.analysis_details.get('wind_stability', 'unknown')}")
        print(f"  月相: {score.analysis_details.get('lunar_phase', 'unknown')}")
        print(f"  季节: {score.analysis_details.get('seasonal_factor', 'unknown')}")
    print()

    # 示例2: 下降气压（钓鱼黄金期）
    print("⭐ 示例2: 下降气压（钓鱼黄金期）")
    print("-" * 40)
    falling_pressure_conditions = {
        'datetime': '2024-11-06T14:00:00',
        'temperature': 22.0,
        'condition': '阴',
        'wind_speed': 8.0,
        'humidity': 75.0,
        'pressure': 1008.0  # 下降气压
    }

    # 下降气压历史数据
    falling_historical = [
        {'pressure': 1018, 'temperature': 20, 'wind_speed': 6},
        {'pressure': 1016, 'temperature': 20.5, 'wind_speed': 6.5},
        {'pressure': 1014, 'temperature': 21, 'wind_speed': 7},
        {'pressure': 1012, 'temperature': 21.5, 'wind_speed': 7.5},
        {'pressure': 1010, 'temperature': 21.8, 'wind_speed': 8},
        {'pressure': 1008, 'temperature': 22, 'wind_speed': 8}
    ]

    date = datetime(2024, 11, 6, 14, 0)
    score2 = scorer.calculate_comprehensive_score(falling_pressure_conditions, falling_historical, date)

    print(f"天气条件: {falling_pressure_conditions['temperature']:.1f}°C, {falling_pressure_conditions['condition']}, 风力{falling_pressure_conditions['wind_speed']}km/h")
    print(f"气压趋势: {score2.analysis_details.get('pressure_trend', 'unknown')} (从1018hPa降至1008hPa)")
    print(f"综合评分: {score2.overall:.1f}/100")
    print(f"气压评分: {score2.pressure:.1f} (下降气压奖励!)")
    print()

    # 示例3: 对比相似条件下的评分差异
    print("🔍 示例3: 相似条件下的评分对比")
    print("-" * 40)

    # 相似但不同的条件
    condition_a = {
        'datetime': '2024-11-06T09:00:00',
        'temperature': 18.5,
        'condition': '多云',
        'wind_speed': 3.2,
        'humidity': 62.0,
        'pressure': 1013.0
    }

    condition_b = {
        'datetime': '2024-11-06T14:00:00',
        'temperature': 23.7,
        'condition': '多云',
        'wind_speed': 2.8,
        'humidity': 68.0,
        'pressure': 1011.0
    }

    condition_c = {
        'datetime': '2024-11-06T17:00:00',
        'temperature': 23.1,
        'condition': '多云',
        'wind_speed': 1.1,
        'humidity': 70.0,
        'pressure': 1009.0  # 最低气压
    }

    # 使用相似的历史数据
    similar_historical = falling_historical

    date_a = datetime(2024, 11, 6, 9, 0)
    date_b = datetime(2024, 11, 6, 14, 0)
    date_c = datetime(2024, 11, 6, 17, 0)

    score_a = scorer.calculate_comprehensive_score(condition_a, similar_historical, date_a)
    score_b = scorer.calculate_comprehensive_score(condition_b, similar_historical, date_b)
    score_c = scorer.calculate_comprehensive_score(condition_c, similar_historical, date_c)

    print("时间段对比:")
    print(f"  上午: {score_a.overall:.1f}分 - {condition_a['temperature']:.1f}°C, 风力{condition_a['wind_speed']}km/h, 气压{condition_a['pressure']}hPa")
    print(f"  中午: {score_b.overall:.1f}分 - {condition_b['temperature']:.1f}°C, 风力{condition_b['wind_speed']}km/h, 气压{condition_b['pressure']}hPa")
    print(f"  下午: {score_c.overall:.1f}分 - {condition_c['temperature']:.1f}°C, 风力{condition_c['wind_speed']}km/h, 气压{condition_c['pressure']}hPa")

    # 显示评分差异
    max_score = max(score_a.overall, score_b.overall, score_c.overall)
    min_score = min(score_a.overall, score_b.overall, score_c.overall)
    print(f"评分差异: {max_score - min_score:.1f}分 (解决了传统86分问题!)")
    print()

    # 示例4: 展示评分分解功能
    print("📈 示例4: 评分权重分解分析")
    print("-" * 40)
    breakdown = scorer.get_score_breakdown(score_c)

    print("权重贡献分析:")
    for factor, analysis in breakdown['weight_analysis'].items():
        factor_name = {
            'temperature': '温度',
            'weather': '天气',
            'wind': '风力',
            'pressure': '气压',
            'humidity': '湿度',
            'seasonal': '季节',
            'lunar': '月相'
        }.get(factor, factor)

        print(f"  {factor_name}: {analysis['score']:.1f} × {analysis['weight']:.1%} = {analysis['contribution']:.1f} ({analysis['contribution_percentage']:.1f}%)")


def compare_scoring_systems():
    """对比3因子和7因子评分系统"""
    print("\n🆚 评分系统对比")
    print("="*60)

    # 测试条件
    test_conditions = {
        'datetime': '2024-11-06T14:00:00',
        'temperature': 22.0,
        'condition': '阴',
        'wind_speed': 8.0,
        'humidity': 75.0,
        'pressure': 1008.0
    }

    test_historical = [
        {'pressure': 1018, 'temperature': 20, 'wind_speed': 6},
        {'pressure': 1016, 'temperature': 20.5, 'wind_speed': 6.5},
        {'pressure': 1014, 'temperature': 21, 'wind_speed': 7},
        {'pressure': 1012, 'temperature': 21.5, 'wind_speed': 7.5},
        {'pressure': 1010, 'temperature': 21.8, 'wind_speed': 8},
        {'pressure': 1008, 'temperature': 22, 'wind_speed': 8}
    ]

    date = datetime(2024, 11, 6, 14, 0)

    # 7因子增强评分
    enhanced_scorer = EnhancedFishingScorer()
    enhanced_score = enhanced_scorer.calculate_comprehensive_score(test_conditions, test_historical, date)

    # 计算3因子传统评分（模拟）
    temp_3factor = enhanced_scorer._calculate_temperature_score(test_conditions['temperature'])
    weather_3factor = enhanced_scorer._calculate_weather_score(test_conditions['condition'])
    wind_3factor = enhanced_scorer._calculate_wind_score(test_conditions['wind_speed'])
    traditional_3factor_score = temp_3factor * 0.4 + weather_3factor * 0.35 + wind_3factor * 0.25

    print("📊 评分结果对比:")
    print(f"  传统3因子系统: {traditional_3factor_score:.1f}/100")
    print(f"    - 温度: {temp_3factor:.1f} × 40% = {temp_3factor * 0.4:.1f}")
    print(f"    - 天气: {weather_3factor:.1f} × 35% = {weather_3factor * 0.35:.1f}")
    print(f"    - 风力: {wind_3factor:.1f} × 25% = {wind_3factor * 0.25:.1f}")
    print()
    print(f"  增强7因子系统: {enhanced_score.overall:.1f}/100")
    print(f"    - 温度: {enhanced_score.temperature:.1f} × {enhanced_score.breakdown['temperature']:.1%} = {enhanced_score.temperature * enhanced_score.breakdown['temperature']:.1f}")
    print(f"    - 天气: {enhanced_score.weather:.1f} × {enhanced_score.breakdown['weather']:.1%} = {enhanced_score.weather * enhanced_score.breakdown['weather']:.1f}")
    print(f"    - 风力: {enhanced_score.wind:.1f} × {enhanced_score.breakdown['wind']:.1%} = {enhanced_score.wind * enhanced_score.breakdown['wind']:.1f}")
    print(f"    - 气压: {enhanced_score.pressure:.1f} × {enhanced_score.breakdown['pressure']:.1%} = {enhanced_score.pressure * enhanced_score.breakdown['pressure']:.1f}")
    print(f"    - 湿度: {enhanced_score.humidity:.1f} × {enhanced_score.breakdown['humidity']:.1%} = {enhanced_score.humidity * enhanced_score.breakdown['humidity']:.1f}")
    print(f"    - 季节: {enhanced_score.seasonal:.1f} × {enhanced_score.breakdown['seasonal']:.1%} = {enhanced_score.seasonal * enhanced_score.breakdown['seasonal']:.1f}")
    print(f"    - 月相: {enhanced_score.lunar:.1f} × {enhanced_score.breakdown['lunar']:.1%} = {enhanced_score.lunar * enhanced_score.breakdown['lunar']:.1f}")
    print()

    improvement = enhanced_score.overall - traditional_3factor_score
    print(f"🎯 改进效果: {improvement:+.1f}分")
    print(f"   更精细的评分反映了更多专业因素")


async def demo_integrated_fishing_analyzer():
    """演示集成的钓鱼分析器"""
    print("\n🔧 集成钓鱼分析器演示")
    print("="*60)

    # 设置环境变量启用增强评分
    os.environ['ENABLE_ENHANCED_FISHING_SCORING'] = 'true'

    analyzer = FishingAnalyzer()
    print(f"增强评分状态: {'启用' if analyzer.use_enhanced_scoring else '禁用'}")

    # 模拟钓鱼推荐查询
    print("\n📍 模拟钓鱼查询: 建德市 2024-11-06")
    try:
        # 使用模拟数据进行演示
        print("正在分析钓鱼条件...")

        # 创建一些模拟的小时数据进行演示
        mock_hourly_data = []
        for hour in range(6, 19):  # 6点到18点
            conditions = analyzer.analyze_hourly_condition(
                {
                    'datetime': f'2024-11-06T{hour:02d}:00:00',
                    'temperature': 18 + (hour - 6) * 0.6,
                    'condition': '多云' if hour < 12 else '阴',
                    'wind_speed': 5 + (hour - 12) * 0.3 if hour > 12 else 5 - (6 - hour) * 0.2,
                    'humidity': 65 + (hour - 12) * 2 if hour > 12 else 65,
                    'pressure': 1015 - (hour - 6) * 0.8  # 下降气压
                },
                historical_data=[{'pressure': 1020 - i * 0.5} for i in range(hour)],
                date=datetime(2024, 11, 6, hour, 0)
            )
            mock_hourly_data.append(conditions)

        # 按时间段分组
        period_scores = {}
        for condition in mock_hourly_data:
            period = condition.period_name
            if period not in period_scores:
                period_scores[period] = []
            # 使用增强评分或传统评分
            score = condition.enhanced_score.overall if condition.is_enhanced and condition.enhanced_score else condition.overall_score
            period_scores[period].append(score)

        # 计算平均评分
        period_avg_scores = {}
        for period, scores in period_scores.items():
            avg_score = sum(scores) / len(scores)
            period_avg_scores[period] = avg_score

        # 排序
        sorted_periods = sorted(period_avg_scores.items(), key=lambda x: x[1], reverse=True)

        print("🎯 最佳钓鱼时间推荐:")
        for i, (period, score) in enumerate(sorted_periods[:3], 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
            enhanced_indicator = "✨" if mock_hourly_data and mock_hourly_data[0].is_enhanced else ""
            print(f"  {emoji} {period}: {score:.1f}分 {enhanced_indicator}")

        print(f"\n💡 使用了{len(mock_hourly_data)}个数据点进行分析")
        print(f"   评分模式: {'增强7因子系统' if mock_hourly_data and mock_hourly_data[0].is_enhanced else '传统3因子系统'}")

    except Exception as e:
        print(f"演示过程出现错误: {e}")


if __name__ == "__main__":
    print("🎣 增强钓鱼评分器完整演示")
    print("基于OpenSpec提案: optimize-fishing-recommendation-weights")
    print("="*70)

    demonstrate_enhanced_scoring()
    compare_scoring_systems()
    asyncio.run(demo_integrated_fishing_analyzer())

    print("\n✨ 演示完成!")
    print("主要改进:")
    print("  1. 评分维度从3个增加到7个")
    print("  2. 解决了传统86分问题，提供更好的区分度")
    print("  3. 基于专业钓鱼研究，更科学准确")
    print("  4. 支持向后兼容，可渐进式部署")
    print("  5. 提供详细的评分分解和分析")