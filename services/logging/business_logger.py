#!/usr/bin/env python3
"""
通用业务日志类
统一管理调试日志开关和日志格式
"""

import os
import logging
import json
import time
from typing import Optional, Dict, Any

class BusinessLogger:
    """通用业务日志记录器"""

    def __init__(self, name: str):
        """
        初始化日志记录器

        Args:
            name: 日志记录器名称
        """
        self.logger = logging.getLogger(name)
        self.debug_enabled = os.getenv('DEBUG_LOGGING', 'true').lower() in ('true', '1', 'yes', 'on')

        if self.debug_enabled:
            self.logger.debug("🔧 调试日志已启用")

    # === API相关日志方法 ===
    def log_api_request_start(self, api_name: str, description: str, params: Optional[Dict[str, Any]] = None, url: Optional[str] = None) -> None:
        """记录API请求开始"""
        self.logger.info(f"🌐 {api_name}请求开始: {description}")
        if self.debug_enabled:
            if params:
                self.logger.debug(f"🔍 请求参数: {params}")
            if url:
                self.logger.debug(f"📍 请求URL: {url}")

    def log_api_response(self, api_name: str, status_code: int, duration: float, headers: Optional[Dict] = None, **kwargs) -> None:
        """记录API响应"""
        extra_info = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        extra_text = f", {extra_info}" if extra_info else ""
        self.logger.info(f"📡 {api_name}响应: status_code={status_code}, duration={duration:.3f}s{extra_text}")
        if self.debug_enabled and headers:
            self.logger.debug(f"📋 响应头: {headers}")

    def log_api_response_data(self, data: Dict[str, Any], label: str = "响应数据") -> None:
        """记录API响应数据"""
        if self.debug_enabled:
            self.logger.debug(f"📄 {label}: {json.dumps(data, ensure_ascii=False, indent=2)}")

    def log_api_success(self, api_name: str, description: str, **kwargs) -> None:
        """记录API成功"""
        extra_info = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        extra_text = f", {extra_info}" if extra_info else ""
        self.logger.info(f"✅ {api_name}成功: {description}{extra_text}")

    def log_api_no_match(self, api_name: str, description: str, response_data: Optional[Dict] = None) -> None:
        """记录API无匹配结果"""
        self.logger.warning(f"❌ {api_name}无匹配结果: {description}")
        if self.debug_enabled and response_data:
            self.logger.debug(f"📋 {api_name}完整响应: {json.dumps(response_data, ensure_ascii=False, indent=2)}")

    def log_http_error(self, api_name: str, status_code: int, description: str, response_text: Optional[str] = None) -> None:
        """记录HTTP错误"""
        self.logger.error(f"💥 {api_name}请求失败: HTTP {status_code}, {description}")
        if response_text:
            self.logger.error(f"📄 响应内容: {response_text}")

    def log_timeout_error(self, api_name: str, description: str, timeout: int) -> None:
        """记录超时错误"""
        self.logger.error(f"⏰ {api_name}请求超时: {description}, timeout={timeout}s")

    def log_connection_error(self, api_name: str, description: str) -> None:
        """记录连接错误"""
        self.logger.error(f"🔌 {api_name}连接错误: {description}")

    def log_request_error(self, api_name: str, description: str, error: Exception) -> None:
        """记录请求异常"""
        self.logger.error(f"🌐 {api_name}请求异常: {description}, error={error}")

    def log_json_error(self, api_name: str, description: str, error: Exception) -> None:
        """记录JSON解析错误"""
        self.logger.error(f"📄 {api_name}响应解析失败: {description}, error={error}")

    def log_general_error(self, api_name: str, description: str, error: Exception) -> None:
        """记录一般错误"""
        self.logger.error(f"❌ {api_name}失败: {description}, error={error}")
        if self.debug_enabled:
            self.logger.exception("详细错误信息:")

    # === 缓存相关日志方法 ===
    def log_cache_hit(self, description: str) -> None:
        """记录缓存命中"""
        self.logger.debug(f"缓存命中: {description}")

    def log_cache_miss(self, description: str) -> None:
        """记录缓存未命中"""
        self.logger.debug(f"缓存未命中: {description}")

    def log_cache_saved(self, description: str) -> None:
        """记录缓存保存"""
        self.logger.debug(f"数据已缓存: {description}")

    # === 数据处理相关日志方法 ===
    def log_data_parsed(self, data_type: str, description: str, **kwargs) -> None:
        """记录数据解析"""
        extra_info = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        extra_text = f", {extra_info}" if extra_info else ""
        self.logger.info(f"📍 {data_type}解析结果: {description}{extra_text}")

    def log_data_details(self, data_type: str, data: Dict[str, Any]) -> None:
        """记录数据详情"""
        if self.debug_enabled:
            self.logger.debug(f"🏛️ {data_type}详情: {json.dumps(data, ensure_ascii=False, indent=2)}")

    def log_operation_success(self, operation: str, description: str, **kwargs) -> None:
        """记录操作成功"""
        extra_info = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        extra_text = f", {extra_info}" if extra_info else ""
        self.logger.info(f"🎉 {operation}成功: {description}{extra_text}")

    def log_invalid_data(self, data_type: str, description: str) -> None:
        """记录无效数据"""
        self.logger.warning(f"⚠️ {data_type}数据无效: {description}")

    # === 服务相关日志方法 ===
    def log_service_initialized(self, service_name: str) -> None:
        """记录服务初始化"""
        self.logger.info(f"{service_name}初始化完成 - 调试日志: {'开启' if self.debug_enabled else '关闭'}")

    def log_database_initialized(self, database_name: str = "数据库") -> None:
        """记录数据库初始化"""
        self.logger.info(f"{database_name}初始化完成")

    def log_database_error(self, operation: str, error: Exception) -> None:
        """记录数据库错误"""
        self.logger.error(f"{operation}失败: {error}")

    def log_config_missing(self, config_name: str) -> None:
        """记录配置缺失"""
        self.logger.warning(f"⚠️ 未配置{config_name}")

    # === 批量处理相关日志方法 ===
    def log_batch_progress(self, operation: str, current: int, total: int) -> None:
        """记录批量处理进度"""
        if self.debug_enabled:
            self.logger.debug(f"{operation}进度: {current}/{total}")

    def log_batch_complete(self, operation: str, success: int, total: int) -> None:
        """记录批量处理完成"""
        self.logger.info(f"{operation}完成: {success}/{total}")

    def log_limit_reset(self, limit_type: str) -> None:
        """记录限制重置"""
        self.logger.info(f"{limit_type}限制已重置")

    def log_limit_check(self, description: str, wait_time: Optional[float] = None) -> None:
        """记录限制检查"""
        if self.debug_enabled:
            if wait_time:
                self.logger.debug(f"{description}, 等待 {wait_time:.2f} 秒")
            else:
                self.logger.debug(description)

    def log_limit_reached(self, limit_type: str, current_count: int) -> None:
        """记录达到限制"""
        self.logger.error(f"已达到{limit_type}限制: {current_count}")

    # === 兼容高德API特定方法 ===
    def log_coordinate_success(self, place_name: str, longitude: float, latitude: float) -> None:
        """记录成功获取坐标（兼容方法）"""
        self.log_operation_success("高德API", f"获取坐标 place_name='{place_name}' -> ({longitude:.6f}, {latitude:.6f})")

    def log_address_components(self, province: str, city: str, district: str) -> None:
        """记录地址组件（兼容方法）"""
        address_data = {"province": province, "city": city, "district": district}
        self.log_data_details("地址组件", address_data)

    def log_cache_miss(self, place_name: str) -> None:
        """记录缓存未命中"""
        self.logger.debug(f"缓存未命中，调用API: {place_name}")

    def log_cache_saved(self, place_name: str) -> None:
        """记录缓存保存"""
        self.logger.debug(f"坐标数据已缓存: {place_name}")

    def log_service_initialized(self, service_name: str) -> None:
        """记录服务初始化"""
        self.logger.info(f"{service_name}初始化完成 - 调试日志: {'开启' if self.debug_enabled else '关闭'}")

    def log_database_initialized(self, database_name: str = "数据库") -> None:
        """记录数据库初始化"""
        self.logger.info(f"{database_name}初始化完成")

    def log_cache_query_error(self, error: Exception) -> None:
        """记录缓存查询错误"""
        self.logger.error(f"查询缓存失败: {error}")

    def log_cache_save_error(self, error: Exception) -> None:
        """记录缓存保存错误"""
        self.logger.error(f"保存缓存失败: {error}")

    def log_api_key_missing(self) -> None:
        """记录API密钥缺失"""
        self.logger.warning("⚠️ 未配置高德API密钥")

    def log_api_limit_reset(self) -> None:
        """记录API限制重置"""
        self.logger.info("API调用计数已重置")

    def log_api_limit_check(self, sleep_time: float) -> None:
        """记录API限制检查"""
        if self.debug_enabled:
            self.logger.debug(f"API调用频率限制，等待 {sleep_time:.2f} 秒")

    def log_api_daily_limit_reached(self, daily_count: int) -> None:
        """记录达到日限制"""
        self.logger.error(f"已达到日API调用限制: {daily_count}")

    def log_batch_progress(self, current: int, total: int) -> None:
        """记录批量处理进度"""
        if self.debug_enabled:
            self.logger.debug(f"批量处理进度: {current}/{total}")

    def log_batch_complete(self, success: int, total: int) -> None:
        """记录批量处理完成"""
        self.logger.info(f"批量获取坐标完成: {success}/{total}")