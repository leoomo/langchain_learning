#!/usr/bin/env python3
"""
日期时间天气服务
支持指定日期和时间粒度的天气查询
"""

import os
import json
import requests
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import asdict

# 导入基础服务
try:
    from .enhanced_weather_service import EnhancedCaiyunWeatherService
    from .weather_service import WeatherData
    from .weather_models import (
        EnhancedWeatherData,
        HourlyWeatherData,
        TimePeriodWeatherData,
        WeatherForecast,
        WeatherQuery,
        WeatherDataType,
        create_hourly_weather_data_from_api,
        create_time_period_weather_data
    )
    from .datetime_utils import DateTimeParser, TimeGranularityParser
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))

    from enhanced_weather_service import EnhancedCaiyunWeatherService
    from weather_service import WeatherData
    from weather_models import (
        EnhancedWeatherData,
        HourlyWeatherData,
        TimePeriodWeatherData,
        WeatherForecast,
        WeatherQuery,
        WeatherDataType,
        create_hourly_weather_data_from_api,
        create_time_period_weather_data
    )
    from datetime_utils import DateTimeParser, TimeGranularityParser

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 错误码定义
class WeatherServiceErrorCode:
    """天气服务统一错误码常量"""
    SUCCESS = 0           # 成功
    CACHE_HIT = 1         # 缓存命中
    API_ERROR = 2         # API错误
    COORDINATE_NOT_FOUND = 3  # 坐标未找到
    NETWORK_TIMEOUT = 4   # 网络超时
    DATA_PARSE_ERROR = 5  # 数据解析失败
    PARAMETER_ERROR = 6   # 参数错误
    DATE_PARSE_ERROR = 7  # 日期解析错误
    TIME_PERIOD_ERROR = 8 # 时间段错误
    DATA_OUT_OF_RANGE = 9 # 数据超出范围

    @classmethod
    def get_description(cls, error_code: int) -> str:
        """获取错误码描述"""
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

# 保持向后兼容
class HourlyForecastErrorCode(WeatherServiceErrorCode):
    """小时级预报错误码常量（向后兼容)"""
    pass


class DateTimeWeatherService(EnhancedCaiyunWeatherService):
    """日期时间天气服务，支持指定日期和时间粒度的天气查询"""

    def __init__(self, api_key: Optional[str] = None, timeout: int = 10):
        """
        初始化日期时间天气服务

        Args:
            api_key: 彩云天气 API 密钥
            timeout: API 请求超时时间（秒)
        """
        super().__init__(api_key, timeout)

        # 初始化解析器
        self.datetime_parser = DateTimeParser()
        self.time_parser = TimeGranularityParser()

        logger.info("日期时间天气服务初始化完成")

    def get_weather_by_date(self, place_name: str, date_str: str) -> Tuple[Optional[EnhancedWeatherData], str, int]:
        """
        获取指定日期的天气信息

        Args:
            place_name: 地区名称
            date_str: 日期字符串，支持多种格式

        Returns:
            (EnhancedWeatherData, status_message, error_code) 元组
            error_code: 0-成功, 1-缓存成功, 2-API错误, 3-坐标未找到, 4-网络超时,
                      5-数据解析失败, 6-参数错误, 7-日期解析错误, 9-数据超出范围
        """
        try:
            # 参数验证
            if not place_name or not place_name.strip():
                error_msg = "地区名称不能为空"
                logger.warning(error_msg)
                return None, f"错误: {error_msg}", WeatherServiceErrorCode.PARAMETER_ERROR

            if not date_str or not date_str.strip():
                error_msg = "日期字符串不能为空"
                logger.warning(error_msg)
                return None, f"错误: {error_msg}", WeatherServiceErrorCode.PARAMETER_ERROR

            # 解析日期
            date_obj = self.datetime_parser.parse_date_string(date_str)
            if not date_obj:
                error_msg = f"无法解析日期: {date_str}"
                logger.warning(error_msg)
                return self._create_error_enhanced_weather_data(place_name, error_msg), f"错误: {error_msg}", WeatherServiceErrorCode.DATE_PARSE_ERROR

            # 检查缓存
            cache_key = f"weather_date:{place_name}:{date_str}"
            cached_weather = self.cache.get(cache_key, extra_params={"type": "weather_date"})
            if cached_weather:
                weather_data = EnhancedWeatherData(**cached_weather["data"])
                logger.info(f"从缓存获取日期天气: {place_name} {date_str}")
                return weather_data, f"缓存数据（{cached_weather.get('source', '未知来源')})", WeatherServiceErrorCode.CACHE_HIT

            # 获取坐标
            coordinates = self.get_coordinates(place_name)
            if not coordinates:
                error_msg = f"未找到地区 '{place_name}' 的坐标信息"
                logger.warning(error_msg)
                fallback_data = self._create_error_enhanced_weather_data(place_name, error_msg)
                return fallback_data, f"模拟数据（坐标未找到)", WeatherServiceErrorCode.COORDINATE_NOT_FOUND

            longitude, latitude = coordinates

            # 判断是历史天气还是预报天气
            today = datetime.now().date()
            target_date = date_obj.date()
            days_diff = (target_date - today).days

            weather_data = None
            source_message = ""

            if days_diff < 0:
                # 历史天气（过去1天内)
                if days_diff >= -1:  # 只支持过去1天
                    weather_data = self._get_historical_weather(longitude, latitude, date_obj, place_name)
                    if weather_data:
                        source_message = "历史天气数据（彩云天气 API)"
                else:
                    source_message = "超出历史天气查询范围（仅支持过去1天)"
                    return self._create_error_enhanced_weather_data(place_name, source_message), f"错误: {source_message}", WeatherServiceErrorCode.DATA_OUT_OF_RANGE
            elif days_diff == 0:
                # 今天，使用实时天气
                weather_data = self._get_current_weather_enhanced(longitude, latitude, place_name, date_obj)
                if weather_data:
                    source_message = "实时天气数据（彩云天气 API)"
            else:
                # 未来天气
                if days_diff <= 15:  # 支持未来15天
                    weather_data = self._get_forecast_weather(longitude, latitude, date_obj, place_name)
                    if weather_data:
                        source_message = "天气预报数据（彩云天气 API)"
                else:
                    source_message = "超出天气预报范围（仅支持未来15天)"
                    return self._create_error_enhanced_weather_data(place_name, source_message), f"错误: {source_message}", WeatherServiceErrorCode.DATA_OUT_OF_RANGE

            # 如果API调用失败，使用模拟数据
            if weather_data is None:
                weather_data = self._create_fallback_enhanced_weather_data(place_name, date_obj)
                if not source_message:
                    source_message = "模拟数据（API 不可用)"
                else:
                    source_message = f"模拟数据（{source_message}))"

            # 设置日期相关字段
            weather_data.datetime = date_obj
            weather_data.date_str = date_obj.strftime('%Y-%m-%d')
            weather_data.data_type = (
                WeatherDataType.HISTORICAL.value if days_diff < 0
                else WeatherDataType.CURRENT.value if days_diff == 0
                else WeatherDataType.DAILY_FORECAST.value
            )

            # 缓存结果
            cache_data = {
                "data": asdict(weather_data),
                "source": source_message,
                "coordinates": coordinates,
                "timestamp": time.time()
            }

            # 设置不同的缓存时间
            if days_diff < 0:
                ttl = 86400  # 历史数据缓存24小时
            elif days_diff == 0:
                ttl = 1800   # 当前数据缓存30分钟
            else:
                ttl = 3600   # 预报数据缓存1小时

            self.cache.set(cache_key, cache_data, ttl=ttl, extra_params={"type": "weather_date"})

            return weather_data, source_message, WeatherServiceErrorCode.SUCCESS

        except requests.exceptions.Timeout:
            error_msg = f"获取日期天气网络超时: {place_name} {date_str}"
            logger.error(error_msg)
            fallback_data = self._create_error_enhanced_weather_data(place_name, error_msg)
            return fallback_data, f"错误: 网络超时", WeatherServiceErrorCode.NETWORK_TIMEOUT
        except requests.exceptions.RequestException as e:
            error_msg = f"获取日期天气网络请求失败: {str(e)}"
            logger.error(error_msg)
            fallback_data = self._create_error_enhanced_weather_data(place_name, error_msg)
            return fallback_data, f"错误: 网络请求失败", WeatherServiceErrorCode.API_ERROR
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            error_msg = f"获取日期天气数据解析失败: {str(e)}"
            logger.error(error_msg)
            fallback_data = self._create_error_enhanced_weather_data(place_name, error_msg)
            return fallback_data, f"错误: {error_msg}", WeatherServiceErrorCode.DATA_PARSE_ERROR
        except Exception as e:
            error_msg = f"获取日期天气未知错误: {str(e)}"
            logger.error(error_msg)
            fallback_data = self._create_error_enhanced_weather_data(place_name, error_msg)
            return fallback_data, f"错误: {error_msg}", WeatherServiceErrorCode.DATA_PARSE_ERROR

    def get_weather_by_datetime(self, place_name: str, datetime_str: str) -> Tuple[Optional[TimePeriodWeatherData], str, int]:
        """
        获取指定日期时间段的天气信息

        Args:
            place_name: 地区名称
            datetime_str: 日期时间表达式，如"明天上午"、"2024-12-25晚上"等

        Returns:
            (TimePeriodWeatherData, status_message, error_code) 元组
            error_code: 0-成功, 1-缓存成功, 2-API错误, 3-坐标未找到, 4-网络超时,
                      5-数据解析失败, 6-参数错误, 7-日期解析错误, 8-时间段错误
        """
        try:
            # 参数验证
            if not place_name or not place_name.strip():
                error_msg = "地区名称不能为空"
                logger.warning(error_msg)
                return None, f"错误: {error_msg}", WeatherServiceErrorCode.PARAMETER_ERROR

            if not datetime_str or not datetime_str.strip():
                error_msg = "日期时间表达式不能为空"
                logger.warning(error_msg)
                return None, f"错误: {error_msg}", WeatherServiceErrorCode.PARAMETER_ERROR

            # 解析日期时间表达式
            date_obj, time_period = self.datetime_parser.parse_datetime_expression(datetime_str)

            if not date_obj:
                error_msg = f"无法解析日期: {datetime_str}"
                logger.warning(error_msg)
                return self._create_error_time_period_data(place_name, datetime_str, error_msg), f"错误: {error_msg}", WeatherServiceErrorCode.DATE_PARSE_ERROR

            if not time_period:
                error_msg = f"无法识别时间段: {datetime_str}"
                logger.warning(error_msg)
                return self._create_error_time_period_data(place_name, datetime_str, error_msg), f"错误: {error_msg}", WeatherServiceErrorCode.TIME_PERIOD_ERROR

            # 检查缓存
            cache_key = f"weather_datetime:{place_name}:{datetime_str}"
            cached_data = self.cache.get(cache_key, extra_params={"type": "weather_datetime"})
            if cached_data:
                period_data = TimePeriodWeatherData(**cached_data["data"])
                logger.info(f"从缓存获取时间段天气: {place_name} {datetime_str}")
                return period_data, f"缓存数据（{cached_data.get('source', '未知来源')})", WeatherServiceErrorCode.CACHE_HIT

            # 获取坐标
            coordinates = self.get_coordinates(place_name)
            if not coordinates:
                error_msg = f"未找到地区 '{place_name}' 的坐标信息"
                logger.warning(error_msg)
                fallback_data = self._create_error_time_period_data(place_name, datetime_str, error_msg)
                return fallback_data, f"模拟数据（坐标未找到)", WeatherServiceErrorCode.COORDINATE_NOT_FOUND

            # 获取小时级预报数据
            hourly_forecast = self._get_hourly_forecast(coordinates[0], coordinates[1], place_name)
            if not hourly_forecast:
                error_msg = "无法获取小时级预报数据"
                logger.warning(error_msg)
                fallback_data = self._create_error_time_period_data(place_name, datetime_str, error_msg)
                return fallback_data, f"模拟数据（{error_msg})", WeatherServiceErrorCode.API_ERROR

            # 聚合时间段数据
            try:
                period_data = hourly_forecast.get_data_for_time_period(time_period, date_obj)

                # 设置位置信息
                period_data.location = place_name

                source_message = f"时间段聚合数据（{len(hourly_forecast.hourly_data)}小时预报)"

                # 缓存结果
                cache_data = {
                    "data": asdict(period_data),
                    "source": source_message,
                    "coordinates": coordinates,
                    "timestamp": time.time()
                }
                self.cache.set(cache_key, cache_data, ttl=3600, extra_params={"type": "weather_datetime"})

                return period_data, source_message, WeatherServiceErrorCode.SUCCESS

            except ValueError as e:
                error_msg = f"时间段数据聚合失败: {str(e)}"
                logger.warning(error_msg)
                fallback_data = self._create_error_time_period_data(place_name, datetime_str, error_msg)
                return fallback_data, f"模拟数据（{error_msg})", WeatherServiceErrorCode.DATA_PARSE_ERROR

        except requests.exceptions.Timeout:
            error_msg = f"获取时间段天气网络超时: {place_name} {datetime_str}"
            logger.error(error_msg)
            fallback_data = self._create_error_time_period_data(place_name, datetime_str, error_msg)
            return fallback_data, f"错误: 网络超时", WeatherServiceErrorCode.NETWORK_TIMEOUT
        except requests.exceptions.RequestException as e:
            error_msg = f"获取时间段天气网络请求失败: {str(e)}"
            logger.error(error_msg)
            fallback_data = self._create_error_time_period_data(place_name, datetime_str, error_msg)
            return fallback_data, f"错误: 网络请求失败", WeatherServiceErrorCode.API_ERROR
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            error_msg = f"获取时间段天气数据解析失败: {str(e)}"
            logger.error(error_msg)
            fallback_data = self._create_error_time_period_data(place_name, datetime_str, error_msg)
            return fallback_data, f"错误: {error_msg}", WeatherServiceErrorCode.DATA_PARSE_ERROR
        except Exception as e:
            error_msg = f"获取时间段天气未知错误: {str(e)}"
            logger.error(error_msg)
            fallback_data = self._create_error_time_period_data(place_name, datetime_str, error_msg)
            return fallback_data, f"错误: {error_msg}", WeatherServiceErrorCode.DATA_PARSE_ERROR

    def get_hourly_forecast(self, place_name: str, hours: int = 24) -> Tuple[Optional[WeatherForecast], str, int]:
        """
        获取小时级天气预报

        Args:
            place_name: 地区名称
            hours: 预报小时数 (1-360)

        Returns:
            (WeatherForecast, status_message, error_code) 元组
            error_code: 0-成功, 1-缓存成功, 2-API错误, 3-坐标未找到, 4-网络超时, 5-数据解析失败, 6-参数错误
        """
        try:
            # 参数验证
            if not place_name or not place_name.strip():
                error_msg = "地区名称不能为空"
                logger.warning(error_msg)
                return None, f"错误: {error_msg}", 6

            if not isinstance(hours, int) or hours < 1 or hours > 360:
                error_msg = f"预报小时数参数错误，应为1-360之间的整数，当前值: {hours}"
                logger.warning(error_msg)
                return None, f"错误: {error_msg}", 6

            # 检查缓存
            cache_key = f"hourly_forecast:{place_name}:{hours}"
            cached_forecast = self.cache.get(cache_key, extra_params={"type": "hourly_forecast"})
            if cached_forecast:
                forecast = WeatherForecast(**cached_forecast["data"])
                logger.info(f"从缓存获取小时预报: {place_name} {hours}小时")
                return forecast, f"缓存数据（{cached_forecast.get('source', '未知来源')})", 1

            # 获取坐标
            coordinates = self.get_coordinates(place_name)
            if not coordinates:
                error_msg = f"未找到地区 '{place_name}' 的坐标信息"
                logger.warning(error_msg)
                fallback_forecast = self._create_fallback_forecast(place_name, hours)
                return fallback_forecast, f"模拟数据（坐标未找到)", 3

            # 获取小时级预报
            forecast = self._get_hourly_forecast(coordinates[0], coordinates[1], place_name, hours)
            if forecast:
                source_message = f"小时预报数据（彩云天气 API)"

                # 缓存结果
                cache_data = {
                    "data": asdict(forecast),
                    "source": source_message,
                    "coordinates": coordinates,
                    "timestamp": time.time()
                }
                self.cache.set(cache_key, cache_data, ttl=3600, extra_params={"type": "hourly_forecast"})

                return forecast, source_message, 0
            else:
                error_msg = "无法获取小时预报数据"
                logger.warning(error_msg)
                fallback_forecast = self._create_fallback_forecast(place_name, hours)
                return fallback_forecast, f"模拟数据（{error_msg})", 2

        except requests.exceptions.Timeout:
            error_msg = f"获取小时预报网络超时: {place_name}"
            logger.error(error_msg)
            fallback_forecast = self._create_fallback_forecast(place_name, hours)
            return fallback_forecast, f"错误: 网络超时", 4
        except requests.exceptions.RequestException as e:
            error_msg = f"获取小时预报网络请求失败: {str(e)}"
            logger.error(error_msg)
            fallback_forecast = self._create_fallback_forecast(place_name, hours)
            return fallback_forecast, f"错误: 网络请求失败", 2
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            error_msg = f"获取小时预报数据解析失败: {str(e)}"
            logger.error(error_msg)
            fallback_forecast = self._create_fallback_forecast(place_name, hours)
            return fallback_forecast, f"错误: {error_msg}", 5
        except Exception as e:
            error_msg = f"获取小时预报未知错误: {str(e)}"
            logger.error(error_msg)
            fallback_forecast = self._create_fallback_forecast(place_name, hours)
            return fallback_forecast, f"错误: {error_msg}", 5

    def is_request_successful(self, error_code: int) -> bool:
        """
        检查天气服务请求是否成功

        Args:
            error_code: 错误码

        Returns:
            bool: True表示成功（包括API成功和缓存命中)，False表示失败
        """
        return error_code in [WeatherServiceErrorCode.SUCCESS, WeatherServiceErrorCode.CACHE_HIT]

    def is_api_success(self, error_code: int) -> bool:
        """
        检查API请求是否成功（不包括缓存)

        Args:
            error_code: 错误码

        Returns:
            bool: True表示API调用成功，False表示失败或来自缓存
        """
        return error_code == WeatherServiceErrorCode.SUCCESS

    # 保持向后兼容的方法
    def is_hourly_forecast_successful(self, error_code: int) -> bool:
        """向后兼容：检查小时级预报请求是否成功"""
        return self.is_request_successful(error_code)

    def is_hourly_forecast_api_success(self, error_code: int) -> bool:
        """向后兼容：检查小时级预报API请求是否成功"""
        return self.is_api_success(error_code)

    def _get_historical_weather(self, longitude: float, latitude: float,
                               date: datetime, place_name: str) -> Optional[EnhancedWeatherData]:
        """获取历史天气数据"""
        if not self.api_key:
            return None

        # 转换为Unix时间戳
        timestamp = int(date.timestamp())

        url = f"{self.base_url}/{self.api_key}/{longitude},{latitude}/weather.json?begin={timestamp}"

        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "ok":
                logger.error(f"历史天气API返回错误: {data.get('status')}")
                return None

            # 解析历史天气数据（使用实时数据格式)
            result = data.get("result", {})
            realtime = result.get("realtime", {})

            # 这里使用简化的解析，因为历史天气API可能返回不同格式
            return EnhancedWeatherData(
                temperature=realtime.get("temperature", 0),
                apparent_temperature=realtime.get("apparent_temperature", 0),
                humidity=realtime.get("humidity", 0),
                pressure=realtime.get("pressure", 0),
                wind_speed=realtime.get("wind", {}).get("speed", 0),
                wind_direction=realtime.get("wind", {}).get("direction", 0),
                condition=self._translate_condition(realtime.get("skycon", "")),
                description=f"{self._translate_condition(realtime.get('skycon', ''))}，{realtime.get('temperature', 0)}°C",
                location=place_name,
                timestamp=timestamp,
                source="彩云天气API",
                datetime=date,
                date_str=date.strftime('%Y-%m-%d'),
                data_type=WeatherDataType.HISTORICAL.value
            )

        except Exception as e:
            logger.error(f"获取历史天气失败: {str(e)}")
            return None

    def _get_current_weather_enhanced(self, longitude: float, latitude: float,
                                      place_name: str, date: datetime) -> Optional[EnhancedWeatherData]:
        """获取增强的当前天气数据"""
        if not self.api_key:
            return None

        url = f"{self.base_url}/{self.api_key}/{longitude},{latitude}/realtime"

        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "ok":
                logger.error(f"实时天气API返回错误: {data.get('status')}")
                return None

            result = data.get("result", {})
            realtime = result.get("realtime", {})

            return EnhancedWeatherData(
                temperature=realtime.get("temperature", 0),
                apparent_temperature=realtime.get("apparent_temperature", 0),
                humidity=realtime.get("humidity", 0),
                pressure=realtime.get("pressure", 0),
                wind_speed=realtime.get("wind", {}).get("speed", 0),
                wind_direction=realtime.get("wind", {}).get("direction", 0),
                condition=self._translate_condition(realtime.get("skycon", "")),
                description=f"{self._translate_condition(realtime.get('skycon', ''))}，{realtime.get('temperature', 0)}°C",
                location=place_name,
                timestamp=realtime.get("timestamp", datetime.now().timestamp()),
                source="彩云天气API",
                datetime=date,
                date_str=date.strftime('%Y-%m-%d'),
                data_type=WeatherDataType.CURRENT.value
            )

        except Exception as e:
            logger.error(f"获取实时天气失败: {str(e)}")
            return None

    def _get_forecast_weather(self, longitude: float, latitude: float,
                             date: datetime, place_name: str) -> Optional[EnhancedWeatherData]:
        """获取预报天气数据"""
        # 获取小时预报，然后聚合为目标日期的数据
        hourly_forecast = self._get_hourly_forecast(longitude, latitude, place_name)
        if not hourly_forecast:
            return None

        # 筛选目标日期的小时数据
        target_date_hours = []
        for hourly in hourly_forecast.hourly_data:
            if hourly.datetime.date() == date.date():
                target_date_hours.append(hourly)

        if not target_date_hours:
            return None

        # 聚合日数据
        temps = [h.temperature for h in target_date_hours]
        apparent_temps = [h.apparent_temperature for h in target_date_hours]
        humidities = [h.humidity for h in target_date_hours]
        pressures = [h.pressure for h in target_date_hours]
        wind_speeds = [h.wind_speed for h in target_date_hours]

        # 统计天气状况
        conditions = [h.condition for h in target_date_hours]
        condition_counts = {}
        for condition in conditions:
            condition_counts[condition] = condition_counts.get(condition, 0) + 1
        primary_condition = max(condition_counts, key=condition_counts.get)

        return EnhancedWeatherData(
            temperature=sum(temps) / len(temps),
            apparent_temperature=sum(apparent_temps) / len(apparent_temps),
            humidity=sum(humidities) / len(humidities),
            pressure=sum(pressures) / len(pressures),
            wind_speed=sum(wind_speeds) / len(wind_speeds),
            wind_direction=0,  # 日预报风向聚合意义不大
            condition=primary_condition,
            description=f"{primary_condition}，平均{sum(temps) / len(temps):.1f}°C",
            location=place_name,
            timestamp=datetime.now().timestamp(),
            source="彩云天气API",
            datetime=date,
            date_str=date.strftime('%Y-%m-%d'),
            data_type=WeatherDataType.DAILY_FORECAST.value,
            is_aggregated=True
        )

    def _get_hourly_forecast(self, longitude: float, latitude: float,
                            place_name: str, hours: int = 24) -> Optional[WeatherForecast]:
        """获取小时级天气预报"""
        if not self.api_key:
            return self._create_fallback_forecast(place_name, hours)

        url = f"{self.base_url}/{self.api_key}/{longitude},{latitude}/hourly?hourlysteps={hours}"

        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "ok":
                logger.error(f"小时预报API返回错误: {data.get('status')}")
                return None

            result = data.get("result", {})
            hourly = result.get("hourly", {})

            if hourly.get("status") != "ok":
                logger.error(f"小时预报数据状态异常: {hourly.get('status')}")
                return None

            # 解析小时数据
            hourly_data_list = []
            precipitation_data = hourly.get("precipitation", [])
            temperature_data = hourly.get("temperature", [])
            apparent_temperature_data = hourly.get("apparent_temperature", [])
            wind_data = hourly.get("wind", [])
            humidity_data = hourly.get("humidity", [])
            cloudrate_data = hourly.get("cloudrate", [])
            skycon_data = hourly.get("skycon", [])
            pressure_data = hourly.get("pressure", [])
            visibility_data = hourly.get("visibility", [])
            air_quality = hourly.get("air_quality", {})

            for i in range(min(len(precipitation_data), hours)):
                hourly_data = HourlyWeatherData(
                    datetime=datetime.fromisoformat(precipitation_data[i]["datetime"].replace('Z', '+00:00')),
                    temperature=temperature_data[i]["value"],
                    apparent_temperature=apparent_temperature_data[i]["value"],
                    humidity=humidity_data[i]["value"],
                    pressure=pressure_data[i]["value"],
                    wind_speed=wind_data[i]["speed"],
                    wind_direction=wind_data[i]["direction"],
                    condition=self._translate_condition(skycon_data[i]["value"]),
                    precipitation_probability=precipitation_data[i]["probability"],
                    precipitation_value=precipitation_data[i]["value"],
                    cloud_rate=cloudrate_data[i]["value"],
                    visibility=visibility_data[i]["value"],
                    aqi=air_quality.get("aqi", [{}])[i] if i < len(air_quality.get("aqi", [])) else None,
                    pm25=air_quality.get("pm25", [{}])[i] if i < len(air_quality.get("pm25", [])) else None
                )
                hourly_data_list.append(hourly_data)

            return WeatherForecast(
                location=place_name,
                forecast_type="hourly",
                hourly_data=hourly_data_list,
                forecast_hours=len(hourly_data_list),
                source="caiyun_api"
            )

        except Exception as e:
            logger.error(f"获取小时预报失败: {str(e)}")
            return None

    def _translate_condition(self, skycon: str) -> str:
        """翻译天气状况"""
        condition_map = {
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
        return condition_map.get(skycon, skycon)

    def _create_error_enhanced_weather_data(self, place_name: str, error_message: str) -> EnhancedWeatherData:
        """创建错误状态的增强天气数据"""
        return EnhancedWeatherData(
            temperature=0.0,
            apparent_temperature=0.0,
            humidity=0.0,
            pressure=0.0,
            wind_speed=0.0,
            wind_direction=0.0,
            condition="错误",
            description=error_message,
            location=place_name,
            timestamp=datetime.now().timestamp(),
            source="错误"
        )

    def _create_fallback_enhanced_weather_data(self, place_name: str,
                                               date: datetime) -> EnhancedWeatherData:
        """创建模拟的增强天气数据"""
        import random

        # 根据日期调整温度（简单模拟)
        days_diff = (date.date() - datetime.now().date()).days
        base_temp = 25.0
        temp_adjustment = days_diff * 2  # 每天变化2度
        temp = base_temp + temp_adjustment + random.uniform(-5, 5)

        conditions = ["晴天", "多云", "阴天", "小雨", "中雨"]
        condition = random.choice(conditions)

        return EnhancedWeatherData(
            temperature=round(temp, 1),
            apparent_temperature=round(temp + random.uniform(-2, 2), 1),
            humidity=random.randint(40, 80),
            pressure=random.randint(1000, 1020),
            wind_speed=random.uniform(0, 20),
            wind_direction=random.randint(0, 360),
            condition=condition,
            description=f"{condition}，{temp:.1f}°C",
            location=place_name,
            timestamp=date.timestamp(),
            source="模拟数据",
            datetime=date,
            date_str=date.strftime('%Y-%m-%d'),
            data_type=WeatherDataType.CURRENT.value
        )

    def _create_error_time_period_data(self, place_name: str, query: str,
                                       error_message: str) -> TimePeriodWeatherData:
        """创建错误状态的时间段天气数据"""
        now = datetime.now()
        return TimePeriodWeatherData(
            location=place_name,
            date=now.strftime('%Y-%m-%d'),
            time_period="未知",
            start_time=now,
            end_time=now + timedelta(hours=1),
            temperature_avg=0.0,
            temperature_min=0.0,
            temperature_max=0.0,
            condition_primary=error_message,
            data_source="错误"
        )

    def _create_fallback_forecast(self, place_name: str, hours: int) -> WeatherForecast:
        """创建模拟的小时预报"""
        import random

        hourly_data = []
        base_temp = 25.0
        base_condition = "晴天"
        conditions = ["晴天", "多云", "阴天", "小雨", "中雨"]

        for i in range(hours):
            temp = base_temp + random.uniform(-5, 5)
            condition = random.choice([base_condition] + conditions)

            hourly_data.append(HourlyWeatherData(
                datetime=datetime.now() + timedelta(hours=i),
                temperature=round(temp, 1),
                apparent_temperature=round(temp + random.uniform(-2, 2), 1),
                humidity=random.randint(40, 80),
                pressure=random.randint(1000, 1020),
                wind_speed=random.uniform(0, 20),
                wind_direction=random.randint(0, 360),
                condition=condition,
                precipitation_probability=random.uniform(0, 1),
                precipitation_value=random.uniform(0, 5),
                cloud_rate=random.uniform(0, 1),
                visibility=random.uniform(5, 25),
                aqi={"chn": random.randint(50, 150), "usa": random.randint(30, 100)},
                pm25=random.uniform(10, 100)
            ))

        return WeatherForecast(
            location=place_name,
            forecast_type="hourly",
            hourly_data=hourly_data,
            forecast_hours=len(hourly_data),
            source="模拟数据"
        )


def create_datetime_weather_service(api_key: Optional[str] = None) -> DateTimeWeatherService:
    """创建日期时间天气服务实例"""
    return DateTimeWeatherService(api_key)