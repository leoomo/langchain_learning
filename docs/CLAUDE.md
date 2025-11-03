<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive LangChain learning project focused on exploring and implementing modern LLM applications using LangChain 1.0+ with real-time weather API integration and **national region coverage**. The project demonstrates intelligent agent capabilities with tool integration, spec-driven development using OpenSpec, structured testing methodologies, and **comprehensive Chinese administrative division support (3,142+ regions)**.

## Package Management

This project uses **uv** for Python package management as specified in the user's global instructions.

### Common Commands

```bash
# Install dependencies
uv sync

# Run Python scripts
uv run python <script>.py

# Add new dependencies
uv add <package-name>

# Check dependency tree
uv tree

# Activate virtual environment (if needed)
source .venv/bin/activate
```

## Dependencies

The project includes key LangChain ecosystem packages and additional tools:
- `langchain>=1.0.2` - Core LangChain library
- `langchain-anthropic>=1.0.0` - Anthropic integration
- `langchain-community>=0.3.0` - Community integrations
- `langchain-core>=0.3.0` - Core LangChain components
- `langchain-openai>=1.0.1` - OpenAI integration
- `anthropic>=0.20.0` - Anthropic API client
- `openai>=1.0.0` - OpenAI API client
- `transformers>=4.21.0` - Hugging Face transformers
- `torch>=1.12.0` - PyTorch
- `zai-sdk>=0.0.4.1` - Zai SDK
- `python-dotenv>=1.0.0` - Environment variable management
- `requests>=2.31.0` - HTTP client for API calls

## Development Environment

- Python version: >=3.11 (specified in pyproject.toml)
- Virtual environment: `.venv/` (managed by uv)
- Git initialized with basic Python `.gitignore`

## Claude Code Permissions

The `.claude/settings.local.json` file allows:
- Web fetching from LangChain documentation
- Web search capabilities
- Context7 library documentation access
- Filesystem operations
- Specific uv and Python bash commands

## Project Structure

A comprehensive LangChain learning project with organized structure:

### Core Application Files
- `modern_langchain_agent.py` - Main LangChain 1.0+ intelligent agent with national weather coverage
- `enhanced_weather_service.py` - Enhanced weather service with 3,142+ region support and intelligent matching
- `weather_service.py` - Basic Caiyun Weather API service module with fallback mechanisms
- `enhanced_place_matcher.py` - Intelligent place name matching system with 105+ aliases
- `city_coordinate_db.py` - Coordinate database for Chinese administrative divisions
- `weather_cache.py` - Multi-level caching system for weather data
- `zhipu_langchain_example.py` - Basic LangChain integration examples with ZhipuAI

### National Coverage Database
- `data/admin_divisions.db` - SQLite database with 3,142+ Chinese regions (95%+ coverage)
- `national_region_database.py` - Automated national region database initialization
- `coordinate_enrichment.py` - Coordinate information enrichment for all regions
- `补充缺失重要城市.py` - Script to add 90 missing important cities (including 景德镇)
- `批量修复层级关系.py` - Comprehensive hierarchy relationship repair script

### Testing Suite (`tests/`)
- `tests/unit/` - Unit tests for individual components
- `tests/integration/` - Integration tests for multi-component workflows
- `tests/demos/` - Demonstration scripts and examples
- `tests/weather/` - Specialized weather API testing
- `tests/README.md` - Comprehensive testing documentation
- `test_national_coverage.py` - Comprehensive national coverage testing script
- `verify_national_integration.py` - Integration verification for enhanced features

### Development Workflow
- `openspec/` - OpenSpec specification-driven development workflow
- `openspec/changes/` - Change proposals and implementation tracking
- `openspec/AGENTS.md` - OpenSpec workflow guide for AI assistants

### Configuration
- `.env` - Environment variables and API keys (not in git)
- `.env.example` - Environment variable template
- `pyproject.toml` - Project dependencies and configuration
- `uv.lock` - Locked dependency versions

### Development Standards
- `.gitignore` - Python gitignore rules
- `.python-version` - Python version specification
- `.venv/` - Virtual environment directory (uv-managed)

This is a mature project setup demonstrating modern LangChain development practices with real-world API integration, comprehensive testing, spec-driven development methodologies, and **production-ready national region coverage system supporting 3,142+ Chinese administrative divisions with 95%+ coverage and 100% coordinate coverage**.

# LangChain1.0+ overview

<Callout icon="bullhorn" color="#DFC5FE" iconType="regular">
  **LangChain v1.0 is now available!**

  For a complete list of changes and instructions on how to upgrade your code, see the [release notes](/oss/python/releases/langchain-v1) and [migration guide](/oss/python/migrate/langchain-v1).

  If you encounter any issues or have feedback, please [open an issue](https://github.com/langchain-ai/docs/issues/new?template=01-langchain.yml) so we can improve. To view v0.x documentation, [go to the archived content](https://github.com/langchain-ai/langchain/tree/v0.3/docs/docs).
</Callout>

LangChain is the easiest way to start building agents and applications powered by LLMs. With under 10 lines of code, you can connect to OpenAI, Anthropic, Google, and [more](/oss/python/integrations/providers/overview). LangChain provides a pre-built agent architecture and model integrations to help you get started quickly and seamlessly incorporate LLMs into your agents and applications.

We recommend you use LangChain if you want to quickly build agents and autonomous applications. Use [LangGraph](/oss/python/langgraph/overview), our low-level agent orchestration framework and runtime, when you have more advanced needs that require a combination of deterministic and agentic workflows, heavy customization, and carefully controlled latency.

LangChain [agents](/oss/python/langchain/agents) are built on top of LangGraph in order to provide durable execution, streaming, human-in-the-loop, persistence, and more. You do not need to know LangGraph for basic LangChain agent usage.

## <Icon icon="download" size={20} /> Install

<CodeGroup>
  ```bash pip theme={null}
  pip install -U langchain
  ```

  ```bash uv theme={null}
  uv add langchain
  ```
</CodeGroup>

## <Icon icon="wand-magic-sparkles" /> Create an agent

```python  theme={null}
# pip install -qU "langchain[anthropic]" to call the model

from langchain.agents import create_agent

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

# Run the agent
agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]}
)
```

## <Icon icon="star" size={20} /> Core benefits

<Columns cols={2}>
  <Card title="Standard model interface" icon="arrows-rotate" href="/oss/python/langchain/models" arrow cta="Learn more">
    Different providers have unique APIs for interacting with models, including the format of responses. LangChain standardizes how you interact with models so that you can seamlessly swap providers and avoid lock-in.
  </Card>

  <Card title="Easy to use, highly flexible agent" icon="wand-magic-sparkles" href="/oss/python/langchain/agents" arrow cta="Learn more">
    LangChain's agent abstraction is designed to be easy to get started with, letting you build a simple agent in under 10 lines of code. But it also provides enough flexibility to allow you to do all the context engineering your heart desires.
  </Card>

  <Card title="Built on top of LangGraph" icon="circle-nodes" href="/oss/python/langgraph/overview" arrow cta="Learn more">
    LangChain's agents are built on top of LangGraph. This allows us to take advantage of LangGraph's durable execution, human-in-the-loop support, persistence, and more.
  </Card>

  <Card title="Debug with LangSmith" icon="eye" href="/langsmith/home" arrow cta="Learn more">
    Gain deep visibility into complex agent behavior with visualization tools that trace execution paths, capture state transitions, and provide detailed runtime metrics.
  </Card>
</Columns>

***

<Callout icon="pen-to-square" iconType="regular">
  [Edit the source of this page on GitHub.](https://github.com/langchain-ai/docs/edit/main/src/oss/langchain/overview.mdx)
</Callout>

<Tip icon="terminal" iconType="regular">
  [Connect these docs programmatically](/use-these-docs) to Claude, VSCode, and more via MCP for    real-time answers.
</Tip>
