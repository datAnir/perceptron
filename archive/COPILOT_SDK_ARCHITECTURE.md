# GitHub Copilot SDK - Complete Architecture Reference

## Overview

The GitHub Copilot SDK is a **production-tested agent runtime** available in multiple languages (Python, TypeScript, Go, .NET, Java) that exposes Copilot CLI functionality programmatically via **JSON-RPC protocol**.

**Current Version:** 0.1.0  
**Key Feature:** Enables embedding agentic workflows in any application without building custom orchestration.

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────┐
│  Your Application       │
│  (Python/TS/Go/.NET)    │
└────────────┬────────────┘
             │
             ▼
      ┌──────────────┐
      │  SDK Client  │  ◄── CopilotClient (main entry point)
      └──────┬───────┘
             │ JSON-RPC (stdio/TCP)
             ▼
┌─────────────────────────────────┐
│  Copilot CLI Server Mode        │
│  (Bundled or External)          │
│  ├─ Agent Runtime               │
│  ├─ Tool Execution              │
│  ├─ File Management             │
│  └─ Permission System           │
└─────────────────────────────────┘
```

### Core Principle

**SDKs are thin clients** — they manage:
- Process lifecycle (spawn/connect to CLI server)
- JSON-RPC message marshaling
- Session management
- Tool definitions and callbacks

The **Copilot CLI** runs as a server and handles all complex logic:
- Agent planning and execution
- Tool invocation
- File operations
- Permission checks

---

## Python SDK Structure

### Main Modules

#### 1. **`client.py`** (102KB - Core Client)
**Purpose:** Main entry point for SDK users. Manages CLI process lifecycle and session creation.

**Key Classes:**
- `CopilotClient` - Main SDK entry point
  - `create_session(...)` - Creates a new agent session
  - Configuration options: authentication, CLI path, transport type
  
- `SubprocessConfig` - Configure bundled CLI subprocess
  - Auto-spawn CLI in server mode
  - Manage process lifecycle
  
- `ExternalServerConfig` - Connect to external CLI server
  - TCP or Unix socket connections
  - Pre-running CLI instance

**Key Features:**
- Automatic CLI bundling detection
- Process lifecycle management
- Authentication handling (GitHub OAuth, BYOK, env vars)
- Model capability/limits overrides

#### 2. **`session.py`** (73KB - Session Management)
**Purpose:** Manages a single agent session. Handles interactions, hooks, permissions, and streaming.

**Key Classes:**
- `CopilotSession` - Represents one agent session
  - `invoke(messages, tools, ...)` - Send prompt and get response
  - `request_input(...)` - Request user input (blocking)
  - `create_task(...)` - Create sub-tasks
  - Streaming events: `on_chunk`, `on_tool_call`, `on_complete`
  
- `CommandDefinition` - Define custom commands/agents
  - `name` - Unique identifier
  - `description` - What the command does
  - `system_prompt` - Custom behavior
  
- `SessionUiApi` - UI callbacks
  - `on_user_input` - Request user input
  - `on_permission_request` - Ask for permissions
  - `on_message` - Display messages
  - `on_stream_chunk` - Handle streaming output

**Permission System:**
- `ElicitationHandler` - Custom permission logic
  - Returns allow/deny/ask for each tool
  - Access to command context, tool details
  
- Built-in tools controlled via session config:
  - Filesystem ops, bash execution, etc.

#### 3. **`tools.py`** (10.6KB - Tool Definition)
**Purpose:** Decorators and utilities for defining custom tools.

**Key Functions & Classes:**
- `@define_tool(...)` - Decorator for tool functions
  - Auto-generates JSON schema from Pydantic models
  - Supports sync and async handlers
  - Examples:
    ```python
    @define_tool(name="my_tool", description="Does X")
    def my_tool(params: MyParams, invocation: ToolInvocation) -> ToolResult:
        # params automatically validated against Pydantic model
        return ToolResult(text_result_for_llm="Success")
    ```

- `ToolResult` - Return value wrapper
  - `text_result_for_llm` - Response to show LLM
  - `result_type` - "success", "failure", "rejected", "denied", "timeout"
  - `binary_results_for_llm` - For images, files, etc.
  - `error` - Error message if failed
  - `session_log` - Optional debug info

- `ToolInvocation` - Context passed to handler
  - `session_id` - Current session
  - `tool_call_id` - Unique invocation ID
  - `tool_name` - Which tool is being called
  - `arguments` - Parameters (already parsed)

#### 4. **`_jsonrpc.py`** (13.6KB - JSON-RPC Transport)
**Purpose:** Low-level JSON-RPC protocol implementation over stdio/TCP.

**Key Responsibilities:**
- Message serialization/deserialization
- Async request/response handling
- Error handling and timeouts
- Process communication

**Details:**
- Uses async/await for non-blocking I/O
- Handles both bidirectional communication patterns
- Automatic retry logic for transient failures

---

## Session Lifecycle

### 1. Create Client
```python
client = CopilotClient()  # Bundled CLI auto-managed
# OR
client = CopilotClient(
    server=ExternalServerConfig(url="http://localhost:8000")
)
```

### 2. Create Session
```python
session = client.create_session(
    working_directory="/path/to/project",
    tools=[custom_tool_1, custom_tool_2],
    system_prompt="You are...",
    auth=ProviderConfig(...)  # GitHub OAuth, BYOK, etc.
)
```

### 3. Invoke Agent
```python
response = session.invoke(
    messages=[{"role": "user", "content": "Build a feature..."}],
    tools=["read_file", "write_file", "bash"],  # Built-in tool names
    on_permission_request=custom_permission_handler,
    streaming=True  # Enable streaming events
)
```

### 4. Handle Responses
```python
# Streaming approach
async for event in response.stream:
    if event.type == "chunk":
        print(event.text)
    elif event.type == "tool_call":
        tool_name = event.tool_name
        arguments = event.arguments
        # Tool auto-executed by CLI

# Or wait for completion
final_result = await response.wait()
```

### 5. Close Session
```python
session.close()
client.close()  # Stops CLI process
```

---

## Authentication Methods

### 1. GitHub User (Default)
- Reads OAuth credentials from `copilot` CLI login
- Requires prior `copilot auth login` in shell
- Automatically uses stored GitHub token

```python
session = client.create_session()  # Uses ~/.copilot/auth
```

### 2. GitHub OAuth App
- Pass user token from your OAuth flow
```python
session = client.create_session(
    auth=ProviderConfig(
        github_token="ghu_xxxxx"  # From your OAuth app
    )
)
```

### 3. Environment Variables
- `COPILOT_GITHUB_TOKEN` - GitHub token
- `GH_TOKEN` - GitHub CLI token
- `GITHUB_TOKEN` - Standard GitHub token

### 4. BYOK (Bring Your Own Key)
- Use your own LLM provider keys
- No GitHub authentication required

```python
session = client.create_session(
    auth=ProviderConfig(
        provider="openai",
        api_key="sk-...",
        model="gpt-4o"
    )
)
# Also supports: azure, anthropic, ollama
```

---

## Tool System

### Built-in Tools

| Tool | Purpose | Example |
|------|---------|---------|
| `read_file` | Read file contents | `read_file(path="/src/main.py")` |
| `write_file` | Create/overwrite file | `write_file(path="/src/new.py", content="...")` |
| `edit_file` | Edit specific lines | `edit_file(path="/src/main.py", line=10, content="...")` |
| `bash` | Execute shell commands | `bash(command="npm install")` |
| `ls` | List directory contents | `ls(path="/src")` |
| `glob` | Find files by pattern | `glob(pattern="/src/**/*.py")` |
| `grep` | Search file contents | `grep(pattern="TODO", path="/src")` |
| `git` | Git operations | `git(command="status")` |
| `web_search` | Search the web | `web_search(query="latest React patterns")` |

### Custom Tools

Define with `@define_tool` decorator:

```python
from pydantic import BaseModel
from copilot_sdk import define_tool, ToolInvocation, ToolResult

class SearchParams(BaseModel):
    query: str
    limit: int = 10

@define_tool(
    name="custom_search",
    description="Search internal knowledge base",
    params_type=SearchParams
)
def custom_search(params: SearchParams, invocation: ToolInvocation) -> ToolResult:
    results = search_db(params.query, params.limit)
    return ToolResult(
        text_result_for_llm=format_results(results),
        result_type="success"
    )

# Use in session
session = client.create_session(tools=[custom_search])
```

### Tool Permissions

Control which tools are allowed via `ElicitationHandler`:

```python
def permission_handler(context: ElicitationContext) -> ElicitationResult:
    tool_name = context.tool_name
    
    if tool_name == "bash":
        return ElicitationResult(allowed=False)  # Deny bash
    
    if tool_name in ["read_file", "write_file"]:
        return ElicitationResult(allowed=True)  # Always allow read/write
    
    return ElicitationResult(allowed=True)  # Allow others

session = client.create_session(
    on_elicitation=permission_handler
)
```

---

## Streaming & Events

### Stream Types

```python
response = session.invoke(
    messages=[{"role": "user", "content": "..."}],
    streaming=True
)

async for event in response.stream:
    if event.type == "chunk":
        # Text chunk being streamed
        print(event.text)
    
    elif event.type == "tool_call":
        # Agent is calling a tool
        print(f"Calling {event.tool_name}({event.arguments})")
    
    elif event.type == "tool_result":
        # Tool returned a result
        print(f"Result: {event.result}")
    
    elif event.type == "complete":
        # Agent finished
        print("Done")
```

### Event Properties
- `type` - Event category
- `timestamp` - When it occurred
- `session_id` - Which session
- `chunk` - Text content (for chunk events)
- `tool_name` - Tool being invoked (for tool events)
- `arguments` - Parameters (parsed JSON)

---

## Configuration Options

### Client Configuration

```python
client = CopilotClient(
    # CLI Management
    cli_path="/custom/path/to/copilot",  # Use custom CLI binary
    subprocess_config=SubprocessConfig(
        bundled=True,  # Use bundled CLI
        auto_start=True,  # Start if not running
        timeout=30  # Startup timeout (seconds)
    ),
    
    # OR External Server
    server=ExternalServerConfig(
        url="http://localhost:8000",
        transport="http"  # or "tcp"
    ),
    
    # Telemetry
    telemetry_enabled=True,
    user_id="custom-id"  # For tracking usage
)
```

### Session Configuration

```python
session = client.create_session(
    # Working Directory
    working_directory="/path/to/project",
    
    # Tools
    tools=["read_file", "write_file", bash_tool],
    allow_all_tools=False,  # Explicit tool list
    
    # Authentication
    auth=ProviderConfig(
        github_token="...",
        # OR BYOK
        provider="openai",
        api_key="sk-..."
    ),
    
    # Behavior
    system_prompt="You are a senior engineer...",
    model="gpt-4o",  # With BYOK
    
    # UI Callbacks
    ui_api=SessionUiApi(
        on_user_input=input_handler,
        on_permission_request=permission_handler,
        on_message=message_handler
    ),
    
    # Streaming
    streaming=True,
    
    # Persistence
    session_id="persistent-id",  # Resume existing session
    checkpointer=my_checkpointer  # Save state
)
```

---

## Models & Capabilities

### Model Override

```python
session = client.create_session(
    model_overrides=ModelCapabilitiesOverride(
        supports={
            "vision": True,  # Can process images
            "streaming": True,
            "tool_use": True
        },
        limits=ModelLimitsOverride(
            max_tokens=100000,
            max_vision_tokens=5000
        )
    )
)
```

---

## Error Handling

### Common Errors

| Error | Cause | Recovery |
|-------|-------|----------|
| `CLINotFoundError` | CLI binary not found | Install CLI or set `cli_path` |
| `AuthenticationError` | Invalid credentials | Check token, run `copilot auth login` |
| `PermissionDeniedError` | Tool not allowed | Update permission handler |
| `TimeoutError` | Command took too long | Increase timeout or check for hangs |
| `InvalidSessionError` | Session expired/deleted | Create new session |

### Error Handling Pattern

```python
try:
    response = session.invoke(messages=[...])
except PermissionDeniedError as e:
    # Tool execution blocked by permissions
    print(f"Tool denied: {e.tool_name}")
except TimeoutError as e:
    # Command took too long
    print("Command timed out, trying again...")
except Exception as e:
    # Generic error
    print(f"Error: {e}")
finally:
    session.close()
```

---

## Integration Patterns

### 1. REPL/Chat Interface
```python
session = client.create_session()

while True:
    prompt = input("You: ")
    response = session.invoke(
        messages=[{"role": "user", "content": prompt}],
        streaming=True
    )
    
    async for event in response.stream:
        if event.type == "chunk":
            print(event.text, end="", flush=True)
```

### 2. Autonomous Agents
```python
session = client.create_session(
    system_prompt="You are an autonomous code generator."
)

# Single invoke - agent plans and executes autonomously
response = session.invoke(
    messages=[{"role": "user", "content": "Build a FastAPI server"}],
    max_iterations=10  # Limit iterations
)
```

### 3. Custom Sub-agents
```python
def create_code_reviewer_agent():
    return session.create_task(
        name="code_review",
        system_prompt="Review code for quality",
        tools=["read_file", "write_file"]
    )
```

---

## Best Practices

### 1. Resource Management
- Always call `session.close()` and `client.close()`
- Use context managers when available
- Limit concurrent sessions to avoid resource exhaustion

### 2. Tool Design
- Keep tool descriptions clear and concise
- Validate parameters in Pydantic models
- Return detailed error messages in `ToolResult.error`

### 3. Permissions
- Default to deny (explicit allow list)
- Log permission decisions for audit
- Regular review of permission rules

### 4. Performance
- Stream responses for better UX
- Use persistent sessions across multiple invocations
- Batch file operations when possible

### 5. Monitoring
- Track response times per tool
- Log all tool calls and results
- Monitor CLI process health

---

## File Reference

| File | Size | Purpose |
|------|------|---------|
| `client.py` | 102KB | Main SDK entry point, process management |
| `session.py` | 73KB | Session management, message handling |
| `tools.py` | 10.6KB | Tool definition decorators |
| `_jsonrpc.py` | 13.6KB | JSON-RPC protocol implementation |
| `_telemetry.py` | 1.4KB | Telemetry reporting |
| `_sdk_protocol_version.py` | 387B | Protocol version tracking |

---

## Key Takeaways for Coding Agent Implementation

1. **Thin Client Pattern** - SDK is minimal; CLI does heavy lifting
2. **JSON-RPC Protocol** - Language-agnostic communication
3. **Permission System** - Fine-grained tool access control
4. **Streaming Support** - Real-time response handling
5. **Flexible Authentication** - Multiple auth methods (GitHub, BYOK)
6. **Tool Composition** - Built-in tools + custom tools
7. **Session Persistence** - Resume across invocations
8. **Model Flexibility** - Works with multiple LLM providers (with BYOK)

---

## Integration Recommendations for Your Coding Agent

✅ **From Copilot SDK, adopt:**
- JSON-RPC protocol for inter-process communication
- Permission/elicitation handler pattern for tool access
- Tool definition decorator approach
- Streaming event architecture
- Session persistence concept
- Model override/configuration patterns

❌ **Not suitable from Copilot SDK:**
- CLI dependency (build agent runtime from scratch)
- Process spawning complexity (use library-based LLM integration)
- Limited to Anthropic/GitHub models in stock config
