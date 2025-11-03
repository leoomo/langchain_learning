# 核心接口规范

## 模块概述
核心接口模块定义了智能体系统中所有基础抽象和接口规范，确保系统的一致性和可扩展性。

## 接口定义

### 1. 工具接口 (ITool)

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class ToolMetadata(BaseModel):
    """工具元数据"""
    name: str
    description: str
    version: str
    author: str
    tags: List[str] = []
    dependencies: List[str] = []

class ToolResult(BaseModel):
    """工具执行结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}

class ITool(ABC):
    """工具基类接口"""

    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        """工具元数据"""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具"""
        pass

    @abstractmethod
    def validate_input(self, **kwargs) -> bool:
        """验证输入参数"""
        pass

    async def __call__(self, **kwargs) -> ToolResult:
        """调用工具"""
        if not self.validate_input(**kwargs):
            return ToolResult(
                success=False,
                error="Invalid input parameters"
            )
        return await self.execute(**kwargs)
```

### 2. 智能体接口 (IAgent)

```python
from langchain_core.messages import BaseMessage
from langchain_core.agents import AgentExecutor

class AgentConfig(BaseModel):
    """智能体配置"""
    name: str
    model: str
    system_prompt: str
    tools: List[str] = []
    max_iterations: int = 10
    verbose: bool = False

class IAgent(ABC):
    """智能体基类接口"""

    @property
    @abstractmethod
    def config(self) -> AgentConfig:
        """智能体配置"""
        pass

    @abstractmethod
    async def run(self, query: str) -> str:
        """运行智能体"""
        pass

    @abstractmethod
    def add_tool(self, tool: ITool) -> None:
        """添加工具"""
        pass

    @abstractmethod
    def remove_tool(self, tool_name: str) -> None:
        """移除工具"""
        pass
```

### 3. 服务接口 (IService)

```python
class ServiceConfig(BaseModel):
    """服务配置"""
    name: str
    version: str
    enabled: bool = True
    config: Dict[str, Any] = {}

class IService(ABC):
    """服务基类接口"""

    @property
    @abstractmethod
    def config(self) -> ServiceConfig:
        """服务配置"""
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """初始化服务"""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """清理服务"""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """健康检查"""
        pass
```

## 实现要求

### 1. 错误处理
- 所有接口实现必须包含适当的错误处理
- 使用统一的错误类型和格式
- 提供详细的错误信息用于调试

### 2. 日志记录
- 所有接口实现必须包含结构化日志记录
- 记录关键操作和错误信息
- 支持不同日志级别的配置

### 3. 配置管理
- 所有接口必须支持外部配置
- 配置变更支持热更新
- 提供配置验证机制

### 4. 性能监控
- 关键操作必须包含性能监控
- 记录执行时间和资源使用情况
- 支持性能指标的收集和报告

## 扩展性考虑

### 1. 插件机制
- 接口设计支持动态插件加载
- 提供插件生命周期管理
- 支持插件依赖解析

### 2. 版本兼容性
- 接口变更必须保持向后兼容
- 提供版本适配机制
- 支持多版本并存

### 3. 异步支持
- 所有I/O操作必须支持异步
- 提供同步和异步两种调用方式
- 优化并发性能

## 测试要求

### 1. 单元测试
- 每个接口实现必须有完整的单元测试
- 测试覆盖率不低于90%
- 包含边界条件和异常情况测试

### 2. 集成测试
- 接口间集成必须有集成测试
- 测试真实的业务场景
- 验证接口契约的正确性

### 3. 性能测试
- 关键接口必须有性能测试
- 测试不同负载下的表现
- 验证性能指标的达成情况