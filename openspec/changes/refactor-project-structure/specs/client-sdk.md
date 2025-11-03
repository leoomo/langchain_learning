# 客户端SDK规范

## 模块概述
客户端SDK提供多语言支持，使其他项目能够方便地集成和使用LangChain Learning项目的功能。支持直接库集成和API服务集成两种模式。

## Python客户端SDK

### 1. 主客户端类

**客户端架构**:
```python
# client/python/client.py
import asyncio
import aiohttp
from typing import Optional, Dict, Any, Union
from urllib.parse import urljoin

class LangChainClient:
    """LangChain客户端主类"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        mode: str = "library",
        timeout: int = 30,
        retries: int = 3
    ):
        """
        初始化客户端

        Args:
            base_url: API服务地址，API模式时必需
            api_key: API密钥，API模式时必需
            mode: 运行模式，"library"或"api"
            timeout: 请求超时时间
            retries: 重试次数
        """
        self.mode = mode
        self.base_url = base_url.rstrip('/') if base_url else None
        self.api_key = api_key
        self.timeout = timeout
        self.retries = retries
        self.session = None

        # 延迟导入避免循环依赖
        self._agent_client = None
        self._tool_client = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        if self.mode == "api":
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers=self._get_headers()
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()

    @property
    def agents(self):
        """智能体客户端"""
        if self._agent_client is None:
            if self.mode == "library":
                from .agents import LibraryAgentClient
                self._agent_client = LibraryAgentClient()
            else:
                from .agents import APIClientAgent
                self._agent_client = APIClientAgent(self)
        return self._agent_client

    @property
    def tools(self):
        """工具客户端"""
        if self._tool_client is None:
            if self.mode == "library":
                from .tools import LibraryToolClient
                self._tool_client = LibraryToolClient()
            else:
                from .tools import APIClientTool
                self._tool_client = APIClientTool(self)
        return self._tool_client

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        if self.mode == "library":
            # 库模式直接检查内部组件
            from agents.agent_manager import AgentManager
            from services.service_manager import ServiceManager

            agent_manager = AgentManager()
            service_manager = ServiceManager()

            agent_health = await agent_manager.health_check_all()
            service_health = await service_manager.health_check_all()

            return {
                "status": "healthy" if all(agent_health.values()) and all(service_health.values()) else "unhealthy",
                "agents": agent_health,
                "services": service_health
            }
        else:
            # API模式调用健康检查接口
            return await self._make_request("GET", "/api/v1/health/detailed")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """发起HTTP请求"""
        if not self.session:
            raise RuntimeError("客户端未初始化，请使用async with语法")

        url = urljoin(self.base_url, endpoint)

        for attempt in range(self.retries):
            try:
                async with self.session.request(
                    method,
                    url,
                    json=data,
                    params=params
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 401:
                        raise Exception("API认证失败，请检查API密钥")
                    elif response.status == 429:
                        raise Exception("请求过于频繁，请稍后再试")
                    else:
                        error_data = await response.json()
                        raise Exception(f"API请求失败: {error_data.get('detail', '未知错误')}")

            except aiohttp.ClientError as e:
                if attempt == self.retries - 1:
                    raise Exception(f"网络请求失败: {str(e)}")
                await asyncio.sleep(2 ** attempt)  # 指数退避
```

### 2. 智能体客户端

**库模式智能体客户端**:
```python
# client/python/agents.py
from typing import Dict, Any, Optional, List
from agents.agent_factory import AgentFactory
from core.registry import ToolRegistry

class LibraryAgentClient:
    """库模式智能体客户端"""

    def __init__(self):
        self.tool_registry = ToolRegistry()
        self.agent_factory = AgentFactory(self.tool_registry)
        self.agent_manager = AgentManager()

    async def create(
        self,
        agent_type: str,
        name: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建智能体"""
        try:
            from agents.modern_agent import AgentConfig

            agent_config = AgentConfig(
                name=name,
                **config
            )

            agent = self.agent_factory.create_agent(
                agent_type,
                agent_config
            )

            await self.agent_manager.create_agent(name, agent_config, self.tool_registry)

            return {
                "id": name,
                "type": agent_type,
                "config": agent_config.dict(),
                "status": "created"
            }

        except Exception as e:
            raise Exception(f"创建智能体失败: {str(e)}")

    async def run(
        self,
        agent_id: str,
        query: str,
        async_execution: bool = False,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """运行智能体"""
        try:
            if async_execution:
                # 异步执行
                import time
                task_id = f"task_{int(time.time())}_{agent_id}"

                # 这里可以集成任务队列系统
                # 暂时直接同步执行
                result = await self.agent_manager.run_agent(agent_id, query)

                return {
                    "task_id": task_id,
                    "status": "completed",
                    "result": result
                }
            else:
                # 同步执行
                result = await self.agent_manager.run_agent(agent_id, query)

                return {
                    "task_id": None,
                    "status": "completed",
                    "result": result
                }

        except Exception as e:
            raise Exception(f"运行智能体失败: {str(e)}")

    async def get_status(self, agent_id: str) -> Dict[str, Any]:
        """获取智能体状态"""
        try:
            stats = self.agent_manager.get_agent_stats(agent_id)
            if not stats:
                raise Exception("智能体未找到")
            return stats
        except Exception as e:
            raise Exception(f"获取智能体状态失败: {str(e)}")

    async def delete(self, agent_id: str) -> Dict[str, Any]:
        """删除智能体"""
        try:
            success = await self.agent_manager.remove_agent(agent_id)
            if not success:
                raise Exception("智能体未找到")
            return {"message": "智能体已删除"}
        except Exception as e:
            raise Exception(f"删除智能体失败: {str(e)}")

    async def list_agents(self) -> List[Dict[str, Any]]:
        """列出所有智能体"""
        try:
            agent_ids = self.agent_manager.list_agents()
            agents = []

            for agent_id in agent_ids:
                stats = self.agent_manager.get_agent_stats(agent_id)
                if stats:
                    agents.append(stats)

            return agents
        except Exception as e:
            raise Exception(f"列出智能体失败: {str(e)}")

class APIClientAgent:
    """API模式智能体客户端"""

    def __init__(self, client):
        self.client = client

    async def create(
        self,
        agent_type: str,
        name: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建智能体"""
        data = {
            "agent_type": agent_type,
            "name": name,
            "config": config
        }
        return await self.client._make_request("POST", "/api/v1/agents/", data)

    async def run(
        self,
        agent_id: str,
        query: str,
        async_execution: bool = False,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """运行智能体"""
        data = {
            "query": query,
            "async_execution": async_execution
        }
        if timeout:
            data["timeout"] = timeout

        return await self.client._make_request(
            "POST",
            f"/api/v1/agents/{agent_id}/run",
            data
        )

    async def get_status(self, agent_id: str) -> Dict[str, Any]:
        """获取智能体状态"""
        return await self.client._make_request("GET", f"/api/v1/agents/{agent_id}/status")

    async def delete(self, agent_id: str) -> Dict[str, Any]:
        """删除智能体"""
        return await self.client._make_request("DELETE", f"/api/v1/agents/{agent_id}")

    async def list_agents(self) -> List[Dict[str, Any]]:
        """列出所有智能体"""
        return await self.client._make_request("GET", "/api/v1/agents/")
```

### 3. 工具客户端

**库模式工具客户端**:
```python
# client/python/tools.py
from typing import Dict, Any, List
from core.registry import ToolRegistry

class LibraryToolClient:
    """库模式工具客户端"""

    def __init__(self):
        self.tool_registry = ToolRegistry()

    async def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有工具"""
        try:
            tools = self.tool_registry.list_tools()
            return [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "version": tool.version,
                    "author": tool.author,
                    "tags": tool.tags,
                    "dependencies": tool.dependencies
                }
                for tool in tools
            ]
        except Exception as e:
            raise Exception(f"列出工具失败: {str(e)}")

    async def run(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """运行工具"""
        try:
            tool = self.tool_registry.get_tool(tool_name)
            if not tool:
                raise Exception(f"工具未找到: {tool_name}")

            result = await tool(**parameters)

            return {
                "tool_name": tool_name,
                "success": result.success,
                "data": result.data,
                "error": result.error,
                "metadata": result.metadata
            }

        except Exception as e:
            raise Exception(f"运行工具失败: {str(e)}")

    async def get_info(self, tool_name: str) -> Dict[str, Any]:
        """获取工具信息"""
        try:
            tool = self.tool_registry.get_tool(tool_name)
            if not tool:
                raise Exception(f"工具未找到: {tool_name}")

            metadata = tool.metadata
            return {
                "name": metadata.name,
                "description": metadata.description,
                "version": metadata.version,
                "author": metadata.author,
                "tags": metadata.tags,
                "dependencies": metadata.dependencies
            }

        except Exception as e:
            raise Exception(f"获取工具信息失败: {str(e)}")

class APIClientTool:
    """API模式工具客户端"""

    def __init__(self, client):
        self.client = client

    async def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有工具"""
        result = await self.client._make_request("GET", "/api/v1/tools/")
        return result["tools"]

    async def run(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """运行工具"""
        return await self.client._make_request(
            "POST",
            f"/api/v1/tools/{tool_name}/run",
            {"parameters": parameters}
        )

    async def get_info(self, tool_name: str) -> Dict[str, Any]:
        """获取工具信息"""
        return await self.client._make_request("GET", f"/api/v1/tools/{tool_name}/info")
```

## JavaScript客户端SDK

### 1. 主客户端类

**客户端架构**:
```javascript
// client/javascript/src/client.js
import axios from 'axios';

class LangChainClient {
    constructor(options = {}) {
        this.mode = options.mode || 'library';
        this.baseURL = options.baseURL;
        this.apiKey = options.apiKey;
        this.timeout = options.timeout || 30000;

        // API模式配置
        if (this.mode === 'api') {
            this.axios = axios.create({
                baseURL: this.baseURL,
                timeout: this.timeout,
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            // 请求拦截器 - 添加认证头
            this.axios.interceptors.request.use(
                config => {
                    if (this.apiKey) {
                        config.headers.Authorization = `Bearer ${this.apiKey}`;
                    }
                    return config;
                },
                error => Promise.reject(error)
            );

            // 响应拦截器 - 处理错误
            this.axios.interceptors.response.use(
                response => response.data,
                error => {
                    if (error.response) {
                        const { status, data } = error.response;
                        throw new Error(`API错误 (${status}): ${data.detail || '未知错误'}`);
                    } else {
                        throw new Error(`网络错误: ${error.message}`);
                    }
                }
            );
        }

        // 延迟初始化子客户端
        this._agents = null;
        this._tools = null;
    }

    get agents() {
        if (!this._agents) {
            if (this.mode === 'library') {
                this._agents = new LibraryAgentClient();
            } else {
                this._agents = new APIClientAgent(this.axios);
            }
        }
        return this._agents;
    }

    get tools() {
        if (!this._tools) {
            if (this.mode === 'library') {
                this._tools = new LibraryToolClient();
            } else {
                this._tools = new APIClientTool(this.axios);
            }
        }
        return this._tools;
    }

    async healthCheck() {
        if (this.mode === 'library') {
            // 库模式 - 调用内部健康检查
            // 这里需要与Python后端通信，实际实现可能需要IPC或HTTP接口
            return { status: 'healthy', mode: 'library' };
        } else {
            // API模式 - 调用健康检查接口
            return await this.axios.get('/api/v1/health/detailed');
        }
    }

    // 静态工厂方法
    static createLibraryClient() {
        return new LangChainClient({ mode: 'library' });
    }

    static createAPIClient(baseURL, apiKey) {
        return new LangChainClient({
            mode: 'api',
            baseURL,
            apiKey
        });
    }
}

export default LangChainClient;
```

### 2. 智能体客户端

```javascript
// client/javascript/src/agents.js
class LibraryAgentClient {
    constructor() {
        // 库模式的实现可能需要与Python后端通信
        // 这里提供接口定义，具体实现取决于集成方式
    }

    async create(agentType, name, config) {
        // 实现库模式的智能体创建
        throw new Error('库模式需要在Python环境中运行');
    }

    async run(agentId, query, options = {}) {
        // 实现库模式的智能体运行
        throw new Error('库模式需要在Python环境中运行');
    }

    async getStatus(agentId) {
        // 实现库模式的状态查询
        throw new Error('库模式需要在Python环境中运行');
    }

    async delete(agentId) {
        // 实现库模式的智能体删除
        throw new Error('库模式需要在Python环境中运行');
    }

    async listAgents() {
        // 实现库模式的智能体列表
        throw new Error('库模式需要在Python环境中运行');
    }
}

class APIClientAgent {
    constructor(axios) {
        this.axios = axios;
    }

    async create(agentType, name, config) {
        return await this.axios.post('/agents/', {
            agent_type: agentType,
            name: name,
            config: config
        });
    }

    async run(agentId, query, options = {}) {
        return await this.axios.post(`/agents/${agentId}/run`, {
            query: query,
            async_execution: options.asyncExecution || false,
            timeout: options.timeout
        });
    }

    async getStatus(agentId) {
        return await this.axios.get(`/agents/${agentId}/status`);
    }

    async delete(agentId) {
        return await this.axios.delete(`/agents/${agentId}`);
    }

    async listAgents() {
        return await this.axios.get('/agents/');
    }
}

export { LibraryAgentClient, APIClientAgent };
```

### 3. 工具客户端

```javascript
// client/javascript/src/tools.js
class LibraryToolClient {
    constructor() {
        // 库模式实现
    }

    async listTools() {
        throw new Error('库模式需要在Python环境中运行');
    }

    async run(toolName, parameters) {
        throw new Error('库模式需要在Python环境中运行');
    }

    async getInfo(toolName) {
        throw new Error('库模式需要在Python环境中运行');
    }
}

class APIClientTool {
    constructor(axios) {
        this.axios = axios;
    }

    async listTools() {
        const response = await this.axios.get('/tools/');
        return response.tools;
    }

    async run(toolName, parameters) {
        return await this.axios.post(`/tools/${toolName}/run`, {
            parameters: parameters
        });
    }

    async getInfo(toolName) {
        return await this.axios.get(`/tools/${toolName}/info`);
    }
}

export { LibraryToolClient, APIClientTool };
```

## 使用示例

### 1. Python使用示例

**库模式示例**:
```python
# examples/python/library_example.py
import asyncio
from langchain_learning import LangChainClient

async def main():
    # 创建库模式客户端
    async with LangChainClient(mode="library") as client:
        # 创建智能体
        agent = await client.agents.create(
            agent_type="general",
            name="my-agent",
            config={
                "model": "gpt-3.5-turbo",
                "system_prompt": "你是一个有用的AI助手"
            }
        )
        print(f"智能体创建成功: {agent['id']}")

        # 运行智能体
        result = await client.agents.run(
            agent_id="my-agent",
            query="现在几点了？北京天气怎么样？"
        )
        print(f"智能体回复: {result['result']}")

        # 使用工具
        tools = await client.tools.list_tools()
        print(f"可用工具: {[tool['name'] for tool in tools]}")

        weather_result = await client.tools.run(
            tool_name="weather_tool",
            parameters={"location": "北京"}
        )
        print(f"天气查询结果: {weather_result['data']}")

if __name__ == "__main__":
    asyncio.run(main())
```

**API模式示例**:
```python
# examples/python/api_example.py
import asyncio
from langchain_learning import LangChainClient

async def main():
    # 创建API模式客户端
    async with LangChainClient(
        base_url="http://localhost:8000",
        api_key="your-api-key",
        mode="api"
    ) as client:
        # 健康检查
        health = await client.health_check()
        print(f"服务状态: {health['status']}")

        # 创建智能体
        agent = await client.agents.create(
            agent_type="weather",
            name="weather-agent",
            config={
                "model": "gpt-3.5-turbo",
                "system_prompt": "你是天气助手"
            }
        )
        print(f"智能体创建成功: {agent['id']}")

        # 运行智能体
        result = await client.agents.run(
            agent_id="weather-agent",
            query="查询上海天气"
        )
        print(f"智能体回复: {result['result']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. JavaScript使用示例

**Node.js示例**:
```javascript
// examples/javascript/node_example.js
const LangChainClient = require('langchain-learning-client');

async function main() {
    try {
        // 创建API模式客户端
        const client = LangChainClient.createAPIClient(
            'http://localhost:8000',
            'your-api-key'
        );

        // 健康检查
        const health = await client.healthCheck();
        console.log('服务状态:', health.status);

        // 创建智能体
        const agent = await client.agents.create(
            'general',
            'my-agent',
            {
                model: 'gpt-3.5-turbo',
                system_prompt: '你是一个有用的AI助手'
            }
        );
        console.log('智能体创建成功:', agent.id);

        // 运行智能体
        const result = await client.agents.run(
            'my-agent',
            '现在几点了？'
        );
        console.log('智能体回复:', result.result);

        // 列出工具
        const tools = await client.tools.listTools();
        console.log('可用工具:', tools.map(t => t.name));

    } catch (error) {
        console.error('错误:', error.message);
    }
}

main();
```

**浏览器示例**:
```html
<!-- examples/javascript/browser_example.html -->
<!DOCTYPE html>
<html>
<head>
    <title>LangChain Client Example</title>
    <script src="https://unpkg.com/axios/dist/axios.min.js"></script>
    <script src="../dist/client.js"></script>
</head>
<body>
    <div id="app">
        <h1>LangChain Client Demo</h1>
        <button onclick="runAgent()">运行智能体</button>
        <div id="result"></div>
    </div>

    <script>
        const client = LangChainClient.createAPIClient(
            'http://localhost:8000',
            'your-api-key'
        );

        async function runAgent() {
            try {
                const result = await client.agents.run(
                    'general-agent',
                    '你好，请介绍一下自己'
                );

                document.getElementById('result').innerHTML =
                    `<p><strong>智能体回复:</strong> ${result.result}</p>`;
            } catch (error) {
                document.getElementById('result').innerHTML =
                    `<p style="color: red;"><strong>错误:</strong> ${error.message}</p>`;
            }
        }
    </script>
</body>
</html>
```

### 3. 配置化集成示例

**配置文件示例**:
```yaml
# config/langchain_config.yaml
langchain_learning:
  mode: "api"
  endpoint: "http://localhost:8000"
  api_key: "your-api-key"
  timeout: 30000
  retries: 3

  default_agent:
    type: "general"
    name: "default-agent"
    config:
      model: "gpt-3.5-turbo"
      system_prompt: "你是一个有用的AI助手"

  tools:
    enabled:
      - "time_tool"
      - "weather_tool"
      - "math_tool"
      - "search_tool"
```

**配置加载客户端**:
```python
# examples/python/config_example.py
import yaml
from langchain_learning import LangChainClient

class ConfigurableLangChainClient:
    """可配置的LangChain客户端"""

    def __init__(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)['langchain_learning']

        self.client = None

    async def __aenter__(self):
        mode = self.config['mode']

        if mode == 'api':
            self.client = LangChainClient(
                base_url=self.config['endpoint'],
                api_key=self.config['api_key'],
                mode=mode,
                timeout=self.config.get('timeout', 30),
                retries=self.config.get('retries', 3)
            )
        else:
            self.client = LangChainClient(mode=mode)

        return await self.client.__aenter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def run_default_agent(self, query: str) -> str:
        """使用默认智能体运行查询"""
        default_config = self.config.get('default_agent')

        if not default_config:
            raise ValueError("未配置默认智能体")

        # 确保默认智能体存在
        try:
            await self.client.agents.get_status(default_config['name'])
        except:
            await self.client.agents.create(**default_config)

        # 运行智能体
        result = await self.client.agents.run(
            agent_id=default_config['name'],
            query=query
        )

        return result['result']

# 使用示例
async def main():
    async with ConfigurableLangChainClient('config/langchain_config.yaml') as client:
        result = await client.run_default_agent("现在几点了？")
        print(f"默认智能体回复: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 包管理和发布

### 1. Python包配置

```toml
# pyproject.toml (客户端包)
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "langchain-learning-client"
version = "1.0.0"
description = "LangChain Learning客户端SDK"
authors = [{name = "Your Name", email = "your.email@example.com"}]
license = {text = "MIT"}
readme = "README.md"
requires-python = ">=3.8"
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]
dependencies = [
    "aiohttp>=3.8.0",
    "pydantic>=1.10.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=22.0.0",
    "flake8>=5.0.0",
    "mypy>=1.0.0",
]

[project.urls]
Homepage = "https://github.com/yourusername/langchain-learning"
Documentation = "https://langchain-learning.readthedocs.io/"
Repository = "https://github.com/yourusername/langchain-learning.git"
Issues = "https://github.com/yourusername/langchain-learning/issues"
```

### 2. JavaScript包配置

```json
// client/javascript/package.json
{
  "name": "langchain-learning-client",
  "version": "1.0.0",
  "description": "LangChain Learning JavaScript客户端SDK",
  "main": "dist/client.js",
  "module": "dist/client.esm.js",
  "types": "dist/types/index.d.ts",
  "scripts": {
    "build": "rollup -c",
    "dev": "rollup -c -w",
    "test": "jest",
    "lint": "eslint src/",
    "type-check": "tsc --noEmit"
  },
  "keywords": [
    "langchain",
    "ai",
    "llm",
    "client",
    "sdk"
  ],
  "author": "Your Name",
  "license": "MIT",
  "dependencies": {
    "axios": "^1.4.0"
  },
  "devDependencies": {
    "@rollup/plugin-commonjs": "^25.0.0",
    "@rollup/plugin-node-resolve": "^15.0.0",
    "@rollup/plugin-typescript": "^11.0.0",
    "@types/jest": "^29.0.0",
    "@types/node": "^20.0.0",
    "eslint": "^8.40.0",
    "jest": "^29.0.0",
    "rollup": "^3.20.0",
    "ts-jest": "^29.0.0",
    "typescript": "^5.0.0"
  },
  "files": [
    "dist/",
    "README.md"
  ],
  "repository": {
    "type": "git",
    "url": "https://github.com/yourusername/langchain-learning.git"
  }
}
```

## 测试要求

### 1. Python客户端测试

```python
# tests/test_client.py
import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from langchain_learning import LangChainClient

@pytest.mark.asyncio
async def test_library_client_creation():
    """测试库模式客户端创建"""
    async with LangChainClient(mode="library") as client:
        assert client.mode == "library"
        assert client.base_url is None

@pytest.mark.asyncio
async def test_api_client_creation():
    """测试API模式客户端创建"""
    async with LangChainClient(
        base_url="http://test.com",
        api_key="test-key",
        mode="api"
    ) as client:
        assert client.mode == "api"
        assert client.base_url == "http://test.com"
        assert client.api_key == "test-key"

@pytest.mark.asyncio
async def test_api_client_request():
    """测试API客户端请求"""
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"status": "ok"})
        mock_request.return_value.__aenter__.return_value = mock_response

        async with LangChainClient(
            base_url="http://test.com",
            api_key="test-key",
            mode="api"
        ) as client:
            result = await client._make_request("GET", "/test")

            assert result["status"] == "ok"
            mock_request.assert_called_once()
```

### 2. JavaScript客户端测试

```javascript
// client/javascript/tests/client.test.js
import axios from 'axios';
import LangChainClient from '../src/client.js';

jest.mock('axios');

describe('LangChainClient', () => {
    let client;

    beforeEach(() => {
        client = new LangChainClient({
            mode: 'api',
            baseURL: 'http://test.com',
            apiKey: 'test-key'
        });
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    test('should create API client correctly', () => {
        expect(client.mode).toBe('api');
        expect(client.baseURL).toBe('http://test.com');
        expect(client.apiKey).toBe('test-key');
    });

    test('should make health check request', async () => {
        const mockResponse = { status: 'healthy' };
        axios.get.mockResolvedValue(mockResponse);

        const result = await client.healthCheck();

        expect(axios.get).toHaveBeenCalledWith('/api/v1/health/detailed');
        expect(result).toEqual(mockResponse);
    });

    test('should handle API errors', async () => {
        const mockError = {
            response: {
                status: 401,
                data: { detail: 'Unauthorized' }
            }
        };
        axios.get.mockRejectedValue(mockError);

        await expect(client.healthCheck()).rejects.toThrow('API错误 (401): Unauthorized');
    });
});
```

## 部署和分发

### 1. Python包发布

```bash
# 构建包
python -m build

# 发布到PyPI
python -m twine upload dist/*

# 或发布到测试PyPI
python -m twine upload --repository testpypi dist/*
```

### 2. JavaScript包发布

```bash
# 构建包
npm run build

# 发布到npm
npm publish

# 或发布到测试环境
npm publish --tag beta
```

## 文档和示例

### 1. API文档生成

```python
# 使用FastAPI自动生成API文档
# 访问 http://localhost:8000/docs 查看Swagger UI
# 访问 http://localhost:8000/redoc 查看ReDoc
```

### 2. 客户端文档

- **README.md**: 基本使用指南
- **examples/**: 详细使用示例
- **docs/**: 完整API文档
- **CHANGELOG.md**: 版本更新记录

这个客户端SDK规范确保了项目可以作为其他项目的后端模块，提供了完整的多语言支持和多种集成方式。