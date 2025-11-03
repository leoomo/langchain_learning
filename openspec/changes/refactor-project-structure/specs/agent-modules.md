# 智能体模块规范

## 模块概述
智能体模块定义了系统中的智能体架构，包括现代LangChain智能体、智能体工厂和配置管理。智能体负责协调各种工具和服务，实现复杂任务的自动化处理。

## 智能体架构

### 1. 现代智能体 (ModernAgent)

**功能描述**: 基于LangChain的现代智能体实现

**接口定义**:
```python
from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.agents import AgentExecutor
from langchain_core.tools import BaseTool
from core.interfaces import IAgent, AgentConfig, ITool

class ModernAgent(IAgent):
    """现代LangChain智能体"""

    def __init__(self, config: AgentConfig, tool_registry):
        self._config = config
        self.tool_registry = tool_registry
        self._agent_executor = None
        self._loaded_tools = {}

    @property
    def config(self) -> AgentConfig:
        return self._config

    async def initialize(self) -> None:
        """初始化智能体"""
        # 1. 加载配置的工具
        await self._load_tools()

        # 2. 创建Agent执行器
        from langchain.agents import create_agent
        from langchain_openai import ChatOpenAI
        from langchain_anthropic import ChatAnthropic

        # 根据配置选择模型
        if self._config.model.startswith("gpt"):
            llm = ChatOpenAI(model=self._config.model)
        elif self._config.model.startswith("claude"):
            llm = ChatAnthropic(model=self._config.model)
        else:
            raise ValueError(f"Unsupported model: {self._config.model}")

        # 创建Agent
        agent = create_agent(
            llm=llm,
            tools=list(self._loaded_tools.values()),
            system_prompt=self._config.system_prompt
        )

        # 创建执行器
        self._agent_executor = AgentExecutor(
            agent=agent,
            tools=list(self._loaded_tools.values()),
            max_iterations=self._config.max_iterations,
            verbose=self._config.verbose
        )

    async def _load_tools(self) -> None:
        """加载配置的工具"""
        for tool_name in self._config.tools:
            tool = self.tool_registry.get_tool(tool_name)
            if tool:
                # 转换为LangChain工具格式
                langchain_tool = self._convert_to_langchain_tool(tool)
                self._loaded_tools[tool_name] = langchain_tool
            else:
                print(f"Warning: Tool not found: {tool_name}")

    def _convert_to_langchain_tool(self, tool: ITool) -> BaseTool:
        """转换工具为LangChain格式"""
        from langchain_core.tools import StructuredTool
        import inspect

        async def tool_func(**kwargs) -> str:
            result = await tool(**kwargs)
            if result.success:
                return str(result.data)
            else:
                return f"Error: {result.error}"

        # 获取工具函数签名
        sig = inspect.signature(tool.execute)
        parameters = {
            name: {
                "title": name,
                "type": "string"
            }
            for name in sig.parameters.keys()
        }

        return StructuredTool.from_function(
            func=tool_func,
            name=tool.metadata.name,
            description=tool.metadata.description,
            args_schema=type(f"{tool.metadata.name}Args", (), {"__annotations__": parameters})
        )

    async def run(self, query: str) -> str:
        """运行智能体"""
        if not self._agent_executor:
            await self.initialize()

        try:
            result = await self._agent_executor.ainvoke({
                "messages": [HumanMessage(content=query)]
            })
            return result.get("output", "No response generated")
        except Exception as e:
            return f"Agent execution failed: {str(e)}"

    def add_tool(self, tool: ITool) -> None:
        """添加工具"""
        tool_name = tool.metadata.name
        self.tool_registry.register(tool)
        if tool_name not in self._config.tools:
            self._config.tools.append(tool_name)

    def remove_tool(self, tool_name: str) -> None:
        """移除工具"""
        if tool_name in self._config.tools:
            self._config.tools.remove(tool_name)
        if tool_name in self._loaded_tools:
            del self._loaded_tools[tool_name]
        # 重新初始化以应用更改
        self._agent_executor = None

    async def chat(self, message: str, history: Optional[List[BaseMessage]] = None) -> str:
        """对话模式"""
        messages = history or []
        messages.append(HumanMessage(content=message))

        if not self._agent_executor:
            await self.initialize()

        try:
            result = await self._agent_executor.ainvoke({
                "messages": messages
            })
            return result.get("output", "No response generated")
        except Exception as e:
            return f"Chat failed: {str(e)}"
```

### 2. 智能体工厂 (AgentFactory)

**功能描述**: 创建和管理智能体实例

**接口定义**:
```python
from typing import Dict, Type, List, Optional
from core.interfaces import IAgent, ITool
from core.registry import ToolRegistry

class AgentFactory:
    """智能体工厂"""

    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry
        self._agent_types: Dict[str, Type[IAgent]] = {}
        self._agent_templates: Dict[str, AgentConfig] = {}

    def register_agent_type(self, name: str, agent_class: Type[IAgent]) -> None:
        """注册智能体类型"""
        self._agent_types[name] = agent_class

    def register_agent_template(self, name: str, template: AgentConfig) -> None:
        """注册智能体模板"""
        self._agent_templates[name] = template

    def create_agent(self, agent_type: str = "modern", config: Optional[AgentConfig] = None, **kwargs) -> IAgent:
        """创建智能体"""
        if agent_type not in self._agent_types:
            raise ValueError(f"Unknown agent type: {agent_type}")

        agent_class = self._agent_types[agent_type]

        # 使用配置或模板
        if config is None:
            template_name = kwargs.get("template", "default")
            if template_name in self._agent_templates:
                config = self._agent_templates[template_name].copy(**kwargs)
            else:
                config = AgentConfig(**kwargs)

        return agent_class(config=config, tool_registry=self.tool_registry)

    def create_weather_agent(self, model: str = "gpt-3.5-turbo") -> IAgent:
        """创建天气专用智能体"""
        config = AgentConfig(
            name="weather_agent",
            model=model,
            system_prompt="你是一个专业的天气助手，可以帮助用户查询天气信息。你可以使用时间工具来获取当前时间，使用天气工具来查询天气信息。",
            tools=["time_tool", "weather_tool"],
            max_iterations=5
        )
        return self.create_agent("modern", config)

    def create_math_agent(self, model: str = "gpt-3.5-turbo") -> IAgent:
        """创建数学专用智能体"""
        config = AgentConfig(
            name="math_agent",
            model=model,
            system_prompt="你是一个专业的数学助手，可以帮助用户进行各种数学计算。你可以使用数学工具来执行复杂的计算。",
            tools=["math_tool"],
            max_iterations=10
        )
        return self.create_agent("modern", config)

    def create_general_agent(self, model: str = "gpt-3.5-turbo") -> IAgent:
        """创建通用智能体"""
        config = AgentConfig(
            name="general_agent",
            model=model,
            system_prompt="你是一个全能的AI助手，可以帮助用户处理各种问题。你可以使用时间工具、数学工具、天气工具和搜索工具。",
            tools=["time_tool", "math_tool", "weather_tool", "search_tool"],
            max_iterations=15
        )
        return self.create_agent("modern", config)

    def list_agent_types(self) -> List[str]:
        """列出可用的智能体类型"""
        return list(self._agent_types.keys())

    def list_templates(self) -> List[str]:
        """列出可用的智能体模板"""
        return list(self._agent_templates.keys())
```

### 3. 智能体管理器 (AgentManager)

**功能描述**: 管理多个智能体实例的生命周期

**接口定义**:
```python
from typing import Dict, List, Optional
import asyncio
from core.interfaces import IAgent

class AgentManager:
    """智能体管理器"""

    def __init__(self):
        self._agents: Dict[str, IAgent] = {}
        self._agent_configs: Dict[str, AgentConfig] = {}
        self._agent_stats: Dict[str, Dict[str, Any]] = {}

    async def create_agent(self, agent_id: str, config: AgentConfig, tool_registry) -> IAgent:
        """创建并管理智能体"""
        if agent_id in self._agents:
            raise ValueError(f"Agent already exists: {agent_id}")

        from agents.modern_agent import ModernAgent
        agent = ModernAgent(config, tool_registry)
        await agent.initialize()

        self._agents[agent_id] = agent
        self._agent_configs[agent_id] = config
        self._agent_stats[agent_id] = {
            "created_at": asyncio.get_event_loop().time(),
            "request_count": 0,
            "error_count": 0
        }

        return agent

    def get_agent(self, agent_id: str) -> Optional[IAgent]:
        """获取智能体"""
        return self._agents.get(agent_id)

    async def remove_agent(self, agent_id: str) -> bool:
        """移除智能体"""
        if agent_id in self._agents:
            # 清理智能体资源
            agent = self._agents[agent_id]
            if hasattr(agent, 'cleanup'):
                await agent.cleanup()

            del self._agents[agent_id]
            del self._agent_configs[agent_id]
            del self._agent_stats[agent_id]
            return True
        return False

    def list_agents(self) -> List[str]:
        """列出所有智能体ID"""
        return list(self._agents.keys())

    async def run_agent(self, agent_id: str, query: str) -> str:
        """运行指定智能体"""
        if agent_id not in self._agents:
            raise ValueError(f"Agent not found: {agent_id}")

        agent = self._agents[agent_id]
        stats = self._agent_stats[agent_id]

        try:
            stats["request_count"] += 1
            result = await agent.run(query)
            return result
        except Exception as e:
            stats["error_count"] += 1
            raise e

    def get_agent_stats(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取智能体统计信息"""
        if agent_id not in self._agent_stats:
            return None

        stats = self._agent_stats[agent_id].copy()
        config = self._agent_configs[agent_id]

        return {
            "agent_id": agent_id,
            "config": config.dict(),
            "stats": stats,
            "uptime": asyncio.get_event_loop().time() - stats["created_at"]
        }

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有智能体统计信息"""
        return {agent_id: self.get_agent_stats(agent_id) for agent_id in self._agents.keys()}

    async def cleanup_all(self) -> None:
        """清理所有智能体"""
        cleanup_tasks = []
        for agent_id in list(self._agents.keys()):
            cleanup_tasks.append(self.remove_agent(agent_id))

        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
```

### 4. 智能体配置 (AgentConfig)

**功能描述**: 智能体配置管理和验证

**接口定义**:
```python
from pydantic import BaseModel, validator
from typing import List, Dict, Any, Optional

class AgentConfig(BaseModel):
    """智能体配置"""
    name: str
    model: str
    system_prompt: str
    tools: List[str] = []
    max_iterations: int = 10
    verbose: bool = False
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: int = 30

    @validator('model')
    def validate_model(cls, v):
        """验证模型名称"""
        supported_models = [
            "gpt-3.5-turbo", "gpt-4", "gpt-4-turbo",
            "claude-3-sonnet", "claude-3-opus", "claude-3-haiku"
        ]
        if v not in supported_models:
            raise ValueError(f"Unsupported model: {v}")
        return v

    @validator('temperature')
    def validate_temperature(cls, v):
        """验证温度参数"""
        if not 0 <= v <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        return v

    @validator('max_iterations')
    def validate_max_iterations(cls, v):
        """验证最大迭代次数"""
        if v <= 0:
            raise ValueError("Max iterations must be positive")
        return v

    def copy(self, **kwargs) -> 'AgentConfig':
        """复制配置"""
        data = self.dict()
        data.update(kwargs)
        return AgentConfig(**data)

class AgentTemplate(BaseModel):
    """智能体模板"""
    name: str
    description: str
    base_config: AgentConfig
    required_tools: List[str] = []
    optional_tools: List[str] = []

    def create_config(self, **kwargs) -> AgentConfig:
        """从模板创建配置"""
        config = self.base_config.copy(**kwargs)

        # 确保必需工具存在
        for tool in self.required_tools:
            if tool not in config.tools:
                config.tools.append(tool)

        return config
```

## 智能体编排

### 1. 多智能体协调器 (MultiAgentCoordinator)

```python
from typing import List, Dict, Any, Optional
from enum import Enum

class AgentRole(Enum):
    """智能体角色"""
    COORDINATOR = "coordinator"
    SPECIALIST = "specialist"
    REVIEWER = "reviewer"

class MultiAgentCoordinator:
    """多智能体协调器"""

    def __init__(self):
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.task_queue = asyncio.Queue()
        self.result_store = {}

    def add_agent(self, agent_id: str, agent: IAgent, role: AgentRole, capabilities: List[str]) -> None:
        """添加智能体"""
        self.agents[agent_id] = {
            "agent": agent,
            "role": role,
            "capabilities": capabilities,
            "busy": False
        }

    async def coordinate_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """协调任务执行"""
        task_type = task.get("type")
        task_data = task.get("data", {})

        # 1. 选择合适的智能体
        selected_agents = self._select_agents(task_type, task_data)

        if not selected_agents:
            return {"success": False, "error": "No suitable agents found"}

        # 2. 执行任务
        results = {}
        for agent_id in selected_agents:
            agent_info = self.agents[agent_id]
            agent = agent_info["agent"]

            try:
                agent_info["busy"] = True
                result = await agent.run(task_data.get("query", ""))
                results[agent_id] = {"success": True, "result": result}
            except Exception as e:
                results[agent_id] = {"success": False, "error": str(e)}
            finally:
                agent_info["busy"] = False

        # 3. 合并结果
        return self._merge_results(results, task_type)

    def _select_agents(self, task_type: str, task_data: Dict[str, Any]) -> List[str]:
        """选择合适的智能体"""
        suitable_agents = []

        for agent_id, agent_info in self.agents.items():
            if agent_info["busy"]:
                continue

            # 根据任务类型和能力匹配
            capabilities = agent_info["capabilities"]
            if task_type in capabilities:
                suitable_agents.append(agent_id)

        return suitable_agents

    def _merge_results(self, results: Dict[str, Dict[str, Any]], task_type: str) -> Dict[str, Any]:
        """合并多个智能体的结果"""
        successful_results = [r for r in results.values() if r["success"]]

        if not successful_results:
            return {"success": False, "error": "All agents failed"}

        # 简单的结果合并策略
        if len(successful_results) == 1:
            return successful_results[0]

        # 多个成功结果时选择最详细的
        best_result = max(successful_results, key=lambda x: len(x["result"]))
        return {"success": True, "result": best_result["result"], "contributors": list(successful_results.keys())}
```

## 配置管理

### 1. 智能体配置文件

```yaml
# agents_config.yaml
agents:
  weather_agent:
    type: "modern"
    model: "gpt-3.5-turbo"
    system_prompt: "你是一个专业的天气助手，可以查询天气信息并提供天气建议。"
    tools: ["time_tool", "weather_tool"]
    max_iterations: 5
    temperature: 0.7

  math_agent:
    type: "modern"
    model: "gpt-4"
    system_prompt: "你是一个专业的数学助手，可以解决各种数学问题。"
    tools: ["math_tool"]
    max_iterations: 10
    temperature: 0.3

  general_agent:
    type: "modern"
    model: "gpt-4-turbo"
    system_prompt: "你是一个全能的AI助手，可以处理各种问题和任务。"
    tools: ["time_tool", "math_tool", "weather_tool", "search_tool"]
    max_iterations: 15
    temperature: 0.7

templates:
  default:
    model: "gpt-3.5-turbo"
    system_prompt: "你是一个有用的AI助手。"
    tools: []
    max_iterations: 10
    temperature: 0.7

  specialist:
    model: "gpt-4"
    system_prompt: "你是一个专业的领域专家。"
    tools: []
    max_iterations: 15
    temperature: 0.5
```

### 2. 配置加载器

```python
import yaml
import os
from typing import Dict, Any

class AgentConfigLoader:
    """智能体配置加载器"""

    def __init__(self, config_path: str = "agents_config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not os.path.exists(self.config_path):
            return {"agents": {}, "templates": {}}

        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def get_agent_config(self, agent_name: str) -> Optional[AgentConfig]:
        """获取智能体配置"""
        agents_config = self.config.get("agents", {})
        agent_data = agents_config.get(agent_name)

        if agent_data:
            return AgentConfig(**agent_data)
        return None

    def get_template_config(self, template_name: str) -> Optional[AgentConfig]:
        """获取模板配置"""
        templates_config = self.config.get("templates", {})
        template_data = templates_config.get(template_name)

        if template_data:
            return AgentConfig(**template_data)
        return None

    def list_agents(self) -> List[str]:
        """列出所有智能体"""
        return list(self.config.get("agents", {}).keys())

    def list_templates(self) -> List[str]:
        """列出所有模板"""
        return list(self.config.get("templates", {}).keys())
```

## 测试要求

### 1. 单元测试

```python
import pytest
from agents.modern_agent import ModernAgent
from core.registry import ToolRegistry
from tools.time_tool import TimeTool

class TestModernAgent:
    """现代智能体测试"""

    @pytest.fixture
    async def agent(self):
        """测试智能体实例"""
        config = AgentConfig(
            name="test_agent",
            model="gpt-3.5-turbo",
            system_prompt="测试智能体",
            tools=["time_tool"]
        )

        tool_registry = ToolRegistry()
        tool_registry.register_class(TimeTool)

        agent = ModernAgent(config, tool_registry)
        await agent.initialize()
        yield agent

    @pytest.mark.asyncio
    async def test_agent_run(self, agent):
        """测试智能体运行"""
        result = await agent.run("现在几点了？")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_add_tool(self, agent):
        """测试添加工具"""
        from tools.math_tool import MathTool
        math_tool = MathTool()
        agent.add_tool(math_tool)
        assert "math_tool" in agent.config.tools

    def test_remove_tool(self, agent):
        """测试移除工具"""
        agent.remove_tool("time_tool")
        assert "time_tool" not in agent.config.tools
```

### 2. 集成测试

```python
import pytest
from agents.agent_factory import AgentFactory
from core.registry import ToolRegistry

class TestAgentIntegration:
    """智能体集成测试"""

    @pytest.fixture
    def agent_factory(self):
        """智能体工厂实例"""
        tool_registry = ToolRegistry()
        # 注册所有工具
        from tools.time_tool import TimeTool
        from tools.math_tool import MathTool
        from tools.weather_tool import WeatherTool
        from tools.search_tool import SearchTool

        tool_registry.register_class(TimeTool)
        tool_registry.register_class(MathTool)
        tool_registry.register_class(WeatherTool)
        tool_registry.register_class(SearchTool)

        return AgentFactory(tool_registry)

    def test_create_weather_agent(self, agent_factory):
        """测试创建天气智能体"""
        agent = agent_factory.create_weather_agent()
        assert agent.config.name == "weather_agent"
        assert "weather_tool" in agent.config.tools

    def test_create_math_agent(self, agent_factory):
        """测试创建数学智能体"""
        agent = agent_factory.create_math_agent()
        assert agent.config.name == "math_agent"
        assert "math_tool" in agent.config.tools
```

## 部署要求

### 1. API服务

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI(title="Agent Service API")

class ChatRequest(BaseModel):
    agent_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    agent_id: str

# 全局智能体管理器
agent_manager = AgentManager()

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """聊天接口"""
    try:
        response = await agent_manager.run_agent(request.agent_id, request.message)
        return ChatResponse(response=response, agent_id=request.agent_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents")
async def list_agents():
    """列出智能体"""
    return {"agents": agent_manager.list_agents()}

@app.get("/agents/{agent_id}/stats")
async def get_agent_stats(agent_id: str):
    """获取智能体统计"""
    stats = agent_manager.get_agent_stats(agent_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Agent not found")
    return stats
```

### 2. 监控和日志

```python
import logging
from typing import Dict, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("agent_service")

class AgentLogger:
    """智能体日志记录器"""

    @staticmethod
    def log_agent_start(agent_id: str, query: str):
        """记录智能体开始执行"""
        logger.info(f"Agent {agent_id} started processing: {query[:100]}...")

    @staticmethod
    def log_agent_complete(agent_id: str, response: str, duration: float):
        """记录智能体完成执行"""
        logger.info(f"Agent {agent_id} completed in {duration:.2f}s: {response[:100]}...")

    @staticmethod
    def log_agent_error(agent_id: str, error: str):
        """记录智能体执行错误"""
        logger.error(f"Agent {agent_id} failed: {error}")
```