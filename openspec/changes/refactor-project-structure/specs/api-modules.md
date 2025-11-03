# API服务层规范

## 模块概述
API服务层提供RESTful API接口，使项目可以作为其他项目的后端模块使用。支持多种部署模式和集成方式，提供完整的客户端SDK。

## API架构设计

### 1. FastAPI服务器架构

**服务器结构**:
```python
# api/fastapi_server.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import uvicorn

class LangChainAPIServer:
    """LangChain API服务器"""

    def __init__(self, config: APIServerConfig):
        self.app = FastAPI(
            title="LangChain Learning API",
            description="智能体和工具API服务",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        self.config = config
        self._setup_middleware()
        self._setup_routes()

    def _setup_middleware(self):
        """设置中间件"""
        # CORS支持
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Gzip压缩
        self.app.add_middleware(GZipMiddleware, minimum_size=1000)

        # 认证中间件
        from api.middleware.auth import AuthMiddleware
        self.app.add_middleware(AuthMiddleware, config=self.config.auth)

        # 限流中间件
        from api.middleware.rate_limit import RateLimitMiddleware
        self.app.add_middleware(RateLimitMiddleware, config=self.config.rate_limit)

    def _setup_routes(self):
        """设置路由"""
        from api.routes.agents import router as agents_router
        from api.routes.tools import router as tools_router
        from api.routes.health import router as health_router

        self.app.include_router(
            agents_router,
            prefix="/api/v1/agents",
            tags=["智能体"]
        )

        self.app.include_router(
            tools_router,
            prefix="/api/v1/tools",
            tags=["工具"]
        )

        self.app.include_router(
            health_router,
            prefix="/api/v1/health",
            tags=["健康检查"]
        )
```

### 2. 智能体API接口

**智能体API规范**:
```python
# api/routes/agents.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from api.schemas.requests import AgentCreateRequest, AgentRunRequest
from api.schemas.responses import AgentResponse, AgentRunResponse

router = APIRouter()

@router.post("/", response_model=AgentResponse)
async def create_agent(request: AgentCreateRequest):
    """创建智能体"""
    try:
        from agents.agent_factory import AgentFactory
        from core.registry import ToolRegistry

        tool_registry = ToolRegistry()
        agent_factory = AgentFactory(tool_registry)

        agent = agent_factory.create_agent(
            agent_type=request.agent_type,
            config=request.config.dict()
        )

        return AgentResponse(
            id=agent.config.name,
            type=request.agent_type,
            config=agent.config.dict(),
            status="created"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{agent_id}/run", response_model=AgentRunResponse)
async def run_agent(
    agent_id: str,
    request: AgentRunRequest,
    background_tasks: BackgroundTasks
):
    """运行智能体"""
    try:
        from agents.agent_manager import AgentManager

        agent_manager = AgentManager()

        # 异步执行任务
        if request.async_execution:
            task_id = f"task_{int(time.time())}_{agent_id}"
            background_tasks.add_task(
                agent_manager.run_agent,
                agent_id,
                request.query
            )

            return AgentRunResponse(
                task_id=task_id,
                status="queued",
                message="任务已加入队列"
            )

        # 同步执行
        result = await agent_manager.run_agent(agent_id, request.query)

        return AgentRunResponse(
            task_id=None,
            status="completed",
            result=result,
            execution_time=0.0
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{agent_id}/status")
async def get_agent_status(agent_id: str):
    """获取智能体状态"""
    try:
        from agents.agent_manager import AgentManager

        agent_manager = AgentManager()
        stats = agent_manager.get_agent_stats(agent_id)

        if not stats:
            raise HTTPException(status_code=404, detail="智能体未找到")

        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    """删除智能体"""
    try:
        from agents.agent_manager import AgentManager

        agent_manager = AgentManager()
        success = await agent_manager.remove_agent(agent_id)

        if not success:
            raise HTTPException(status_code=404, detail="智能体未找到")

        return {"message": "智能体已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 3. 工具API接口

**工具API规范**:
```python
# api/routes/tools.py
from fastapi import APIRouter, HTTPException
from api.schemas.requests import ToolRunRequest
from api.schemas.responses import ToolResponse, ToolListResponse

router = APIRouter()

@router.get("/", response_model=ToolListResponse)
async def list_tools():
    """列出所有可用工具"""
    try:
        from core.registry import ToolRegistry

        tool_registry = ToolRegistry()
        tools = tool_registry.list_tools()

        return ToolListResponse(
            tools=[
                {
                    "name": tool.name,
                    "description": tool.description,
                    "version": tool.version,
                    "tags": tool.tags
                }
                for tool in tools
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{tool_name}/run", response_model=ToolResponse)
async def run_tool(tool_name: str, request: ToolRunRequest):
    """运行工具"""
    try:
        from core.registry import ToolRegistry

        tool_registry = ToolRegistry()
        tool = tool_registry.get_tool(tool_name)

        if not tool:
            raise HTTPException(status_code=404, detail="工具未找到")

        result = await tool(**request.parameters)

        return ToolResponse(
            tool_name=tool_name,
            success=result.success,
            data=result.data,
            error=result.error,
            metadata=result.metadata
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{tool_name}/info")
async def get_tool_info(tool_name: str):
    """获取工具信息"""
    try:
        from core.registry import ToolRegistry

        tool_registry = ToolRegistry()
        tool = tool_registry.get_tool(tool_name)

        if not tool:
            raise HTTPException(status_code=404, detail="工具未找到")

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
        raise HTTPException(status_code=500, detail=str(e))
```

### 4. 健康检查API

**健康检查规范**:
```python
# api/routes/health.py
from fastapi import APIRouter, HTTPException
from api.schemas.responses import HealthResponse, SystemStatusResponse

router = APIRouter()

@router.get("/", response_model=HealthResponse)
async def health_check():
    """基础健康检查"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )

@router.get("/detailed", response_model=SystemStatusResponse)
async def detailed_health_check():
    """详细健康检查"""
    try:
        from agents.agent_manager import AgentManager
        from services.service_manager import ServiceManager

        # 检查智能体
        agent_manager = AgentManager()
        agent_health = await agent_manager.health_check_all()

        # 检查服务
        service_manager = ServiceManager()
        service_health = await service_manager.health_check_all()

        # 系统资源检查
        import psutil
        system_info = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }

        return SystemStatusResponse(
            status="healthy",
            agents=agent_health,
            services=service_health,
            system=system_info,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        return SystemStatusResponse(
            status="unhealthy",
            error=str(e),
            timestamp=datetime.now().isoformat()
        )
```

## 数据模型规范

### 1. 请求数据模型

```python
# api/schemas/requests.py
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from enum import Enum

class AgentType(str, Enum):
    """智能体类型"""
    MODERN = "modern"
    WEATHER = "weather"
    MATH = "math"
    GENERAL = "general"

class AgentConfig(BaseModel):
    """智能体配置"""
    model: str = Field(..., description="模型名称")
    system_prompt: str = Field(default="", description="系统提示")
    tools: List[str] = Field(default=[], description="工具列表")
    max_iterations: int = Field(default=10, description="最大迭代次数")
    temperature: float = Field(default=0.7, description="温度参数")

class AgentCreateRequest(BaseModel):
    """创建智能体请求"""
    agent_type: AgentType = Field(..., description="智能体类型")
    name: str = Field(..., description="智能体名称")
    config: AgentConfig = Field(..., description="智能体配置")

class AgentRunRequest(BaseModel):
    """运行智能体请求"""
    query: str = Field(..., description="查询内容")
    async_execution: bool = Field(default=False, description="是否异步执行")
    timeout: Optional[int] = Field(default=30, description="超时时间（秒）")

class ToolRunRequest(BaseModel):
    """运行工具请求"""
    parameters: Dict[str, Any] = Field(..., description="工具参数")
```

### 2. 响应数据模型

```python
# api/schemas/responses.py
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime

class AgentResponse(BaseModel):
    """智能体响应"""
    id: str = Field(..., description="智能体ID")
    type: str = Field(..., description="智能体类型")
    config: Dict[str, Any] = Field(..., description="智能体配置")
    status: str = Field(..., description="状态")
    created_at: Optional[datetime] = Field(None, description="创建时间")

class AgentRunResponse(BaseModel):
    """智能体运行响应"""
    task_id: Optional[str] = Field(None, description="任务ID")
    status: str = Field(..., description="执行状态")
    result: Optional[str] = Field(None, description="执行结果")
    message: Optional[str] = Field(None, description="状态消息")
    execution_time: Optional[float] = Field(None, description="执行时间")

class ToolResponse(BaseModel):
    """工具响应"""
    tool_name: str = Field(..., description="工具名称")
    success: bool = Field(..., description="执行是否成功")
    data: Optional[Any] = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息")
    metadata: Dict[str, Any] = Field(default={}, description="元数据")

class ToolListResponse(BaseModel):
    """工具列表响应"""
    tools: List[Dict[str, Any]] = Field(..., description="工具列表")
    total: int = Field(..., description="工具总数")

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="健康状态")
    timestamp: str = Field(..., description="检查时间")
    version: str = Field(..., description="API版本")

class SystemStatusResponse(BaseModel):
    """系统状态响应"""
    status: str = Field(..., description="整体状态")
    agents: Dict[str, bool] = Field(default={}, description="智能体状态")
    services: Dict[str, bool] = Field(default={}, description="服务状态")
    system: Dict[str, float] = Field(default={}, description="系统资源")
    error: Optional[str] = Field(None, description="错误信息")
    timestamp: str = Field(..., description="检查时间")
```

## 中间件规范

### 1. 认证中间件

```python
# api/middleware/auth.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import jwt
import time

class AuthMiddleware(BaseHTTPMiddleware):
    """认证中间件"""

    def __init__(self, app, config):
        super().__init__(app)
        self.config = config
        self.exclude_paths = ["/docs", "/redoc", "/health", "/api/v1/health"]

    async def dispatch(self, request: Request, call_next):
        # 跳过不需要认证的路径
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # 获取认证头
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="缺少认证信息")

        # 验证Token
        try:
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, self.config.secret_key, algorithms=["HS256"])

            # 检查Token过期
            if payload.get("exp", 0) < time.time():
                raise HTTPException(status_code=401, detail="Token已过期")

            # 将用户信息添加到请求状态
            request.state.user = payload

        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="无效的Token")

        response = await call_next(request)
        return response
```

### 2. 限流中间件

```python
# api/middleware/rate_limit.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import time
import asyncio
from collections import defaultdict

class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""

    def __init__(self, app, config):
        super().__init__(app)
        self.config = config
        self.requests = defaultdict(list)
        self.cleanup_task = None

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = time.time()

        # 清理过期记录
        if self.cleanup_task is None:
            self.cleanup_task = asyncio.create_task(self._cleanup_expired_requests())

        # 检查请求频率
        self._remove_old_requests(client_ip, current_time)

        if len(self.requests[client_ip]) >= self.config.max_requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail="请求过于频繁，请稍后再试"
            )

        # 记录当前请求
        self.requests[client_ip].append(current_time)

        response = await call_next(request)
        return response

    def _remove_old_requests(self, client_ip: str, current_time: float):
        """移除过期的请求记录"""
        one_minute_ago = current_time - 60
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > one_minute_ago
        ]

    async def _cleanup_expired_requests(self):
        """定期清理过期请求记录"""
        while True:
            await asyncio.sleep(60)  # 每分钟清理一次
            current_time = time.time()

            for client_ip in list(self.requests.keys()):
                self._remove_old_requests(client_ip, current_time)

                # 如果没有请求记录，删除该IP
                if not self.requests[client_ip]:
                    del self.requests[client_ip]
```

## 配置管理

### 1. API服务器配置

```python
# api/config.py
from pydantic import BaseModel
from typing import List, Optional

class AuthConfig(BaseModel):
    """认证配置"""
    enabled: bool = True
    secret_key: str
    algorithm: str = "HS256"
    token_expire_minutes: int = 30

class RateLimitConfig(BaseModel):
    """限流配置"""
    enabled: bool = True
    max_requests_per_minute: int = 60
    burst_size: int = 10

class CORSConfig(BaseModel):
    """CORS配置"""
    enabled: bool = True
    origins: List[str] = ["*"]
    allow_credentials: bool = True
    allow_methods: List[str] = ["*"]
    allow_headers: List[str] = ["*"]

class APIServerConfig(BaseModel):
    """API服务器配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    workers: int = 1
    cors: CORSConfig = CORSConfig()
    auth: AuthConfig
    rate_limit: RateLimitConfig = RateLimitConfig()
```

### 2. 环境配置

```yaml
# config/api_config.yaml
server:
  host: "0.0.0.0"
  port: 8000
  debug: false
  workers: 4

auth:
  enabled: true
  secret_key: "${JWT_SECRET_KEY}"
  token_expire_minutes: 30

rate_limit:
  enabled: true
  max_requests_per_minute: 100
  burst_size: 20

cors:
  enabled: true
  origins:
    - "http://localhost:3000"
    - "https://yourdomain.com"
  allow_credentials: true
```

## 部署配置

### 1. Docker配置

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "api.fastapi_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  langchain-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - JWT_SECRET_KEY=your-secret-key
      - DATABASE_URL=postgresql://user:password@db:5432/langchain
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=langchain
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 2. Kubernetes配置

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: langchain-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: langchain-api
  template:
    metadata:
      labels:
        app: langchain-api
    spec:
      containers:
      - name: langchain-api
        image: langchain-learning:latest
        ports:
        - containerPort: 8000
        env:
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: langchain-secrets
              key: jwt-secret
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: langchain-api-service
spec:
  selector:
    app: langchain-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

## 监控和日志

### 1. 日志配置

```python
# api/logging.py
import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging(config):
    """设置日志配置"""

    # 创建日志格式器
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # 文件处理器
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        'logs/api.log',
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)

    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.log_level.upper()))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
```

### 2. 性能监控

```python
# api/monitoring.py
import time
import psutil
from functools import wraps
from prometheus_client import Counter, Histogram, Gauge

# Prometheus指标
REQUEST_COUNT = Counter('api_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('api_request_duration_seconds', 'Request duration')
ACTIVE_CONNECTIONS = Gauge('api_active_connections', 'Active connections')
SYSTEM_CPU = Gauge('system_cpu_percent', 'CPU usage')
SYSTEM_MEMORY = Gauge('system_memory_percent', 'Memory usage')

def monitor_performance(func):
    """性能监控装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)
            REQUEST_COUNT.labels(method='GET', endpoint=func.__name__, status='200').inc()
            return result
        except Exception as e:
            REQUEST_COUNT.labels(method='GET', endpoint=func.__name__, status='500').inc()
            raise e
        finally:
            REQUEST_DURATION.observe(time.time() - start_time)

    return wrapper

def update_system_metrics():
    """更新系统指标"""
    SYSTEM_CPU.set(psutil.cpu_percent())
    SYSTEM_MEMORY.set(psutil.virtual_memory().percent)
```

## 测试要求

### 1. API测试

```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from api.fastapi_server import LangChainAPIServer

@pytest.fixture
def client():
    """测试客户端"""
    config = APIServerConfig(
        auth=AuthConfig(secret_key="test-secret"),
        rate_limit=RateLimitConfig(enabled=False)
    )
    server = LangChainAPIServer(config)
    return TestClient(server.app)

def test_health_check(client):
    """测试健康检查"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_create_agent(client):
    """测试创建智能体"""
    request_data = {
        "agent_type": "general",
        "name": "test-agent",
        "config": {
            "model": "gpt-3.5-turbo",
            "system_prompt": "测试智能体"
        }
    }

    response = client.post("/api/v1/agents/", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test-agent"
    assert data["type"] == "general"

def test_run_agent(client):
    """测试运行智能体"""
    # 先创建智能体
    create_response = client.post("/api/v1/agents/", json={
        "agent_type": "general",
        "name": "test-agent-2",
        "config": {"model": "gpt-3.5-turbo"}
    })

    # 运行智能体
    run_response = client.post("/api/v1/agents/test-agent-2/run", json={
        "query": "现在几点了？"
    })

    assert run_response.status_code == 200
    data = run_response.json()
    assert data["status"] in ["completed", "queued"]
```

## 部署要求

### 1. 生产环境配置

- **负载均衡**: 支持多实例负载均衡
- **健康检查**: 定期健康检查和自动恢复
- **滚动更新**: 支持零停机滚动更新
- **资源限制**: CPU和内存使用限制
- **安全加固**: HTTPS、防火墙、安全头配置

### 2. 可观测性

- **日志聚合**: 集中化日志收集和分析
- **指标监控**: Prometheus + Grafana监控
- **链路追踪**: 分布式请求追踪
- **告警系统**: 异常和性能告警