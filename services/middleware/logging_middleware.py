"""
LangChain 智能体日志中间件

提供完整的智能体执行日志记录功能，包括：
- 用户输入和AI回复记录
- 工具调用监控和性能统计
- 错误追踪和调试信息
- 可配置的日志级别和输出方式
"""

import json
import time
import uuid
import os
import logging
from typing import Any, Dict, Optional, List, Callable
from datetime import datetime
from dataclasses import dataclass, asdict

# LangChain imports
try:
    from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
    from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
    from langgraph.runtime import Runtime
    from langchain.agents import AgentState
except ImportError:
    # 如果没有安装完整的LangChain，提供基础类型
    AgentMiddleware = object
    ModelRequest = object
    ModelResponse = object
    BaseMessage = object

from .config import MiddlewareConfig, default_config


@dataclass
class ModelCallRecord:
    """模型调用记录 - 增强版"""
    call_id: int
    timestamp: str
    model_name: str
    duration_ms: float
    token_usage: Dict[str, int]
    success: bool
    call_purpose: str = "unknown"  # 调用目的
    intent_category: str = ""  # 意图分类
    call_context_summary: str = ""  # 调用上下文摘要
    key_points: List[str] = None  # 关键信息点
    inference_method: str = "position_and_content_analysis"  # 推断方法
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.key_points is None:
            self.key_points = []
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if not self.token_usage:
            self.token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


@dataclass
class ToolCallRecord:
    """工具调用记录"""
    tool_name: str
    tool_args: Dict[str, Any]
    result: Any
    duration_ms: float
    success: bool
    error_message: Optional[str] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class AgentExecutionMetrics:
    """智能体执行指标"""
    session_id: str
    timestamp: str
    execution_id: str
    total_duration_ms: float = 0.0
    model_calls_count: int = 0
    tool_calls_count: int = 0
    token_usage: Dict[str, int] = None
    errors_count: int = 0
    success: bool = True
    model_name: str = ""
    model_calls: List[ModelCallRecord] = None  # 增强的模型调用记录
    tool_calls: List[ToolCallRecord] = None    # 工具调用记录

    def __post_init__(self):
        if self.token_usage is None:
            self.token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        if self.model_calls is None:
            self.model_calls = []
        if self.tool_calls is None:
            self.tool_calls = []

    def add_model_call(self, call_record: ModelCallRecord):
        """添加模型调用记录"""
        self.model_calls.append(call_record)
        self.model_calls_count += 1

    def get_model_calls_summary(self) -> Dict[str, Any]:
        """获取模型调用摘要"""
        if not self.model_calls:
            return {}

        purposes = {}
        intents = {}
        total_duration = 0

        for call in self.model_calls:
            # 统计调用目的
            purpose = call.call_purpose
            purposes[purpose] = purposes.get(purpose, 0) + 1

            # 统计意图分类
            intent = call.intent_category
            intents[intent] = intents.get(intent, 0) + 1

            total_duration += call.duration_ms

        return {
            "total_calls": len(self.model_calls),
            "purposes_distribution": purposes,
            "intents_distribution": intents,
            "average_duration_ms": total_duration / len(self.model_calls) if self.model_calls else 0,
            "total_model_duration_ms": total_duration
        }


class CallPurposeAnalyzer:
    """调用目的分析器 - 智能推断模型调用的目的和意图"""

    # 调用目的类型定义
    CALL_PURPOSES = {
        "tool_selection": "工具选择",
        "result_generation": "结果生成",
        "intent_understanding": "意图理解",
        "context_analysis": "上下文分析",
        "tool_execution": "工具执行处理",
        "final_response": "最终回复生成",
        "error_handling": "错误处理",
        "unknown": "未知目的"
    }

    # 意图分类定义
    INTENT_CATEGORIES = {
        "weather_query": "天气查询",
        "weather_fishing_query": "钓鱼天气查询",
        "location_query": "地点查询",
        "time_query": "时间查询",
        "calculation": "计算请求",
        "information_search": "信息搜索",
        "general_conversation": "一般对话",
        "error_recovery": "错误恢复",
        "unknown": "未知意图"
    }

    # 关键词映射
    INTENT_KEYWORDS = {
        "weather_query": ["天气", "气温", "下雨", "晴天", "阴天", "多云", "温度"],
        "weather_fishing_query": ["钓鱼", "钓鱼天气", "适合钓鱼", "钓鱼时间", "钓鱼推荐"],
        "location_query": ["在哪", "位置", "坐标", "地址", "怎么去"],
        "time_query": ["时间", "几点", "什么时候", "明天", "后天", "今天"],
        "calculation": ["计算", "加法", "乘法", "除法", "等于"],
        "information_search": ["搜索", "查找", "信息", "资料", "什么是"]
    }

    @classmethod
    def analyze_call_purpose(cls, messages: List[Any], call_position: int,
                            has_tool_calls: bool, response: Any = None,
                            compiled_patterns: Optional[Dict] = None) -> Dict[str, str]:
        """
        分析模型调用的目的 - 增强版，支持预编译模式

        Args:
            messages: 消息列表
            call_position: 调用在对话中的位置（从1开始）
            has_tool_calls: 是否包含工具调用
            response: 模型响应（可选）
            compiled_patterns: 预编译的正则表达式模式（可选）

        Returns:
            包含调用目的分析的字典
        """
        # 基于调用位置的基础推断
        purpose = cls._infer_purpose_by_position(call_position, has_tool_calls)

        # 基于消息内容的意图分析
        intent_category = cls._analyze_intent_from_messages(messages)

        # 提取关键信息点（使用预编译模式）
        key_points = cls._extract_key_points(messages, response, compiled_patterns)

        # 生成上下文摘要
        context_summary = cls._generate_context_summary(messages, purpose, key_points)

        return {
            "call_purpose": purpose,
            "intent_category": intent_category,
            "key_points": key_points,
            "context_summary": context_summary,
            "inference_method": "position_and_content_analysis"
        }

    @classmethod
    def _infer_purpose_by_position(cls, position: int, has_tool_calls: bool) -> str:
        """基于调用位置推断目的"""
        if position == 1:
            # 首次调用通常是工具选择
            return "tool_selection"
        elif has_tool_calls:
            # 包含工具调用的可能是工具执行处理
            return "tool_execution"
        else:
            # 后续调用通常是结果生成
            return "result_generation"

    @classmethod
    def _analyze_intent_from_messages(cls, messages: List[Any]) -> str:
        """从消息中分析用户意图"""
        if not messages:
            return "unknown"

        # 获取最新的用户消息
        user_message = None
        for msg in reversed(messages):
            if hasattr(msg, 'type') and msg.type == 'human':
                user_message = msg
                break
            elif hasattr(msg, '__class__') and 'HumanMessage' in str(msg.__class__):
                user_message = msg
                break

        if not user_message or not hasattr(user_message, 'content'):
            return "unknown"

        content = str(user_message.content).lower()

        # 基于关键词匹配意图
        for intent, keywords in cls.INTENT_KEYWORDS.items():
            if any(keyword in content for keyword in keywords):
                return intent

        # 特殊检查：钓鱼相关查询
        if "钓鱼" in content:
            return "weather_fishing_query"

        return "general_conversation"

    @classmethod
    def _extract_key_points(cls, messages: List[Any], response: Any = None, compiled_patterns: Optional[Dict] = None) -> List[str]:
        """提取关键信息点 - 优化版本，支持预编译模式"""
        key_points = []

        # 从用户消息中提取关键词
        for msg in messages:
            if hasattr(msg, 'type') and msg.type == 'human':
                content = str(msg.content)

                # 使用预编译模式（如果提供）
                if compiled_patterns:
                    # 时间相关关键词
                    for word in compiled_patterns.get('time_words', []):
                        if word in content:
                            key_points.append(word)

                    # 地点相关关键词（使用预编译正则）
                    location_regex = compiled_patterns.get('location')
                    if location_regex:
                        locations = location_regex.findall(content)
                        key_points.extend(locations)

                    # 活动相关关键词
                    for word in compiled_patterns.get('activity_words', []):
                        if word in content:
                            key_points.append(word)
                else:
                    # 回退到原始模式
                    # 时间相关关键词
                    time_words = ["明天", "后天", "今天", "早上", "上午", "下午", "晚上", "夜间"]
                    for word in time_words:
                        if word in content:
                            key_points.append(word)

                    # 地点相关关键词
                    import re
                    location_pattern = r'(北京|上海|广州|深圳|杭州|南京|苏州|成都|武汉|西安|郑州|青岛|大连|厦门|无锡|福州|济南|哈尔滨|沈阳|长春|石家庄|太原|呼和浩特|银川|西宁|乌鲁木齐|兰州|西安|成都|贵阳|昆明|南宁|拉萨|杭州|合肥|南昌|长沙|武汉|郑州|济南|青岛|南京|苏州|上海|福州|厦门|台北|香港|澳门|天津|重庆|.[区县])'
                    locations = re.findall(location_pattern, content)
                    key_points.extend(locations)

                    # 活动相关关键词
                    activity_words = ["钓鱼", "天气", "查询", "计算", "搜索"]
                    for word in activity_words:
                        if word in content:
                            key_points.append(word)

        # 去重并限制数量
        key_points = list(set(key_points))[:5]
        return key_points

    @classmethod
    def _generate_context_summary(cls, messages: List[Any], purpose: str, key_points: List[str]) -> str:
        """生成调用上下文摘要"""
        if not messages:
            return "空消息上下文"

        # 获取用户消息内容
        user_content = ""
        for msg in messages:
            if hasattr(msg, 'type') and msg.type == 'human':
                user_content = str(msg.content)[:100]  # 限制长度
                break

        # 生成摘要
        purpose_desc = cls.CALL_PURPOSES.get(purpose, purpose)

        if key_points:
            key_points_str = "、".join(key_points[:3])  # 最多显示3个关键点
            summary = f"{purpose_desc}，关键信息：{key_points_str}"
        else:
            summary = f"{purpose_desc}，用户输入：{user_content}"

        return summary[:200]  # 限制摘要长度


class SensitiveDataFilter:
    """敏感数据过滤器"""

    SENSITIVE_PATTERNS = [
        ('api_key', r'(?i)api[_-]?key["\']?\s*[:=]\s*["\']?([^"\'\\s]{10,})'),
        ('password', r'(?i)password["\']?\s*[:=]\s*["\']?([^"\'\\s]{6,})'),
        ('token', r'(?i)token["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{10,})'),
        ('secret', r'(?i)secret["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{10,})'),
    ]

    @classmethod
    def filter_text(cls, text: str) -> str:
        """过滤文本中的敏感信息"""
        import re
        filtered_text = text
        for pattern_name, pattern in cls.SENSITIVE_PATTERNS:
            filtered_text = re.sub(pattern, f'{pattern_name}=***FILTERED***', filtered_text)
        return filtered_text

    @classmethod
    def filter_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """递归过滤字典中的敏感信息"""
        if not isinstance(data, dict):
            return data

        filtered = {}
        for key, value in data.items():
            key_lower = str(key).lower()
            if any(sensitive in key_lower for sensitive in ['api_key', 'password', 'token', 'secret', 'key']):
                filtered[key] = "***FILTERED***"
            elif isinstance(value, dict):
                filtered[key] = cls.filter_dict(value)
            elif isinstance(value, str):
                filtered[key] = cls.filter_text(value)
            else:
                filtered[key] = value
        return filtered


class AgentLoggingMiddleware(AgentMiddleware):
    """
    LangChain 智能体日志中间件

    提供完整的智能体执行日志记录和性能监控功能。
    """

    def __init__(self, config: Optional[MiddlewareConfig] = None, logger: Optional[logging.Logger] = None):
        """
        初始化日志中间件

        Args:
            config: 中间件配置，如果为None则使用默认配置
            logger: 自定义logger，如果为None则创建默认logger
        """
        self.config = config or default_config
        self.config.validate()

        # 设置logger
        self.logger = logger or self._setup_logger()

        # 会话管理
        self.session_id = self._generate_session_id()
        self.execution_start_time = None

        # 执行统计
        self.metrics = AgentExecutionMetrics(
            session_id=self.session_id,
            timestamp=datetime.now().isoformat(),
            execution_id=str(uuid.uuid4())
        )

        # 工具调用记录
        self.tool_calls: List[ToolCallRecord] = []

        # 敏感数据过滤器
        self.sensitive_filter = SensitiveDataFilter() if self.config.enable_sensitive_filter else None

        # 性能优化：缓存机制
        self._purpose_analysis_cache = {}
        self._max_cache_size = 100

        # 性能优化：预编译正则表达式
        self._compiled_patterns = {}
        if self.config.enable_call_purpose_analysis:
            self._compile_intent_patterns()

        self.logger.info(f"🔧 AgentLoggingMiddleware 初始化完成 (增强版)", extra={
            'session_id': self.session_id,
            'config': self.config.to_dict(),
            'enhanced_features': {
                'call_purpose_analysis': self.config.enable_call_purpose_analysis,
                'enhanced_console_output': self.config.show_enhanced_console_output,
                'model_call_detail_level': self.config.model_call_detail_level
            }
        })

    def _compile_intent_patterns(self):
        """预编译意图识别的正则表达式以提高性能"""
        import re

        # 预编译地点识别正则
        location_pattern = r'(北京|上海|广州|深圳|杭州|南京|苏州|成都|武汉|西安|郑州|青岛|大连|厦门|无锡|福州|济南|哈尔滨|沈阳|长春|石家庄|太原|呼和浩特|银川|西宁|乌鲁木齐|兰州|西安|成都|贵阳|昆明|南宁|拉萨|杭州|合肥|南昌|长沙|武汉|郑州|济南|青岛|南京|苏州|上海|福州|厦门|台北|香港|澳门|天津|重庆|.[区县])'
        self._compiled_patterns['location'] = re.compile(location_pattern)

        # 预编译时间词识别列表
        time_words = ["明天", "后天", "今天", "早上", "上午", "下午", "晚上", "夜间"]
        self._compiled_patterns['time_words'] = time_words

        # 预编译活动词识别列表
        activity_words = ["钓鱼", "天气", "查询", "计算", "搜索"]
        self._compiled_patterns['activity_words'] = activity_words

    def _get_purpose_analysis_cache_key(self, messages_str: str, call_position: int, has_tool_calls: bool) -> str:
        """生成目的分析缓存键"""
        import hashlib
        content = f"{messages_str}_{call_position}_{has_tool_calls}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def _cache_purpose_analysis(self, cache_key: str, analysis: Dict[str, Any]):
        """缓存目的分析结果"""
        if len(self._purpose_analysis_cache) >= self._max_cache_size:
            # 移除最旧的缓存项
            oldest_key = next(iter(self._purpose_analysis_cache))
            del self._purpose_analysis_cache[oldest_key]

        self._purpose_analysis_cache[cache_key] = analysis

    def _get_cached_purpose_analysis(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """获取缓存的目的分析结果"""
        return self._purpose_analysis_cache.get(cache_key)

    def _setup_logger(self) -> logging.Logger:
        """设置专用的agent日志logger"""
        logger = logging.getLogger('agent.middleware')
        logger.setLevel(getattr(logging, self.config.log_level))

        # 避免重复添加handler
        if not logger.handlers:
            # 创建formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

            # 控制台输出
            if self.config.log_to_console:
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(formatter)
                logger.addHandler(console_handler)

            # 文件输出
            if self.config.log_to_file:
                # 确保日志目录存在
                os.makedirs(os.path.dirname(self.config.log_file_path), exist_ok=True)
                file_handler = logging.FileHandler(self.config.log_file_path)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)

        return logger

    def _generate_session_id(self) -> str:
        """生成会话ID"""
        if self.config.session_id_generator == "uuid":
            return str(uuid.uuid4())
        elif self.config.session_id_generator == "timestamp":
            return str(int(time.time()))
        else:
            return f"session_{int(time.time())}"

    def _log_with_context(self, level: str, message: str, extra: Optional[Dict[str, Any]] = None):
        """带上下文的日志记录"""
        log_extra = {
            'session_id': self.session_id,
            'execution_id': self.metrics.execution_id,
            'component': 'AgentMiddleware'
        }

        if extra:
            log_extra.update(extra)

        # 过滤敏感信息
        if self.sensitive_filter and extra:
            log_extra = self.sensitive_filter.filter_dict(log_extra)

        # 截断过长的日志
        if len(message) > self.config.max_log_length:
            message = message[:self.config.max_log_length] + "...[TRUNCATED]"

        getattr(self.logger, level.lower())(message, extra=log_extra)

    def _format_messages(self, messages: List[BaseMessage]) -> str:
        """格式化消息列表"""
        if not messages:
            return "[]"

        formatted = []
        for msg in messages:
            msg_dict = {
                'type': msg.__class__.__name__,
                'content': str(msg.content)[:200] + ("..." if len(str(msg.content)) > 200 else "")
            }

            # 添加工具调用信息
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                msg_dict['tool_calls'] = [
                    {
                        'name': tc.get('name', 'unknown'),
                        'args': tc.get('args', {})
                    }
                    for tc in msg.tool_calls
                ]

            formatted.append(msg_dict)

        return json.dumps(formatted, ensure_ascii=False, indent=2)

    def _extract_model_name(self, request: ModelRequest) -> str:
        """提取模型名称"""
        if hasattr(request, 'model') and request.model:
            if hasattr(request.model, 'model_name'):
                return request.model.model_name
            elif hasattr(request.model, 'name'):
                return request.model.name
            elif isinstance(request.model, str):
                return request.model
        return "unknown"

    def before_model(self, state: AgentState, runtime: Runtime) -> Optional[Dict[str, Any]]:
        """模型调用前的处理"""
        if not self.execution_start_time:
            self.execution_start_time = time.time()

        self.metrics.model_calls_count += 1

        # 记录输入信息
        messages = state.get('messages', [])

        self._log_with_context('INFO', "🚀 开始模型调用", {
            'messages_count': len(messages),
            'messages_preview': self._format_messages(messages),
            'runtime_context': str(runtime.context) if hasattr(runtime, 'context') else None
        })

        return None

    def wrap_model_call(self, request: ModelRequest, handler: Callable) -> ModelResponse:
        """包装模型调用，记录详细信息和调用目的分析"""
        start_time = time.time()
        self.metrics.model_name = self._extract_model_name(request)

        # 获取调用信息用于目的分析
        messages = getattr(request, 'messages', [])
        call_position = self.metrics.model_calls_count + 1  # 调用位置（从1开始）

        try:
            # 执行模型调用
            response = handler(request)

            # 计算耗时
            duration_ms = (time.time() - start_time) * 1000
            self.metrics.total_duration_ms += duration_ms

            # 提取token使用信息
            token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                token_usage.update(response.usage_metadata)
                self.metrics.token_usage.update(response.usage_metadata)

            # 检查是否包含工具调用
            has_tool_calls = False
            if hasattr(response, 'tool_calls') and response.tool_calls:
                has_tool_calls = True

            # 分析调用目的（如果启用）
            purpose_analysis = {}
            if self.config.enable_call_purpose_analysis:
                # 尝试从缓存获取分析结果
                messages_str = str([str(getattr(msg, 'content', '')) for msg in messages[-3:]])  # 只使用最近3条消息生成缓存键
                cache_key = self._get_purpose_analysis_cache_key(messages_str, call_position, has_tool_calls)

                cached_analysis = self._get_cached_purpose_analysis(cache_key)
                if cached_analysis:
                    purpose_analysis = cached_analysis
                else:
                    # 执行分析并缓存结果
                    purpose_analysis = CallPurposeAnalyzer.analyze_call_purpose(
                        messages=messages,
                        call_position=call_position,
                        has_tool_calls=has_tool_calls,
                        response=response,
                        compiled_patterns=self._compiled_patterns
                    )
                    self._cache_purpose_analysis(cache_key, purpose_analysis)

            # 创建增强的模型调用记录
            call_record = ModelCallRecord(
                call_id=call_position,
                timestamp=datetime.now().isoformat(),
                model_name=self.metrics.model_name,
                duration_ms=duration_ms,
                token_usage=token_usage.copy(),
                success=True,
                call_purpose=purpose_analysis.get("call_purpose", "unknown"),
                intent_category=purpose_analysis.get("intent_category", ""),
                call_context_summary=purpose_analysis.get("context_summary", ""),
                key_points=purpose_analysis.get("key_points", []),
                inference_method=purpose_analysis.get("inference_method", "position_and_content_analysis")
            )

            # 添加到指标中
            self.metrics.add_model_call(call_record)

            # 记录增强的请求信息
            self._log_enhanced_model_request(request, purpose_analysis)

            # 记录增强的响应信息
            self._log_enhanced_model_response(response, call_record, purpose_analysis)

            return response

        except Exception as e:
            self.metrics.errors_count += 1
            self.metrics.success = False
            duration_ms = (time.time() - start_time) * 1000

            # 即使失败也创建调用记录
            purpose_analysis = {}
            if self.config.enable_call_purpose_analysis:
                purpose_analysis = CallPurposeAnalyzer.analyze_call_purpose(
                    messages=messages,
                    call_position=call_position,
                    has_tool_calls=False,
                    response=None,
                    compiled_patterns=self._compiled_patterns
                )

            error_call_record = ModelCallRecord(
                call_id=call_position,
                timestamp=datetime.now().isoformat(),
                model_name=self.metrics.model_name,
                duration_ms=duration_ms,
                token_usage=self.metrics.token_usage.copy(),
                success=False,
                call_purpose=purpose_analysis.get("call_purpose", "error_handling"),
                intent_category=purpose_analysis.get("intent_category", "error_recovery"),
                call_context_summary=purpose_analysis.get("context_summary", "模型调用失败"),
                key_points=purpose_analysis.get("key_points", []),
                inference_method=purpose_analysis.get("inference_method", "position_and_content_analysis"),
                error_message=str(e)
            )

            self.metrics.add_model_call(error_call_record)

            # 记录错误信息
            self._log_with_context('ERROR', f"❌ 模型调用失败: {str(e)}", {
                'duration_ms': round(duration_ms, 2),
                'error_type': type(e).__name__,
                'error_details': str(e),
                'call_purpose': error_call_record.call_purpose,
                'call_id': call_position
            })

            raise

    def _log_enhanced_model_request(self, request: ModelRequest, purpose_analysis: Dict[str, str]):
        """记录增强的模型请求信息"""
        messages = getattr(request, 'messages', [])

        # 构建易读的控制台输出（如果启用增强输出）
        if self.config.show_enhanced_console_output and purpose_analysis:
            purpose_desc = CallPurposeAnalyzer.CALL_PURPOSES.get(
                purpose_analysis.get("call_purpose", "unknown"),
                "未知目的"
            )

            key_points = purpose_analysis.get("key_points", [])
            key_points_str = "、".join(key_points[:3]) if key_points else "无"

            console_msg = f"🤖 模型调用 #{self.metrics.model_calls_count + 1} [{purpose_desc}]"

            if self.config.log_to_console:
                print(f"\n{console_msg}")
                print(f"├── 目的: {purpose_desc}")
                print(f"├── 意图: {CallPurposeAnalyzer.INTENT_CATEGORIES.get(purpose_analysis.get('intent_category', ''), purpose_analysis.get('intent_category', ''))}")
                if key_points:
                    print(f"├── 关键点: [{key_points_str}]")
                print(f"└── 模型: {self.metrics.model_name}")

        # 记录调试信息
        self._log_with_context('DEBUG', "📤 模型请求详情", {
            'call_id': self.metrics.model_calls_count + 1,
            'model': self.metrics.model_name,
            'tools_count': len(getattr(request, 'tools', [])),
            'messages_count': len(messages),
            'call_purpose': purpose_analysis.get("call_purpose"),
            'intent_category': purpose_analysis.get("intent_category"),
            'key_points': key_points,
            'context_summary': purpose_analysis.get("context_summary", "")[:100]
        })

    def _log_enhanced_model_response(self, response: ModelResponse, call_record: ModelCallRecord, purpose_analysis: Dict[str, str]):
        """记录增强的模型响应信息"""

        # 构建易读的控制台输出（如果启用增强输出）
        if self.config.show_enhanced_console_output:
            purpose_desc = CallPurposeAnalyzer.CALL_PURPOSES.get(call_record.call_purpose, call_record.call_purpose)
            duration_str = f"{call_record.duration_ms:.1f}ms"

            if self.config.log_to_console:
                # 选择合适的emoji
                if call_record.call_purpose == "tool_selection":
                    emoji = "🎯"
                elif call_record.call_purpose == "result_generation":
                    emoji = "✨"
                elif call_record.call_purpose == "tool_execution":
                    emoji = "⚙️"
                else:
                    emoji = "⚡"

                print(f"{emoji} 处理完成: {duration_str} | Tokens: {call_record.token_usage.get('total_tokens', 0)}")
                if call_record.key_points:
                    print(f"└── 摘要: {call_record.call_context_summary[:80]}...")

        # 记录完整的响应信息
        self._log_with_context('INFO', "📥 模型响应详情", {
            'call_id': call_record.call_id,
            'call_purpose': call_record.call_purpose,
            'purpose_desc': purpose_desc,
            'duration_ms': round(call_record.duration_ms, 2),
            'token_usage': call_record.token_usage,
            'intent_category': call_record.intent_category,
            'key_points': call_record.key_points,
            'context_summary': call_record.call_context_summary,
            'success': call_record.success,
            'response_preview': str(response)[:200] + "..." if len(str(response)) > 200 else str(response)
        })

    def wrap_tool_call(self, request, handler) -> Any:
        """包装工具调用，记录工具执行详情"""
        if not self.config.enable_tool_tracking:
            return handler(request)

        start_time = time.time()

        # 提取工具信息
        tool_name = "unknown"
        tool_args = {}

        if hasattr(request, 'tool_call'):
            tool_call = request.tool_call
            tool_name = tool_call.get('name', 'unknown')
            tool_args = tool_call.get('args', {})
        elif hasattr(request, 'name'):
            tool_name = request.name
            tool_args = getattr(request, 'args', {})

        self.metrics.tool_calls_count += 1

        try:
            self._log_with_context('INFO', f"🔧 开始工具调用: {tool_name}", {
                'tool_name': tool_name,
                'tool_args': tool_args,
                'args_count': len(tool_args) if isinstance(tool_args, dict) else 0
            })

            # 执行工具调用
            result = handler(request)

            # 计算耗时
            duration_ms = (time.time() - start_time) * 1000

            # 记录工具调用成功
            tool_record = ToolCallRecord(
                tool_name=tool_name,
                tool_args=tool_args,
                result=result,
                duration_ms=duration_ms,
                success=True
            )
            self.tool_calls.append(tool_record)

            self._log_with_context('INFO', f"✅ 工具调用完成: {tool_name}", {
                'tool_name': tool_name,
                'duration_ms': round(duration_ms, 2),
                'result_preview': str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
            })

            return result

        except Exception as e:
            self.metrics.errors_count += 1
            duration_ms = (time.time() - start_time) * 1000

            # 记录工具调用失败
            tool_record = ToolCallRecord(
                tool_name=tool_name,
                tool_args=tool_args,
                result=None,
                duration_ms=duration_ms,
                success=False,
                error_message=str(e)
            )
            self.tool_calls.append(tool_record)

            self._log_with_context('ERROR', f"❌ 工具调用失败: {tool_name}", {
                'tool_name': tool_name,
                'duration_ms': round(duration_ms, 2),
                'error_type': type(e).__name__,
                'error_message': str(e)
            })

            raise

    def after_model(self, state: AgentState, runtime: Runtime) -> Optional[Dict[str, Any]]:
        """模型调用后的处理"""
        # 更新最终指标
        if self.execution_start_time:
            self.metrics.total_duration_ms = (time.time() - self.execution_start_time) * 1000

        # 记录执行完成
        self._log_with_context('INFO', "🏁 模型调用完成", {
            'final_metrics': asdict(self.metrics),
            'tool_calls_summary': [
                {
                    'tool_name': tc.tool_name,
                    'duration_ms': round(tc.duration_ms, 2),
                    'success': tc.success
                }
                for tc in self.tool_calls[-5:]  # 只显示最近5个工具调用
            ]
        })

        return None

    def get_execution_summary(self) -> Dict[str, Any]:
        """获取执行摘要"""
        return {
            'session_id': self.session_id,
            'execution_id': self.metrics.execution_id,
            'metrics': asdict(self.metrics),
            'tool_calls': [asdict(tc) for tc in self.tool_calls],
            'timestamp': datetime.now().isoformat()
        }

    def reset_metrics(self):
        """重置执行指标"""
        self.metrics = AgentExecutionMetrics(
            session_id=self.session_id,
            timestamp=datetime.now().isoformat(),
            execution_id=str(uuid.uuid4())
        )
        self.tool_calls = []
        self.execution_start_time = None