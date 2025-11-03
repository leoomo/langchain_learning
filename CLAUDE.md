# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a LangChain learning project focused on exploring and implementing various LLM chain architectures and patterns using Python with uv package management.

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

The project includes key LangChain ecosystem packages:
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

Currently a minimal setup with:
- `pyproject.toml` - Project configuration and dependencies
- `uv.lock` - Locked dependency versions
- `.gitignore` - Python gitignore rules
- `.python-version` - Python version specification
- `.venv/` - Virtual environment directory

This appears to be a fresh project setup ready for LangChain experimentation and learning.

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
