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

    def __post_init__(self):
        if self.token_usage is None:
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

        self.logger.info(f"🔧 AgentLoggingMiddleware 初始化完成", extra={
            'session_id': self.session_id,
            'config': self.config.to_dict()
        })

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
        """包装模型调用，记录详细信息"""
        start_time = time.time()
        self.metrics.model_name = self._extract_model_name(request)

        try:
            # 记录请求
            self._log_with_context('DEBUG', "📤 模型请求", {
                'model': self.metrics.model_name,
                'tools_count': len(getattr(request, 'tools', [])),
                'messages_count': len(getattr(request, 'messages', []))
            })

            # 执行模型调用
            response = handler(request)

            # 计算耗时
            duration_ms = (time.time() - start_time) * 1000
            self.metrics.total_duration_ms += duration_ms

            # 提取token使用信息
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                self.metrics.token_usage.update(response.usage_metadata)

            # 记录响应
            self._log_with_context('INFO', "📥 模型响应", {
                'duration_ms': round(duration_ms, 2),
                'token_usage': self.metrics.token_usage,
                'response_preview': str(response)[:300] + "..." if len(str(response)) > 300 else str(response)
            })

            return response

        except Exception as e:
            self.metrics.errors_count += 1
            self.metrics.success = False
            duration_ms = (time.time() - start_time) * 1000

            self._log_with_context('ERROR', f"❌ 模型调用失败: {str(e)}", {
                'duration_ms': round(duration_ms, 2),
                'error_type': type(e).__name__,
                'error_details': str(e)
            })

            raise

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