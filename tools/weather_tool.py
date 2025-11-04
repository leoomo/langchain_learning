"""
LangChain Learning - Weather Tool

天气工具模块提供天气查询和预报功能，集成彩云天气API。
"""

import os
import requests
import json
from typing import Optional, Any, Dict, Union, List, Tuple
import logging
from dataclasses import dataclass, asdict
from core.base_tool import BaseTool, ConfigurableTool
from core.interfaces import ToolMetadata, ToolResult

# 导入错误码类
try:
    from services.weather.datetime_weather_service import WeatherServiceErrorCode, HourlyForecastErrorCode
except ImportError:
    # 如果导入失败，创建一个简单的替代
    class WeatherServiceErrorCode:
        SUCCESS = 0
        CACHE_HIT = 1
        API_ERROR = 2
        COORDINATE_NOT_FOUND = 3
        NETWORK_TIMEOUT = 4
        DATA_PARSE_ERROR = 5
        PARAMETER_ERROR = 6
        DATE_PARSE_ERROR = 7
        TIME_PERIOD_ERROR = 8
        DATA_OUT_OF_RANGE = 9

        @classmethod
        def get_description(cls, error_code: int) -> str:
            descriptions = {
                0: "成功",
                1: "缓存命中",
                2: "API错误",
                3: "坐标未找到",
                4: "网络超时",
                5: "数据解析失败",
                6: "参数错误",
                7: "日期解析错误",
                8: "时间段错误",
                9: "数据超出范围"
            }
            return descriptions.get(error_code, "未知错误码")

    class HourlyForecastErrorCode:
        SUCCESS = 0
        CACHE_HIT = 1
        API_ERROR = 2
        COORDINATE_NOT_FOUND = 3
        NETWORK_TIMEOUT = 4
        DATA_PARSE_ERROR = 5
        PARAMETER_ERROR = 6

        @classmethod
        def get_description(cls, error_code: int) -> str:
            descriptions = {
                0: "成功",
                1: "缓存命中",
                2: "API错误",
                3: "坐标未找到",
                4: "网络超时",
                5: "数据解析失败",
                6: "参数错误"
            }
            return descriptions.get(error_code, "未知错误码")


@dataclass
class WeatherData:
    """天气数据类"""
    temperature: float  # 温度 (摄氏度)
    apparent_temperature: float  # 体感温度 (摄氏度)
    humidity: float  # 湿度 (百分比)
    pressure: float  # 气压 (hPa)
    wind_speed: float  # 风速 (km/h)
    wind_direction: float  # 风向 (度)
    condition: str  # 天气状况
    description: str  # 天气描述
    location: str  # 位置
    timestamp: float  # 时间戳
    source: str  # 数据源


class WeatherTool(ConfigurableTool):
    """天气工具类"""

    def __init__(self, config: Optional[Dict[str, Any]] = None, logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)
        self._api_key = self.get_config_value("api_key") or os.getenv("CAIYUN_API_KEY")
        self._timeout = self.get_config_value("timeout", 10)
        self._base_url = self.get_config_value("base_url", "https://api.caiyunapp.com/v2.6")
        self._cache = {}  # 简单缓存
        self._cache_ttl = self.get_config_value("cache_ttl", 1800)  # 30分钟缓存

        # 城市坐标映射
        self._city_coordinates = {
            "北京": (116.4074, 39.9042),
            "上海": (121.4737, 31.2304),
            "广州": (113.2644, 23.1291),
            "深圳": (114.0579, 22.5431),
            "杭州": (120.1551, 30.2741),
            "成都": (104.0668, 30.5728),
            "西安": (108.9402, 34.3416),
            "武汉": (114.3055, 30.5928),
            "南京": (118.7674, 32.0416),
            "重庆": (106.5516, 29.5630),
            "天津": (117.1901, 39.0842),
            "苏州": (120.5853, 31.2989),
            "青岛": (120.3826, 36.0671),
            "大连": (121.6147, 38.9140),
            "厦门": (118.1119, 24.4899),
            "朝阳": (116.4436, 39.9214),  # 北京朝阳区
            "海淀": (116.2982, 39.9596),  # 北京海淀区
            "浦东": (121.5440, 31.2212),  # 上海浦东新区
            "黄浦": (121.4903, 31.2364),  # 上海黄浦区
        }

        # 天气状况映射
        self._condition_map = {
            "CLEAR_DAY": "晴天",
            "CLEAR_NIGHT": "晴夜",
            "PARTLY_CLOUDY_DAY": "多云",
            "PARTLY_CLOUDY_NIGHT": "多云",
            "CLOUDY": "阴天",
            "LIGHT_HAZE": "轻雾",
            "MODERATE_HAZE": "中雾",
            "HEAVY_HAZE": "重雾",
            "LIGHT_RAIN": "小雨",
            "MODERATE_RAIN": "中雨",
            "HEAVY_RAIN": "大雨",
            "STORM_RAIN": "暴雨",
            "LIGHT_SNOW": "小雪",
            "MODERATE_SNOW": "中雪",
            "HEAVY_SNOW": "大雪",
            "STORM_SNOW": "暴雪",
            "DUST": "浮尘",
            "SAND": "沙尘",
            "WIND": "大风"
        }

        if not self._api_key:
            self._logger.warning("未设置彩云天气 API 密钥，将使用模拟数据")

    @property
    def metadata(self) -> ToolMetadata:
        """工具元数据"""
        return ToolMetadata(
            name="weather_tool",
            description="提供天气查询和预报功能",
            version="1.0.0",
            author="langchain-learning",
            tags=["weather", "api", "climate"],
            dependencies=["requests"]
        )

    def validate_input(self, **kwargs) -> bool:
        """验证输入参数"""
        operation = kwargs.get("operation")
        return operation in [
            "current_weather", "get_coordinates", "get_weather",
            "batch_weather", "search_locations", "weather_forecast",
            # 新增日期时间查询操作
            "weather_by_date", "weather_by_datetime", "hourly_forecast",
            "time_period_weather"
        ]

    async def _execute(self, **kwargs) -> ToolResult:
        """执行天气操作"""
        operation = kwargs.get("operation")

        try:
            if operation == "current_weather":
                return await self._current_weather(**kwargs)
            elif operation == "get_coordinates":
                return await self._get_coordinates(**kwargs)
            elif operation == "get_weather":
                return await self._get_weather(**kwargs)
            elif operation == "batch_weather":
                return await self._batch_weather(**kwargs)
            elif operation == "search_locations":
                return await self._search_locations(**kwargs)
            elif operation == "weather_forecast":
                return await self._weather_forecast(**kwargs)
            elif operation == "weather_by_date":
                return await self._weather_by_date(**kwargs)
            elif operation == "weather_by_datetime":
                return await self._weather_by_datetime(**kwargs)
            elif operation == "hourly_forecast":
                return await self._hourly_forecast(**kwargs)
            elif operation == "time_period_weather":
                return await self._time_period_weather(**kwargs)
            else:
                return ToolResult(
                    success=False,
                    error=f"不支持的操作: {operation}"
                )

        except Exception as e:
            self._logger.error(f"天气工具执行失败: {str(e)}")
            return ToolResult(
                success=False,
                error=f"天气工具执行失败: {str(e)}"
            )

    async def _current_weather(self, location: str, **kwargs) -> ToolResult:
        """获取当前天气"""
        try:
            # 检查缓存
            cache_key = f"weather:{location}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return ToolResult(
                    success=True,
                    data=cached_data,
                    metadata={"operation": "current_weather", "source": "cache"}
                )

            # 获取坐标
            coordinates = self._get_location_coordinates(location)
            if not coordinates:
                # 使用模拟数据
                weather_data = self._create_fallback_weather(location)
                return ToolResult(
                    success=True,
                    data=asdict(weather_data),
                    metadata={"operation": "current_weather", "source": "fallback"}
                )

            longitude, latitude = coordinates

            # 调用 API
            weather_data = await self._call_weather_api(longitude, latitude, location)

            # 缓存结果
            self._set_cache(cache_key, asdict(weather_data))

            return ToolResult(
                success=True,
                data=asdict(weather_data),
                metadata={
                    "operation": "current_weather",
                    "source": "api",
                    "coordinates": coordinates
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"获取当前天气失败: {str(e)}"
            )

    async def _get_coordinates(self, location: str, **kwargs) -> ToolResult:
        """获取位置坐标"""
        try:
            coordinates = self._get_location_coordinates(location)
            if coordinates:
                return ToolResult(
                    success=True,
                    data={
                        "location": location,
                        "longitude": coordinates[0],
                        "latitude": coordinates[1],
                        "coordinates": coordinates
                    },
                    metadata={"operation": "get_coordinates"}
                )
            else:
                return ToolResult(
                    success=False,
                    error=f"未找到位置 '{location}' 的坐标信息"
                )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"获取坐标失败: {str(e)}"
            )

    async def _get_weather(self, location: str, detailed: bool = False, **kwargs) -> ToolResult:
        """获取天气信息（兼容方法）"""
        return await self._current_weather(location, **kwargs)

    async def _batch_weather(self, locations: List[str], **kwargs) -> ToolResult:
        """批量获取多个位置的天气"""
        try:
            results = []
            for location in locations:
                try:
                    weather_result = await self._current_weather(location)
                    results.append({
                        "location": location,
                        "success": weather_result.success,
                        "data": weather_result.data if weather_result.success else None,
                        "error": weather_result.error if not weather_result.success else None
                    })
                except Exception as e:
                    self._logger.error(f"批量查询失败: {location}, 错误: {e}")
                    results.append({
                        "location": location,
                        "success": False,
                        "data": None,
                        "error": str(e)
                    })

            successful_count = sum(1 for r in results if r["success"])

            return ToolResult(
                success=successful_count > 0,
                data={
                    "results": results,
                    "summary": {
                        "total": len(locations),
                        "successful": successful_count,
                        "failed": len(locations) - successful_count
                    }
                },
                metadata={"operation": "batch_weather"}
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"批量天气查询失败: {str(e)}"
            )

    async def _search_locations(self, query: str, limit: int = 10, **kwargs) -> ToolResult:
        """搜索位置"""
        try:
            matches = []
            for location, coordinates in self._city_coordinates.items():
                if query.lower() in location.lower():
                    matches.append({
                        "name": location,
                        "coordinates": coordinates,
                        "longitude": coordinates[0],
                        "latitude": coordinates[1]
                    })
                    if len(matches) >= limit:
                        break

            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "matches": matches,
                    "count": len(matches)
                },
                metadata={"operation": "search_locations"}
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"位置搜索失败: {str(e)}"
            )

    async def _weather_forecast(self, location: str, days: int = 3, **kwargs) -> ToolResult:
        """获取天气预报（简化版本）"""
        try:
            # 当前实现返回基于当前天气的简单预报
            current_weather_result = await self._current_weather(location)
            if not current_weather_result.success:
                return current_weather_result

            current_data = current_weather_result.data

            # 生成简单的预报数据（实际应用中应调用专门的预报API）
            forecast = []
            base_temp = current_data["temperature"]
            base_condition = current_data["condition"]

            import random
            conditions = ["晴天", "多云", "阴天", "小雨", "中雨"]

            for i in range(1, days + 1):
                temp_variation = random.uniform(-3, 3)
                forecast.append({
                    "day": i,
                    "temperature": round(base_temp + temp_variation, 1),
                    "condition": random.choice([base_condition] + conditions),
                    "humidity": max(30, min(95, current_data["humidity"] + random.randint(-10, 10))),
                    "wind_speed": max(0, current_data["wind_speed"] + random.uniform(-5, 5))
                })

            return ToolResult(
                success=True,
                data={
                    "location": location,
                    "current": current_data,
                    "forecast": forecast,
                    "days": days
                },
                metadata={"operation": "weather_forecast", "source": "simulated"}
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"天气预报失败: {str(e)}"
            )

    async def _weather_by_date(self, location: str, date: str, **kwargs) -> ToolResult:
        """获取指定日期的天气"""
        try:
            # 导入日期时间天气服务
            try:
                from services.weather.datetime_weather_service import DateTimeWeatherService
            except ImportError:
                self._logger.warning("无法导入DateTimeWeatherService，使用模拟数据")
                # 创建简单的模拟天气数据
                import random
                mock_data = {
                    "location": location,
                    "date": date,
                    "temperature": random.randint(15, 30),
                    "condition": random.choice(["晴天", "多云", "阴天", "小雨"]),
                    "humidity": random.randint(40, 80),
                    "description": f"{date} {location} 模拟天气数据",
                    "source": "模拟数据"
                }
                return ToolResult(
                    success=True,
                    data=mock_data,
                    metadata={"operation": "weather_by_date", "source": "mock"}
                )

            # 使用DateTimeWeatherService
            service = DateTimeWeatherService(
                api_key=self._api_key,
                timeout=self._timeout
            )

            weather_data, status_msg, error_code = service.get_weather_by_date(location, date)

            # 检查是否有错误（status_msg包含"错误"、"失败"等关键词）
            if any(keyword in status_msg.lower() for keyword in ["错误", "失败", "error", "失败", "不可用", "超出范围"]):
                return ToolResult(
                    success=False,
                    error=f"指定日期天气查询失败: {status_msg}",
                    metadata={
                        "operation": "weather_by_date",
                        "error_code": error_code,
                        "status_message": status_msg,
                        "description": WeatherServiceErrorCode.get_description(error_code)
                    }
                )

            return ToolResult(
                success=True,
                data=weather_data.to_dict(),
                metadata={
                    "operation": "weather_by_date",
                    "source": "api",
                    "error_code": error_code,
                    "status_message": status_msg,
                    "description": WeatherServiceErrorCode.get_description(error_code)
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"指定日期天气查询失败: {str(e)}"
            )

    async def _weather_by_datetime(self, location: str, datetime_str: str, **kwargs) -> ToolResult:
        """获取指定日期时间段的天气"""
        try:
            # 导入日期时间天气服务
            try:
                from services.weather.datetime_weather_service import DateTimeWeatherService
            except ImportError:
                self._logger.warning("无法导入DateTimeWeatherService，使用模拟数据")
                # 创建简单的模拟时间段天气数据
                import random
                mock_data = {
                    "location": location,
                    "datetime": datetime_str,
                    "temperature_avg": random.randint(15, 30),
                    "temperature_min": random.randint(10, 25),
                    "temperature_max": random.randint(25, 35),
                    "condition": random.choice(["晴天", "多云", "阴天", "小雨"]),
                    "humidity_avg": random.randint(40, 80),
                    "time_period": datetime_str.split(" ")[-1] if " " in datetime_str else "全天",
                    "description": f"{datetime_str} {location} 模拟天气数据",
                    "source": "模拟数据"
                }
                return ToolResult(
                    success=True,
                    data=mock_data,
                    metadata={"operation": "weather_by_datetime", "source": "mock"}
                )

            # 使用DateTimeWeatherService
            service = DateTimeWeatherService(
                api_key=self._api_key,
                timeout=self._timeout
            )

            weather_data, error_msg, error_code = service.get_weather_by_datetime(location, datetime_str)

            if error_msg:
                return ToolResult(
                    success=False,
                    error=f"指定时间段天气查询失败: {error_msg}",
                    metadata={
                        "operation": "weather_by_datetime",
                        "error_code": error_code,
                        "status_message": error_msg,
                        "description": WeatherServiceErrorCode.get_description(error_code)
                    }
                )

            return ToolResult(
                success=True,
                data=weather_data.to_dict(),
                metadata={
                    "operation": "weather_by_datetime",
                    "source": "api",
                    "error_code": error_code,
                    "status_message": error_msg,
                    "description": WeatherServiceErrorCode.get_description(error_code)
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"指定时间段天气查询失败: {str(e)}"
            )

    async def _hourly_forecast(self, location: str, hours: int = 24, **kwargs) -> ToolResult:
        """获取小时级天气预报"""
        try:
            # 导入日期时间天气服务
            try:
                from services.weather.datetime_weather_service import DateTimeWeatherService
            except ImportError:
                self._logger.warning("无法导入DateTimeWeatherService，使用模拟数据")
                # 创建简单的模拟小时预报数据
                import random
                from datetime import datetime, timedelta

                forecast_data = []
                for i in range(min(hours, 48)):  # 限制最多48小时
                    hour_time = datetime.now() + timedelta(hours=i+1)
                    forecast_data.append({
                        "datetime": hour_time.isoformat(),
                        "temperature": random.randint(15, 30),
                        "condition": random.choice(["晴天", "多云", "阴天", "小雨"]),
                        "humidity": random.randint(40, 80),
                        "wind_speed": random.uniform(0, 20)
                    })

                mock_result = {
                    "location": location,
                    "forecast_hours": len(forecast_data),
                    "hourly_data": forecast_data,
                    "source": "模拟数据"
                }
                return ToolResult(
                    success=True,
                    data=mock_result,
                    metadata={"operation": "hourly_forecast", "source": "mock"}
                )

            # 使用DateTimeWeatherService
            service = DateTimeWeatherService(
                api_key=self._api_key,
                timeout=self._timeout
            )

            # 调用增强的方法，返回3个值：(forecast_data, status_message, error_code)
            forecast_data, status_message, error_code = service.get_hourly_forecast(location, hours)

            # 使用便利方法判断是否成功
            if service.is_hourly_forecast_successful(error_code):
                return ToolResult(
                    success=True,
                    data=forecast_data.to_dict() if forecast_data else None,
                    metadata={
                        "operation": "hourly_forecast",
                        "source": forecast_data.source if forecast_data else "unknown",
                        "error_code": error_code,
                        "status_message": status_message,
                        "description": HourlyForecastErrorCode.get_description(error_code)
                    }
                )
            else:
                return ToolResult(
                    success=False,
                    error=f"小时级预报查询失败: {status_message} (错误码: {error_code})",
                    data=forecast_data.to_dict() if forecast_data else None,  # 即使失败也返回模拟数据
                    metadata={
                        "operation": "hourly_forecast",
                        "source": forecast_data.source if forecast_data else "mock",
                        "error_code": error_code,
                        "status_message": status_message,
                        "description": HourlyForecastErrorCode.get_description(error_code)
                    }
                )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"小时级预报查询失败: {str(e)}"
            )

    async def _time_period_weather(self, location: str, date: str, time_period: str, **kwargs) -> ToolResult:
        """获取指定时间段的天气"""
        try:
            # 组合日期和时间段
            datetime_str = f"{date} {time_period}" if date else time_period
            return await self._weather_by_datetime(location, datetime_str, **kwargs)

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"时间段天气查询失败: {str(e)}"
            )

    def _get_location_coordinates(self, location: str) -> Optional[Tuple[float, float]]:
        """获取位置坐标（使用增强版服务）"""
        # 首先尝试从预定义城市坐标中查找
        coords = self._city_coordinates.get(location.strip())
        if coords:
            return coords

        # 如果预定义中没有，使用增强版天气服务（支持高德API）
        try:
            # 使用绝对导入
            import sys
            from pathlib import Path
            project_root = Path(__file__).parent.parent
            sys.path.insert(0, str(project_root))

            from services.weather.enhanced_weather_service import EnhancedCaiyunWeatherService
            if not hasattr(self, '_enhanced_service'):
                self._enhanced_service = EnhancedCaiyunWeatherService()
                self._logger.info("增强版天气服务已初始化")

            coords = self._enhanced_service.get_coordinates(location.strip())
            if coords:
                # 将结果缓存到城市坐标字典中（内存缓存）
                self._city_coordinates[location.strip()] = coords
                self._logger.debug(f"坐标已缓存到内存: {location.strip()} -> {coords}")
                return coords
            else:
                self._logger.warning(f"增强版天气服务未能获取坐标: {location.strip()}")
        except Exception as e:
            self._logger.error(f"增强版坐标查询失败: {e}")
            import traceback
            self._logger.debug(traceback.format_exc())
        finally:
            # 清理sys.path
            if 'project_root' in locals() and str(project_root) in sys.path:
                sys.path.remove(str(project_root))

        return None

    async def _call_weather_api(self, longitude: float, latitude: float, location: str) -> WeatherData:
        """调用天气API"""
        if not self._api_key:
            return self._create_fallback_weather(location)

        url = f"{self._base_url}/{self._api_key}/{longitude},{latitude}/realtime"

        try:
            response = requests.get(url, timeout=self._timeout)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "ok":
                self._logger.error(f"API 返回错误状态: {data.get('status')}")
                return self._create_fallback_weather(location)

            return self._parse_weather_data(data, location)

        except requests.exceptions.RequestException as e:
            self._logger.error(f"API 请求失败: {str(e)}")
            return self._create_fallback_weather(location)
        except json.JSONDecodeError as e:
            self._logger.error(f"API 响应解析失败: {str(e)}")
            return self._create_fallback_weather(location)

    def _parse_weather_data(self, api_data: Dict, location: str) -> WeatherData:
        """解析API返回的天气数据"""
        try:
            result = api_data.get("result", {})
            realtime = result.get("realtime", {})

            skycon = realtime.get("skycon", "")
            condition = self._condition_map.get(skycon, skycon)

            return WeatherData(
                temperature=realtime.get("temperature", 0),
                apparent_temperature=realtime.get("apparent_temperature", 0),
                humidity=realtime.get("humidity", 0),
                pressure=realtime.get("pressure", 0),
                wind_speed=realtime.get("wind", {}).get("speed", 0),
                wind_direction=realtime.get("wind", {}).get("direction", 0),
                condition=condition,
                description=f"{condition}，{realtime.get('temperature', 0)}°C",
                location=location,
                timestamp=__import__('time').time(),
                source="彩云天气API"
            )

        except Exception as e:
            self._logger.error(f"天气数据解析失败: {str(e)}")
            return self._create_fallback_weather(location)

    def _create_fallback_weather(self, location: str) -> WeatherData:
        """创建模拟天气数据"""
        import random

        fallback_weather = {
            "北京": {"temp": 25, "condition": "晴天", "humidity": 60},
            "上海": {"temp": 28, "condition": "多云", "humidity": 70},
            "广州": {"temp": 30, "condition": "阴天", "humidity": 80},
            "深圳": {"temp": 29, "condition": "晴天", "humidity": 75},
            "杭州": {"temp": 22, "condition": "小雨", "humidity": 85},
            "成都": {"temp": 20, "condition": "雾", "humidity": 90},
            "西安": {"temp": 18, "condition": "晴", "humidity": 50}
        }

        weather_info = fallback_weather.get(location.strip(), {
            "temp": random.randint(15, 30),
            "condition": random.choice(["晴天", "多云", "阴天"]),
            "humidity": random.randint(40, 80)
        })

        return WeatherData(
            temperature=weather_info["temp"],
            apparent_temperature=weather_info["temp"] + random.randint(-2, 2),
            humidity=weather_info["humidity"],
            pressure=random.randint(1000, 1020),
            wind_speed=random.uniform(0, 20),
            wind_direction=random.randint(0, 360),
            condition=weather_info["condition"],
            description=f"{weather_info['condition']}，{weather_info['temp']}°C",
            location=location,
            timestamp=__import__('time').time(),
            source="模拟数据"
        )

    def _get_from_cache(self, key: str) -> Optional[Dict]:
        """从缓存获取数据"""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if __import__('time').time() - timestamp < self._cache_ttl:
                return data
            else:
                del self._cache[key]
        return None

    def _set_cache(self, key: str, data: Dict) -> None:
        """设置缓存数据"""
        self._cache[key] = (data, __import__('time').time())

    def clear_cache(self) -> None:
        """清理缓存"""
        self._cache.clear()

    def get_cache_info(self) -> Dict:
        """获取缓存信息"""
        return {
            "cache_size": len(self._cache),
            "cache_ttl": self._cache_ttl,
            "api_configured": bool(self._api_key),
            "supported_locations": len(self._city_coordinates)
        }

    def _validate_required_params(self, required_params: list, **kwargs) -> bool:
        """验证必需参数"""
        for param in required_params:
            if param not in kwargs or kwargs[param] is None:
                self._logger.error(f"缺少必需参数: {param}")
                return False
        return True