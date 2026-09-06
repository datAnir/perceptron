# Deep Agents - Complete Architecture Reference

## Overview

**Deep Agents** is a "batteries-included agent harness" - a production-ready Python framework built on LangGraph that provides a fully functional AI agent out of the box with sensible defaults, extensible patterns, and enterprise features.

**Current Version:** Latest (active development on main)  
**Framework:** LangGraph-based  
**Key Language:** Python  
**Core Philosophy:** "Don't wire up prompts, tools, and context management yourself - you get a working agent immediately and customize what you need."

---

## Architecture Overview

### High-Level Architecture

```
┌───────────────────────────────────────┐
│  Deep Agents Framework                │
├───────────────────────────────────────┤
│  ┌─ Core Agent Graph ─────────────┐  │
│  │ (LangGraph StateGraph)          │  │
│  │ ├─ State management             │  │
│  │ ├─ Tool orchestration           │  │
│  │ ├─ Planning (write_todos)       │  │
│  │ └─ Streaming                    │  │
│  └─────────────────────────────────┘  │
│                                        │
│  ┌─ Middleware Stack ──────────────┐  │
│  │ ├─ Filesystem (read/write/edit) │  │
│  │ ├─ Shell (execute with sandbox) │  │
│  │ ├─ Sub-agents (task delegation) │  │
│  │ ├─ Memory (summarization)       │  │
│  │ ├─ Skills (knowledge injection) │  │
│  │ ├─ Permissions (access control) │  │
│  │ ├─ MCP Support                  │  │
│  │ └─ Context Management           │  │
│  └─────────────────────────────────┘  │
│                                        │
│  ┌─ Backends ──────────────────────┐  │
│  │ ├─ Local Shell                  │  │
│  │ ├─ Sandbox (e2b, etc.)          │  │
│  │ ├─ Filesystem                   │  │
│  │ ├─ LangSmith Store              │  │
│  │ └─ Custom Backends              │  │
│  └─────────────────────────────────┘  │
│                                        │
│  ┌─ Profiles ──────────────────────┐  │
│  │ ├─ Anthropic defaults           │  │
│  │ ├─ Model-specific configs       │  │
│  │ └─ Custom harness profiles      │  │
│  └─────────────────────────────────┘  │
└───────────────────────────────────────┘
         │
         ▼
    LLM Integration
    (Any LangChain model)
```

### Monorepo Structure

```
deepagents/
├── libs/
│   ├── deepagents/           # Main SDK (Python package)
│   │   ├── graph.py          # Core agent assembly
│   │   ├── _models.py        # Model resolution
│   │   ├── backends/         # Execution backends
│   │   ├── middleware/       # Tool middleware
│   │   ├── profiles/         # Model profiles
│   │   └── __init__.py       # Public API
│   │
│   ├── cli/                  # Terminal UI (deepagents-cli)
│   │   ├── agent.py          # Main CLI agent
│   │   └── ...
│   │
│   ├── evals/                # Evaluation & Harbor integration
│   │
│   ├── acp/                  # Agent Context Protocol support
│   │
│   └── partners/             # Integration packages
│       ├── daytona/          # E2b Daytona sandbox
│       └── ...
│
├── examples/                 # Reference implementations
│   ├── text-to-sql-agent/   # SQL generation example
│   ├── content-builder/      # Content creation example
│   └── ...
│
└── README.md, AGENTS.md     # Documentation
```

---

## Core Concepts

### 1. Agent as Compiled Graph

```python
from deepagents import create_deep_agent

# Returns a compiled LangGraph state graph
agent = create_deep_agent()

# Invoke like any LangGraph compiled graph
result = agent.invoke({
    "messages": [{"role": "user", "content": "Do something"}]
})
```

**Key Advantage:** Full LangGraph compatibility
- Stream events
- Use with Studio
- Add checkpointers
- Compose with other graphs

### 2. Tool Ecosystem

Deep Agents provides **built-in tools** you get automatically:

| Category | Tools |
|----------|-------|
| **Planning** | `write_todos` - Break tasks into subtasks |
| **Filesystem** | `read_file`, `write_file`, `edit_file`, `ls`, `glob`, `grep` |
| **Shell** | `execute` - Run commands (with sandbox support) |
| **Sub-agents** | `task` - Delegate work with isolated context |
| **Context** | Auto-summarization, large output→file |

### 3. Middleware Architecture

Middleware intercepts and modifies:
- **Input** - Messages, instructions, context
- **Tools** - Tool calls, parameters, validation
- **Output** - Results, responses, state updates

```python
agent = create_deep_agent(
    tools=[custom_tool_1, custom_tool_2],
    system_prompt="Custom instructions",
    # Middleware added implicitly:
    # - FilesystemMiddleware
    # - AsyncSubAgentMiddleware
    # - MemoryMiddleware (auto-summarization)
    # - SkillsMiddleware (knowledge injection)
    # - PermissionMiddleware (access control)
    # - MCP Middleware (model context protocol)
)
```

---

## File Structure & Key Modules

### `graph.py` (28KB - Core Agent Assembly)

**Purpose:** Main entry point. Assembles the complete agent graph with all middleware.

**Key Functions:**

#### `create_deep_agent(...)`
The primary factory function.

```python
def create_deep_agent(
    model: BaseChatModel | None = None,           # LLM to use
    tools: list[BaseTool] | None = None,         # Extra tools
    system_prompt: str | None = None,            # Custom system prompt
    working_directory: str | None = None,        # File operations root
    # Backends
    filesystem_backend: BackendProtocol | None = None,
    shell_backend: BackendProtocol | None = None,
    # Middleware customization
    include_memory: bool = True,
    memory_backend: BackendProtocol | None = None,
    summarization_config: dict | None = None,
    skills: list[str] | None = None,            # Skill names/paths
    subagent_backend: BackendProtocol | None = None,
    # Advanced
    extra_middleware: list[AgentMiddleware] | None = None,
    max_iterations: int = 25,
    max_tokens: int = 8000,
) -> CompiledStateGraph:
```

**Returns:** Compiled LangGraph state graph ready to invoke.

**Key Behaviors:**
1. Resolves `model` to default if None (Claude Sonnet)
2. Loads harness profile for model (Anthropic-specific defaults)
3. Stacks middleware in order:
   - Permission middleware
   - Patch tool calls
   - Tool exclusion
   - Filesystem
   - Sub-agents (async)
   - Memory/summarization
   - Skills
   - MCP adapters
4. Creates base system prompt + custom prompt
5. Wraps with interrupt/human-in-loop
6. Compiles to ready-to-invoke graph

#### `get_default_model()`
Returns `ChatAnthropic(model="claude-sonnet-4-6")`

---

### `backends/` - Execution Backends

Backend protocol defines **where tasks execute** (local shell, sandbox, database, etc.)

#### `protocol.py` (Key Interface)

```python
class BackendProtocol(Protocol):
    """All backends implement this protocol"""
    
    async def file_download(self, paths: list[str]) -> list[FileDownloadResponse]:
        """Download file(s)"""
        ...
    
    async def file_upload(self, files: list[FileUploadRequest]) -> list[FileUploadResponse]:
        """Upload file(s)"""
        ...
    
    async def shell_execute(self, commands: list[str]) -> list[ShellExecuteResponse]:
        """Execute shell command(s)"""
        ...
    
    async def store_set(self, keys: list[str], values: list[str]):
        """Store key-value pairs (state persistence)"""
        ...
    
    async def store_get(self, keys: list[str]) -> list[str | None]:
        """Retrieve stored values"""
        ...
```

**Standard Error Codes:**
- `file_not_found` - File doesn't exist
- `permission_denied` - Access denied
- `is_directory` - Tried to download dir as file
- `invalid_path` - Malformed path

#### Built-in Backends:

1. **`LocalShellBackend`** - Execute on local machine
   - Used by default in CLI
   - Full access to filesystem and shell
   
2. **`SandboxBackend`** - Execute in isolated environment
   - Integration with e2b, Docker, etc.
   - Safety boundary between agent and host
   
3. **`CompositeBackend`** - Combine multiple backends
   - Filesystem via one backend, shell via another
   
4. **`StateBackend`** - In-memory state storage
   - Checkpointing between invocations
   - Memory persistence

#### Implementing Custom Backend:

```python
class MyBackend:
    async def file_download(self, paths: list[str]) -> list[FileDownloadResponse]:
        # Custom file retrieval logic
        return [FileDownloadResponse(path=p, content=b"...") for p in paths]
    
    async def shell_execute(self, commands: list[str]) -> list[ShellExecuteResponse]:
        # Custom command execution
        return [ShellExecuteResponse(command=c, stdout="...", exit_code=0) for c in commands]
    
    # ... implement other methods

# Use with agent
agent = create_deep_agent(
    filesystem_backend=MyBackend(),
    shell_backend=MyBackend(),
)
```

---

### `middleware/` - Processing Pipeline

Middleware intercepts tool calls and modifies behavior.

#### 1. **`filesystem.py`** - File Operations Middleware
- Validates paths (security)
- Enforces working directory
- Handles large files (→ temp storage)
- Supports read, write, edit, glob, grep

#### 2. **`subagents.py`** - Sub-agent Middleware
- Provides `task` tool for delegation
- Isolated context window per task
- Parallel execution support
- Async variant available

#### 3. **`memory.py`** - Memory & Summarization Middleware
- Auto-summarizes conversations when token limit approached
- Extracts key info before summarization
- Saves summaries to memory backend
- On resume: reloads context

**How it works:**
```python
# Token thresholds (configurable)
if total_tokens > max_tokens:
    summary = summarize(conversation)
    memory.store("summary", summary)
    context = [summary + recent_messages]
```

#### 4. **`skills.py`** - Skills/Knowledge Injection Middleware
- Loads skill definitions from files or memory
- Injects relevant skills into system prompt
- Skill files are Markdown (human-readable)
- Can be version-controlled and evolved

**Skill Definition:**
```markdown
# Skill: API Design

## Description
Guidelines for RESTful API design

## Content
- Use nouns for resources
- GET, POST, PUT, DELETE for operations
- Return 200, 201, 400, 404, 500 status codes
- Validate input...
```

#### 5. **`permissions.py`** - Access Control Middleware
- Fine-grained tool permission checks
- Supports allow/deny/ask policies
- Context-aware decisions

#### 6. **`async_subagents.py`** - Parallel Task Execution
- Async variant of subagents
- Multiple tasks simultaneously
- Resource pooling

#### 7. **`patch_tool_calls.py`** - Tool Call Validation
- Validates tool invocations against schema
- Fixes common formatting issues
- Provides helpful error messages

---

### `_models.py` - Model Resolution

```python
def resolve_model(spec: str | None) -> BaseChatModel:
    """
    Resolve model string to LangChain model instance.
    
    Examples:
    - "openai:gpt-4o"
    - "anthropic:claude-opus-4-6"
    - "ollama:qwen2.5-coder"
    """
    if spec is None:
        return get_default_model()
    
    provider, model_name = spec.split(":")
    
    if provider == "anthropic":
        return ChatAnthropic(model_name=model_name)
    elif provider == "openai":
        return ChatOpenAI(model=model_name)
    elif provider == "ollama":
        return ChatOllama(model=model_name)
    # ... more providers
```

### `profiles/` - Model-Specific Configurations

Different models have different capabilities. Profiles contain:
- System prompt variants
- Token limits
- Streaming support flags
- Tool availability
- Middleware customization per model

```python
@dataclass
class _HarnessProfile:
    base_system_prompt: str  # Model-specific base prompt
    extra_middleware: list[AgentMiddleware] | Callable[[], list]
    capabilities: ModelCapabilities
    # ...
```

---

## Customization Patterns

### 1. Custom Model

```python
from langchain.chat_models import ChatOpenAI

agent = create_deep_agent(
    model=ChatOpenAI(
        model_name="gpt-4o",
        temperature=0.7
    )
)
```

### 2. Custom Tools

```python
from langchain.tools import tool

@tool
def my_database_query(sql: str) -> str:
    """Execute a SQL query against our database"""
    result = db.execute(sql)
    return json.dumps(result)

agent = create_deep_agent(
    tools=[my_database_query]
)
```

### 3. Custom System Prompt

```python
agent = create_deep_agent(
    system_prompt="""You are a specialized data analyst.
    
    Guidelines:
    - Always verify data before analysis
    - Explain your assumptions
    - Provide confidence scores
    """
)
```

### 4. Custom Skills

```python
agent = create_deep_agent(
    skills=[
        "/path/to/my/skills/database-optimization",
        "/path/to/my/skills/performance-tuning"
    ]
)
```

### 5. Custom Backends

```python
agent = create_deep_agent(
    filesystem_backend=MyCustomFilesystemBackend(),
    shell_backend=SandboxBackend(sandbox_type="docker"),
    memory_backend=PostgresMemoryBackend(connection_string="...")
)
```

### 6. Custom Middleware

```python
class MyMiddleware(AgentMiddleware):
    def process_tool_calls(self, tool_calls):
        # Custom processing
        return modified_tool_calls

agent = create_deep_agent(
    extra_middleware=[MyMiddleware()]
)
```

---

## Usage Examples

### Basic Agentic Loop

```python
from deepagents import create_deep_agent

agent = create_deep_agent()

# Single invocation - agent autonomously plans and executes
result = agent.invoke({
    "messages": [
        {"role": "user", "content": "Research LangGraph and write a summary"}
    ]
})

print(result["messages"][-1].content)
```

### Streaming Responses

```python
agent = create_deep_agent()

# Stream events in real-time
for event in agent.stream(
    {"messages": [{"role": "user", "content": "Build a feature..."}]},
    stream_mode="updates"  # or "values"
):
    print(event)
```

### With Checkpointing

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
agent = create_deep_agent()  # Returns compiled graph
agent_with_memory = agent.with_config(checkpointer=checkpointer)

# Resume from checkpoint
result = agent_with_memory.invoke(
    {"messages": [...]},
    config={"configurable": {"thread_id": "user-123"}}
)
```

### Custom Permissions

```python
def permission_handler(tool_name: str, context: dict) -> bool:
    if tool_name == "bash":
        # Require confirmation for shell commands
        return user_confirms(f"Allow bash: {context['command']}?")
    return True

agent = create_deep_agent(
    # Custom permission logic via middleware
)
```

---

## Deep Agents CLI

A **pre-built coding agent** powered by Deep Agents framework.

### Features

- **Interactive TUI** - Terminal UI with streaming responses
- **Web Search** - Ground responses in live info
- **Headless Mode** - Run non-interactively
- **Persistent Memory** - Remember across sessions
- **Custom Skills** - Load domain knowledge
- **Human-in-Loop** - Approval workflows

### Installation

```bash
curl -LsSf https://raw.githubusercontent.com/langchain-ai/deepagents/main/libs/cli/scripts/install.sh | bash
```

### Basic Usage

```bash
deepagents "Implement a REST API in FastAPI"
```

### Advanced Usage

```bash
deepagents \
  --model openai:gpt-4o \
  --skills /path/to/skills \
  --memory-backend postgres://... \
  --sandboxed \
  "Complex task description"
```

---

## Integration with LangChain Ecosystem

Deep Agents fully integrates with LangChain:

1. **LangSmith Tracing**
   ```python
   import os
   os.environ["LANGSMITH_API_KEY"] = "..."
   
   agent = create_deep_agent()
   # All invocations automatically traced
   ```

2. **LangGraph Studio**
   ```python
   agent = create_deep_agent()
   # Can be visualized and debugged in Studio
   ```

3. **Custom Runnable Composition**
   ```python
   agent = create_deep_agent()
   
   # Compose with other runnables
   chain = input_parser | agent | output_formatter
   ```

4. **MCP Support**
   ```python
   # Via langchain-mcp-adapters
   from langchain_mcp_adapters import MCPTools
   
   agent = create_deep_agent(
       tools=MCPTools.from_server("npx", ["mcp", "run", "github"])
   )
   ```

---

## Key Takeaways for Coding Agent Implementation

1. **Middleware Pipeline** - Modular tool processing architecture
2. **Backend Protocol** - Pluggable execution environments
3. **Memory Management** - Automatic summarization for long conversations
4. **Skills System** - Knowledge injection via Markdown files
5. **Sub-agents** - Task delegation with isolated context
6. **LangGraph Native** - Full compatibility with LangGraph ecosystem
7. **Permission System** - Fine-grained access control
8. **Model Flexibility** - Works with any LangChain model

---

## Integration Recommendations for Your Coding Agent

✅ **From Deep Agents, adopt:**
- Middleware architecture for tool processing
- Backend protocol for pluggable execution
- Skills system (knowledge as Markdown files)
- Memory/summarization for context management
- Sub-agent pattern for task delegation
- Model resolution pattern
- Todo-list tool for planning
- LangGraph as base framework

✅ **Definitely use:**
- LangGraph as core orchestration
- LangChain tools integration
- Middleware for extensibility

❌ **Not necessary:**
- Claude Sonnet hardcoding (support multiple models)
- Specific backends (implement custom ones)
- Anthropic prompt caching (if not using Anthropic)

---

## File Reference

| File | Size | Purpose |
|------|------|---------|
| `graph.py` | 28.9KB | Core agent assembly (`create_deep_agent`) |
| `_models.py` | 4KB | Model resolution and registration |
| `backends/protocol.py` | Major | File/shell execution interface |
| `backends/local_shell.py` | | Local execution backend |
| `backends/sandbox.py` | | Sandboxed execution |
| `middleware/filesystem.py` | | File operations |
| `middleware/subagents.py` | | Sub-agent tool |
| `middleware/memory.py` | | Summarization + memory |
| `middleware/skills.py` | | Knowledge injection |
| `middleware/permissions.py` | | Access control |
| `middleware/async_subagents.py` | | Parallel task execution |

---

## Development Guidelines (From AGENTS.md)

- **Stable Interfaces** - Never break public APIs; use keyword-only args for new params
- **Type Hints** - All code must have type hints
- **Testing** - 100% coverage required for new features
- **Commit Format** - Use Conventional Commits (`feat(sdk): ...`)
- **Code Quality** - Break functions >20 lines, use descriptive names
- **No Eval** - Never use eval/exec on user input
- **Error Handling** - Always use proper exception handling
