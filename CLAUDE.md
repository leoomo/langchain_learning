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

### 🎯 Smart Fishing Recommendation System
**Successfully implemented and functional**:
- ✅ Professional fishing analysis tools with 7-factor enhanced scoring algorithm
- ✅ Enhanced weather tool ecosystem (6 specialized tools)
- ✅ LangChain 1.0+ agent integration with fishing expertise
- ✅ Intent understanding for fishing-related queries
- ✅ Time-slot recommendations based on comprehensive weather conditions
- ✅ Enhanced Fishing Scorer with pressure trend, humidity, seasonal, and lunar analysis
- ✅ Backward-compatible dual-mode scoring (3-factor traditional vs 7-factor enhanced)
- ✅ Scientific weight distribution solving the "86-point problem"

### 🗺️ Enhanced Coordinate System
**High-performance location services**:
- ✅ Multi-tier coordinate lookup: Local DB → Amap API → Fallback logic
- ✅ Intelligent caching system with persistent file storage
- ✅ Comprehensive Chinese region support (3,142+ administrative divisions)
- ✅ Robust error handling with detailed logging
- ✅ BusinessLogger class with DEBUG_LOGGING environment control
- ⚠️ **Known Issue**: Coordinate inconsistency for district names (e.g., "朝阳区" returns Changchun coordinates instead of Beijing)

### 🌤️ Weather Tool System
**Comprehensive weather data ecosystem with hierarchical logging**:
- ✅ Real-time weather API integration with 彩云天气
- ✅ Multi-tier fallback system (API → Local cache → Mock data)
- ✅ Enhanced weather service with date/time queries
- ✅ Professional fishing condition analysis
- ✅ **Hierarchical logging system** with Normal/Debug/Error modes
- ✅ **Performance monitoring** and cache statistics
- ✅ **Template-based configuration** (production/development/debugging/minimal)
- ⚠️ **Coordinate Dependency**: Weather accuracy depends on coordinate service quality

### 📊 Hierarchical Logging System
**Advanced logging configuration with mode-based output control**:
- ✅ **Three logging modes**: Normal (简洁), Debug (详细), Error (异常)
- ✅ **Four preset templates**: Production, Development, Debugging, Minimal
- ✅ **Environment variable control**: `LOG_MODE` and `LOG_TEMPLATE`
- ✅ **Layer-based configuration**: Agent/Tool/Service independent settings
- ✅ **Dynamic mode switching**: Runtime configuration adjustment
- ✅ **Performance metrics**: Execution time, cache hit rates, API response times
- ✅ **Backward compatibility**: Supports existing `DEBUG_LOGGING` configuration
- 📖 **Configuration guide**: See `LOGGING_CONFIGURATION.md` for detailed usage

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
- `demo_enhanced_fishing_scorer.py` - Comprehensive demonstration of the 7-factor enhanced fishing scoring system
- `tools/enhanced_fishing_scorer.py` - Enhanced fishing scorer with 7-factor algorithm (temperature, weather, wind, pressure, humidity, seasonal, lunar)

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
- `tests/test_enhanced_fishing_scorer.py` - Comprehensive test suite for enhanced fishing scorer (16 tests, 100% pass rate)
- `tests/README.md` - Comprehensive testing documentation
- `test_national_coverage.py` - Comprehensive national coverage testing script
- `verify_national_integration.py` - Integration verification for enhanced features

### Logging System (`services/logging/`)
- `services/logging/hierarchical_logger_config.py` - Hierarchical logging configuration manager
- `services/logging/hierarchical_logger.py` - Enhanced logging recorder with mode-based output
- `services/logging/log_templates.py` - Preset template configurations (production/development/debugging/minimal)
- `LOGGING_CONFIGURATION.md` - Comprehensive logging configuration guide

### Development Workflow
- `openspec/` - OpenSpec specification-driven development workflow
- `openspec/changes/` - Change proposals and implementation tracking
- `openspec/AGENTS.md` - OpenSpec workflow guide for AI assistants

### Configuration
- `.env` - Environment variables and API keys (not in git)
- `.env.example` - Environment variable template
- `pyproject.toml` - Project dependencies and configuration
- `uv.lock` - Locked dependency versions

### API Configuration

All API keys are configured in the `.env` file in the project root directory:
- **智谱AI (GLM-4.6)**: `ANTHROPIC_AUTH_TOKEN` ⚠️ Token已过期或验证不正确 (401 Error)
- **彩云天气 API**: `CAIYUN_API_KEY` ✅ Active (Weather queries functional)
- **Anthropic Claude**: `ANTHROPIC_API_KEY` ❌ Invalid API key (401 Error)
- **OpenAI GPT**: `OPENAI_API_KEY` ❌ Request timeout issues

**Current Status**:
- ✅ Weather API (彩云天气) is functional and provides weather data
- ❌ All LLM providers currently have authentication/connectivity issues
- ⚠️ Agent creation succeeds but LLM calls fail due to API key problems

**Note**: All sensitive API credentials are stored in `.env` file and are not committed to version control.

## 🔧 Technical Issues & Solutions

### Weather Tool Coordinate Inconsistency (Identified 2025-11-13)

**Problem Analysis**:
- **Issue**: `朝阳区` query returns Changchun coordinates (125.288168, 43.833845) instead of Beijing (116.4436, 39.9214)
- **Root Cause**: Amap API returns multiple matches for district names; service selects first result without metropolitan prioritization
- **Impact**: Incorrect weather data (5.77°C vs expected 16.26°C for Beijing Chaoyang)

**Function Flow**:
```
User: "朝阳区天气"
→ WeatherTool._current_weather()
→ WeatherTool._get_location_coordinates()
→ [Hardcoded check fails]
→ EnhancedAmapCoordinateService.get_coordinate()
→ Amap API returns 2+ matches
→ Selects first (wrong) match
→ Wrong coordinates → Wrong weather
```

**Affected Files**:
- `tools/weather_tool.py:627-669` - Coordinate lookup logic
- `services/coordinate/enhanced_amap_coordinate_service.py:361-498` - API selection logic

**Proposed Solutions**:
1. **Priority Scoring**: Add population/administrative level weighting for major cities
2. **Context Enhancement**: Include city/province context when querying districts
3. **Match Ranking**: Select most populous match when multiple results exist
4. **Cache Coordination**: Better integration between hardcoded and API coordinates

### 🎯 Smart Fishing Recommendation System
**Successfully implemented and functional**:
- ✅ Professional fishing analysis tools with 7-factor enhanced scoring algorithm
- ✅ Enhanced weather tool ecosystem (6 specialized tools)
- ✅ LangChain 1.0+ agent integration with fishing expertise
- ✅ Intent understanding for fishing-related queries
- ✅ Time-slot recommendations based on comprehensive weather conditions
- ✅ Enhanced Fishing Scorer with pressure trend, humidity, seasonal, and lunar analysis
- ✅ Backward-compatible dual-mode scoring (3-factor traditional vs 7-factor enhanced)
- ✅ Scientific weight distribution solving the "86-point problem"

**Key Features**:
- 🎣 `query_fishing_recommendation(location, date)` - Specialized fishing time analysis
- 📊 Enhanced 7-factor weather condition scoring (0-100) for optimal fishing times
- 🧠 Natural language intent understanding for fishing queries
- 🎯 Professional recommendations based on temperature, weather, wind, pressure, humidity, seasonal, and lunar conditions
- ⚡ Scientific weight distribution: Temperature 26.3%, Weather 21.1%, Wind 15.8%, Pressure 15.8%, Humidity 10.5%, Seasonal 5.3%, Lunar 5.3%
- 🔄 Backward-compatible dual-mode scoring with environment variable control (`ENABLE_ENHANCED_FISHING_SCORING`)

**Usage Example**:
```
User: "余杭区明天钓鱼合适吗？"
→ Agent analyzes intent, extracts location/time
→ Calls fishing recommendation tool
→ Returns: "推荐明天早上6-8点钓鱼，评分85/100，多云天气18°C，微风"
```

## Development Standards
- `.gitignore` - Python gitignore rules
- `.python-version` - Python version specification
- `.venv/` - Virtual environment directory (uv-managed)

This is a mature project setup demonstrating modern LangChain development practices with real-world API integration, comprehensive testing, spec-driven development methodologies, **intelligent fishing recommendation system**, and **production-ready national region coverage system supporting 3,142+ Chinese administrative divisions with 95%+ coverage and 100% coordinate coverage**.

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
