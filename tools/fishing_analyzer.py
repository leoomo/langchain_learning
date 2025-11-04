#!/usr/bin/env python3
"""
钓鱼分析工具
基于天气数据分析最佳的钓鱼时间
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

# 导入现有的天气工具
try:
    from .weather_tool import WeatherTool
    from ..services.weather.enhanced_weather_service import EnhancedCaiyunWeatherService
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    from weather_tool import WeatherTool
    sys.path.append(str(Path(__file__).parent.parent))
    from services.weather.enhanced_weather_service import EnhancedCaiyunWeatherService


@dataclass
class FishingCondition:
    """钓鱼条件数据"""
    hour: int                    # 小时 (0-23)
    temperature: float           # 温度 (°C)
    condition: str              # 天气状况
    wind_speed: float           # 风速 (km/h)
    humidity: float             # 湿度 (%)
    pressure: float             # 气压 (hPa)

    # 钓鱼适宜性评分 (0-100)
    temperature_score: float    # 温度评分
    weather_score: float        # 天气评分
    wind_score: float          # 风力评分
    overall_score: float       # 综合评分

    # 时间段名称
    period_name: str           # 时间段名称（如"早上"、"上午"等）


@dataclass
class FishingRecommendation:
    """钓鱼推荐结果"""
    location: str                              # 地点
    date: str                                  # 日期
    best_time_slots: List[Tuple[str, float]]   # 最佳时间段 (时间段名称, 评分)
    detailed_analysis: str                     # 详细分析
    hourly_conditions: List[FishingCondition] # 每小时条件
    summary: str                               # 总结建议

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "location": self.location,
            "date": self.date,
            "best_time_slots": [(period, score) for period, score in self.best_time_slots],
            "detailed_analysis": self.detailed_analysis,
            "hourly_conditions": [
                {
                    "hour": cond.hour,
                    "period_name": cond.period_name,
                    "temperature": cond.temperature,
                    "condition": cond.condition,
                    "overall_score": cond.overall_score
                } for cond in self.hourly_conditions
            ],
            "summary": self.summary
        }


class FishingAnalyzer:
    """钓鱼条件分析器"""

    def __init__(self):
        """初始化钓鱼分析器"""
        # 使用增强版天气服务，支持高德API坐标查询
        self.weather_tool = WeatherTool()
        self.enhanced_weather_service = EnhancedCaiyunWeatherService()

        # 钓鱼最佳条件参数
        self.optimal_temp_range = (15, 25)        # 最佳温度范围
        self.optimal_wind_speed = (0, 15)         # 最佳风速范围
        self.preferred_weather = ["晴", "多云", "阴", "小雨"]  # 偏好天气

        # 时间段定义
        self.time_periods = {
            "深夜": (0, 5),
            "早上": (5, 9),
            "上午": (9, 12),
            "中午": (12, 14),
            "下午": (14, 18),
            "傍晚": (18, 21),
            "晚上": (21, 24)
        }

    def get_time_period(self, hour: int) -> str:
        """获取小时对应的时间段"""
        for period, (start, end) in self.time_periods.items():
            if start <= hour < end:
                return period
        return "深夜"

    def calculate_temperature_score(self, temperature: float) -> float:
        """
        计算温度评分

        Args:
            temperature: 温度 (°C)

        Returns:
            温度评分 (0-100)
        """
        min_temp, max_temp = self.optimal_temp_range

        if min_temp <= temperature <= max_temp:
            # 在最佳范围内，给满分
            return 100.0
        elif temperature < min_temp:
            # 低于最佳范围，线性递减
            if temperature < 0:
                return 0.0
            ratio = temperature / min_temp
            return max(0.0, ratio * 80)  # 最低0分，最高80分
        else:
            # 高于最佳范围，线性递减
            if temperature > 35:
                return 0.0
            excess = temperature - max_temp
            ratio = max(0, 1 - excess / 10)  # 超过10度给0分
            return ratio * 80  # 最低0分，最高80分

    def calculate_weather_score(self, condition: str) -> float:
        """
        计算天气评分

        Args:
            condition: 天气状况

        Returns:
            天气评分 (0-100)
        """
        condition = condition.lower()

        # 最佳天气
        best_weather = ["多云", "阴"]
        for weather in best_weather:
            if weather in condition:
                return 100.0

        # 良好天气
        good_weather = ["晴", "小雨"]
        for weather in good_weather:
            if weather in condition:
                return 85.0

        # 一般天气
        fair_weather = ["中雨"]
        for weather in fair_weather:
            if weather in condition:
                return 50.0

        # 较差天气
        poor_weather = ["大雨", "暴雨", "雷阵雨"]
        for weather in poor_weather:
            if weather in condition:
                return 20.0

        # 极差天气
        terrible_weather = ["雪", "冰雹", "雾", "霾"]
        for weather in terrible_weather:
            if weather in condition:
                return 10.0

        # 未知天气，给中等分数
        return 60.0

    def calculate_wind_score(self, wind_speed: float) -> float:
        """
        计算风力评分

        Args:
            wind_speed: 风速 (km/h)

        Returns:
            风力评分 (0-100)
        """
        min_wind, max_wind = self.optimal_wind_speed

        if min_wind <= wind_speed <= max_wind:
            # 在最佳范围内
            return 100.0
        elif wind_speed < min_wind:
            # 风太小，影响钓饵传播
            return 85.0
        else:
            # 风太大，影响钓鱼
            if wind_speed > 30:
                return 10.0
            excess = wind_speed - max_wind
            ratio = max(0, 1 - excess / 15)  # 超过15km/h开始快速递减
            return ratio * 80

    def analyze_hourly_condition(self, hourly_data: Dict) -> FishingCondition:
        """
        分析单小时的钓鱼条件

        Args:
            hourly_data: 小时天气数据

        Returns:
            钓鱼条件评分
        """
        # 提取天气数据
        hour = datetime.fromisoformat(hourly_data.get("datetime", "").replace("Z", "+00:00")).hour
        temperature = hourly_data.get("temperature", 0)
        condition = hourly_data.get("condition", "")
        wind_speed = hourly_data.get("wind_speed", 0)
        humidity = hourly_data.get("humidity", 0)
        pressure = hourly_data.get("pressure", 0)

        # 计算各项评分
        temp_score = self.calculate_temperature_score(temperature)
        weather_score = self.calculate_weather_score(condition)
        wind_score = self.calculate_wind_score(wind_speed)

        # 综合评分 (加权平均)
        overall_score = (
            temp_score * 0.4 +      # 温度权重40%
            weather_score * 0.35 +  # 天气权重35%
            wind_score * 0.25       # 风力权重25%
        )

        period_name = self.get_time_period(hour)

        return FishingCondition(
            hour=hour,
            temperature=temperature,
            condition=condition,
            wind_speed=wind_speed,
            humidity=humidity,
            pressure=pressure,
            temperature_score=temp_score,
            weather_score=weather_score,
            wind_score=wind_score,
            overall_score=overall_score,
            period_name=period_name
        )

    async def find_best_fishing_time(self, location: str, date: str = None) -> FishingRecommendation:
        """
        找出最佳的钓鱼时间

        Args:
            location: 地点
            date: 日期 (YYYY-MM-DD格式，如果为None则查询明天)

        Returns:
            钓鱼推荐结果
        """
        try:
            # 如果没有指定日期，默认查询明天
            if date is None:
                tomorrow = datetime.now() + timedelta(days=1)
                date = tomorrow.strftime("%Y-%m-%d")

            # 获取小时级天气预报
            result = await self.weather_tool.execute(
                operation="hourly_forecast",
                location=location,
                hours=24
            )

            if not result.success:
                return FishingRecommendation(
                    location=location,
                    date=date,
                    best_time_slots=[],
                    detailed_analysis=f"无法获取天气数据: {result.error}",
                    hourly_conditions=[],
                    summary="建议查询其他日期或地点"
                )

            # 分析每小时的条件
            hourly_conditions = []
            hourly_data = result.data.get("hourly_data", [])

            for data in hourly_data:
                condition = self.analyze_hourly_condition(data)
                hourly_conditions.append(condition)

            # 按时间段分组并找出最佳时间
            period_scores = {}
            for condition in hourly_conditions:
                period = condition.period_name
                if period not in period_scores:
                    period_scores[period] = []
                period_scores[period].append(condition.overall_score)

            # 计算每个时间段的平均评分
            period_avg_scores = {}
            for period, scores in period_scores.items():
                avg_score = sum(scores) / len(scores)
                period_avg_scores[period] = avg_score

            # 排序找出最佳时间段
            sorted_periods = sorted(
                period_avg_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )

            best_time_slots = sorted_periods[:3]  # 取前3个最佳时间段

            # 生成详细分析
            detailed_analysis = self._generate_detailed_analysis(
                hourly_conditions, sorted_periods
            )

            # 生成总结建议
            summary = self._generate_summary(best_time_slots, hourly_conditions)

            return FishingRecommendation(
                location=location,
                date=date,
                best_time_slots=best_time_slots,
                detailed_analysis=detailed_analysis,
                hourly_conditions=hourly_conditions,
                summary=summary
            )

        except Exception as e:
            return FishingRecommendation(
                location=location,
                date=date or "未知",
                best_time_slots=[],
                detailed_analysis=f"分析过程中出现错误: {str(e)}",
                hourly_conditions=[],
                summary="建议稍后重试或咨询其他信息源"
            )

    def _generate_detailed_analysis(self, hourly_conditions: List[FishingCondition],
                                  sorted_periods: List[Tuple[str, float]]) -> str:
        """生成详细分析"""
        if not hourly_conditions:
            return "无天气数据可供分析"

        analysis_parts = []

        # 总体评价
        avg_score = sum(c.overall_score for c in hourly_conditions) / len(hourly_conditions)
        if avg_score >= 80:
            overall = "非常适合钓鱼"
        elif avg_score >= 60:
            overall = "比较适合钓鱼"
        elif avg_score >= 40:
            overall = "一般适合钓鱼"
        else:
            overall = "不太适合钓鱼"

        analysis_parts.append(f"**总体评价**: {overall} (综合评分: {avg_score:.1f}/100)")

        # 最佳时间段
        if sorted_periods:
            best_period, best_score = sorted_periods[0]
            analysis_parts.append(f"**最佳时间段**: {best_period} (评分: {best_score:.1f}/100)")

        # 温度分析
        temps = [c.temperature for c in hourly_conditions]
        min_temp, max_temp = min(temps), max(temps)
        analysis_parts.append(f"**温度范围**: {min_temp:.1f}°C - {max_temp:.1f}°C")

        # 天气状况
        conditions = [c.condition for c in hourly_conditions]
        condition_count = {}
        for condition in conditions:
            condition_count[condition] = condition_count.get(condition, 0) + 1
        main_condition = max(condition_count, key=condition_count.get)
        analysis_parts.append(f"**主要天气**: {main_condition}")

        return "\n".join(analysis_parts)

    def _generate_summary(self, best_time_slots: List[Tuple[str, float]],
                         hourly_conditions: List[FishingCondition]) -> str:
        """生成总结建议"""
        if not best_time_slots:
            return "今日天气条件不适宜钓鱼，建议改日进行。"

        summary_parts = []

        # 推荐最佳时间
        if best_time_slots:
            best_period, best_score = best_time_slots[0]
            if best_score >= 80:
                summary_parts.append(f"**强烈推荐**在{best_period}钓鱼，条件极佳！")
            elif best_score >= 60:
                summary_parts.append(f"**推荐**在{best_period}钓鱼，条件良好。")
            else:
                summary_parts.append(f"可以考虑在{best_period}钓鱼，但条件一般。")

        # 次佳选择
        if len(best_time_slots) >= 2:
            second_period, second_score = best_time_slots[1]
            if second_score >= 60:
                summary_parts.append(f"次佳选择是{second_period}。")

        # 注意事项
        # 找出条件最差的因素
        temp_scores = [c.temperature_score for c in hourly_conditions]
        weather_scores = [c.weather_score for c in hourly_conditions]
        wind_scores = [c.wind_score for c in hourly_conditions]

        avg_temp_score = sum(temp_scores) / len(temp_scores)
        avg_weather_score = sum(weather_scores) / len(weather_scores)
        avg_wind_score = sum(wind_scores) / len(wind_scores)

        min_score = min(avg_temp_score, avg_weather_score, avg_wind_score)

        if min_score < 50:
            if avg_temp_score == min_score:
                summary_parts.append("**注意**: 温度条件不太理想，请做好保暖或防暑准备。")
            elif avg_weather_score == min_score:
                summary_parts.append("**注意**: 天气条件较差，请做好防护措施。")
            else:
                summary_parts.append("**注意**: 风力较大，请注意安全并调整钓法。")

        return "\n".join(summary_parts)


# 全局分析器实例
_fishing_analyzer = FishingAnalyzer()


async def find_best_fishing_time(location: str, date: str = None) -> str:
    """
    找出最佳钓鱼时间的工具函数

    Args:
        location: 地点名称
        date: 日期 (可选，默认为明天)

    Returns:
        JSON格式的钓鱼推荐结果
    """
    try:
        recommendation = await _fishing_analyzer.find_best_fishing_time(location, date)
        result_dict = recommendation.to_dict()

        return json.dumps(result_dict, ensure_ascii=False, indent=2)

    except Exception as e:
        error_result = {
            "error": f"钓鱼时间分析失败: {str(e)}",
            "location": location,
            "date": date or "明天"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)